import cv2
from osgeo import gdal
from ultralytics.utils.ops import clip_boxes

from util.labels import arrange_label

gdal.UseExceptions()

from util.labels import *
from utils import *
from natsort import natsorted
from predict import read_original_image_list, build_mask
from config import output_path, original_image_path, modified_label_path, output_combine_label_path, EXPANSION_FACTOR, \
    support_file_list

# 设置随机种子以确保一致性
torch.manual_seed(42)
np.random.seed(42)


def read_image_as_ndarray(image_path, as_rgb=True, gray2rgb=True, channel_combination=(0,1,2), ndarray_dtype=np.float32) -> np.ndarray:
    _, suffix = os.path.splitext(image_path)
    if suffix in ['.tif', '.tiff']:
        with gdal.Open(image_path) as tiff_file:
            image = tiff_file.ReadAsArray().astype(ndarray_dtype)
            if image.ndim == 3:
                image = np.transpose(image, (1, 2, 0))
                if as_rgb and image.shape[-1] != 3:
                    if np.max(channel_combination) >= image.shape[-1]:
                        raise RuntimeError('select band exceed image bands count')
                    new_image = np.zeros((image.shape[0], image.shape[1], 3), dtype=ndarray_dtype)
                    new_image[:, :, 0] = image[:, :, channel_combination[0]]
                    new_image[:, :, 1] = image[:, :, channel_combination[1]]
                    new_image[:, :, 2] = image[:, :, channel_combination[2]]
                    image = new_image
            else:
                if gray2rgb:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        image = cv2.imread(image_path).astype(ndarray_dtype)
    if not image.flags['C_CONTIGUOUS']:
        image = np.ascontiguousarray(image)
    return image

def valid_box_on_2_images(annotation_array_1, annotation_array_2, max_platform_id, iou_min = 0.00001, pixel_size=(10, 10), area_min = 500):
    boxes_1 = annotation_array_1[..., 1:5]
    boxes_2 = annotation_array_2[..., 1:5]

    platform_args = []
    iou_array = np.asarray([[i, j, calculate_iou(box1, box2)]
                          for i, box1 in enumerate(boxes_1)
                          for j, box2 in enumerate(boxes_2)
                          if calculate_iou(box1, box2) > iou_min])

    if len(iou_array) != 0:
        iou_array = delete_non_max_items(iou_array, delete_column=(0, 1), score_column=-1)
        index_all = iou_array[..., 0:2].astype(np.intp)
        annotation_array_1[index_all[..., 0], 0] = 2
        annotation_array_2[index_all[..., 1], 0] = 2
        platform_args = index_all[..., 0]
        for item in index_all:
            i = item[0]
            j = item[1]
            if annotation_array_1[i, -1] == 0:
                max_platform_id += 1
                annotation_array_1[i, -1] = max_platform_id
                annotation_array_2[j, -1] = max_platform_id
            else:
                annotation_array_2[j, -1] = annotation_array_1[i, -1]
    return annotation_array_1, annotation_array_2, platform_args, max_platform_id


def draw_box_on_image(image, boxes: np.ndarray, ids=None, expansion_factor=None, color=(0, 255, 0), thickness=4, draw_id=False):
    if boxes.ndim == 1:
        boxes = np.expand_dims(boxes, axis=1)

    width = boxes[..., 2] - boxes[..., 0]
    height = boxes[..., 3] - boxes[..., 1]

    if expansion_factor == 'auto':
        half_width_expand_size = 6
        half_height_expand_size = 6
    else:
        half_width_expand_size = width * (expansion_factor - 1) / 2
        half_height_expand_size = height * (expansion_factor - 1) / 2

    boxes[..., 0] = (boxes[..., 0] - half_width_expand_size)
    boxes[..., 1] = (boxes[..., 1] - half_height_expand_size)
    boxes[..., 2] = (boxes[..., 2] + half_width_expand_size)
    boxes[..., 3] = (boxes[..., 3] + half_height_expand_size)

    boxes[..., 0][np.where(boxes[..., 0] < 0)] = 0
    boxes[..., 1][np.where(boxes[..., 1] < 0)] = 0
    boxes[..., 2][np.where(boxes[..., 2] > image.shape[1])] = image.shape[1]
    boxes[..., 3][np.where(boxes[..., 3] > image.shape[0])] = image.shape[0]
    boxes = boxes.astype(np.intp)

    for i, box in enumerate(boxes):
        cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]),
                      color=color, thickness=thickness)
        if draw_id and ids is not None:
            font = cv2.FONT_HERSHEY_SIMPLEX  # 定义字体
            org = (box[0], box[1] - 8)
            cv2.putText(image, f'{int(ids[i])}', org, fontFace=font, fontScale=1, color=color, thickness=thickness)
            # 图像，文字内容，坐标(右上角坐标) ，字体，大小，颜色，字体厚度


def draw_box_on_one_image(output_path, annotations_list: np.ndarray, ori_image, ori_image_stem, geo_transform, projection,
                          write_tif=True):
    boxes = annotations_list[..., 1:5]
    labels = annotations_list[..., 0]
    ids = annotations_list[..., 6].astype(np.intp)
    if ori_image.ndim == 2:
        ori_image = cv2.cvtColor(ori_image, cv2.COLOR_GRAY2RGB)

    boxes_label_1 = boxes[labels == 1]
    # boxes_label_2 = boxes[labels == 2]
    # ids_label_1 = ids[labels == 1]
    # ids_label_2 = ids[labels == 2]
    draw_box_on_image(ori_image, boxes_label_1, None, expansion_factor='auto', color=(0, 0, 255), thickness=4)
    # draw_box_on_image(ori_image, boxes_label_2, None, expansion_factor='auto', color=(0, 0, 255), thickness=4)

    # 保存结果图像
    if write_tif:
        driver = gdal.GetDriverByName('GTiff')
        # ########### ?
        ori_image = cv2.cvtColor(ori_image, cv2.COLOR_BGR2RGB)

        band_count = ori_image.shape[-1] if ori_image.ndim == 3 else 1
        # Create a new GeoTIFF file to store the result
        with driver.Create(f'{output_path}/{ori_image_stem}.tif', ori_image.shape[1], ori_image.shape[0], band_count,
                           gdal.GDT_Byte, options=['COMPRESS=LZW']) as out_tiff:
            # Set the geotransform and projection information for the out TIFF based on the input tif
            out_tiff.SetGeoTransform(geo_transform)
            out_tiff.SetProjection(projection)
            # Write the out array to the first band of the new TIFF
            if band_count != 1:
                for i in range(band_count):
                    out_tiff.GetRasterBand(i + 1).WriteArray(ori_image[:, :, i])
            else:
                out_tiff.GetRasterBand(1).WriteArray(ori_image)

            # Write the data to disk
            out_tiff.FlushCache()


if __name__ == "__main__":
    ori_list = read_original_image_list(original_image_path, support_file_list)
    annotations_name_list = [os.path.splitext(annotation_name)[0]
                             for annotation_name in natsorted(os.listdir(output_combine_label_path))
                             if os.path.splitext(annotation_name)[1] == '.txt']
    out_annotations_list = [arrange_label(f'{output_combine_label_path}/{annotations_name}.txt', ori_list[i]['shape'])
                            for i, annotations_name in enumerate(annotations_name_list)]

    platform_count_list = np.zeros(len(ori_list) - 2)
    ship_count_list = np.zeros(len(ori_list) - 2)
    # result_list = []
    max_platform_id = 0

    for i in tqdm(range(len(ori_list) - 1)):
        # logging.info(i)
        ori_image_stem = f'{ori_list[i]['image_original_stem']}'
        ori_image_name = f'{ori_list[i]['image_original_name']}'
        # logging.info(f'ori_image = {ori_image_name}')

        out_annotations_list[i], out_annotations_list[i + 1], platform_args, max_platform_id = (
            valid_box_on_2_images(out_annotations_list[i], out_annotations_list[i + 1], max_platform_id))
        if i == 0:
            continue
        info = out_annotations_list[i].copy()
        info[:, 1:5] = number2yolo(ori_list[i]['shape'], info[:, 1:5])
        # logging.info(f'info = {info}')
        write_txt_label(f'{modified_label_path}/{ori_list[i]['image_original_stem']}.txt', info)

        _, suffix = os.path.splitext(ori_image_name)
        # if suffix in ['.tif', '.tiff']:
        #     with gdal.Open(f'{original_image_path}/{ori_image_name}') as tiff_file:
        #         ori_image = tiff_file.ReadAsArray()
        # else:
        #     ori_image = cv2.imread(f'{original_image_path}/{ori_image_name}')
        ori_image = read_image_as_ndarray(f'{original_image_path}/{ori_image_name}',
                                          as_rgb=True, channel_combination=(0,0,0), ndarray_dtype=np.uint8)
        geo_transform = ori_list[i]['geo_transform']
        projection = ori_list[i]['projection']
        draw_box_on_one_image(output_path, out_annotations_list[i], ori_image, ori_image_stem, geo_transform, projection, write_tif=False)
