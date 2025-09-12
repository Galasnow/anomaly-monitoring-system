import cv2
import numpy as np
from osgeo import gdal

from summarize_platform_final import round_day
from util.image_io import read_image_as_ndarray

gdal.UseExceptions()
# from combine_label_new import arange_label

from util.labels import *
from utils import *
# from predict import read_original_image_list, build_mask
from config import output_path, original_image_path, modified_label_path, output_combine_label_path, EXPANSION_FACTOR, \
    support_file_list


def arange_label(label_path, image_shape):
    bbox = read_txt_label(label_path)
    bbox[..., 1:5] = yolo2number(image_shape, bbox[..., 1:5])
    return bbox


def round_day(dt: datetime.timedelta | None = None):
    if dt.seconds >= 12 * 3600:
        return dt.days + 1
    else:
        return dt.days
    
    
def valid_box_on_2_images(annotation_array_1, annotation_array_2, max_platform_id,
                          iou_min = 1e-5):

    if len(annotation_array_1) == 0 or len(annotation_array_2) == 0:
        platform_args = None
        return annotation_array_1, annotation_array_2, platform_args, max_platform_id
    boxes_1 = annotation_array_1[..., 1:5]
    boxes_2 = annotation_array_2[..., 1:5]
    boxes_1_ids = annotation_array_1[..., -1]
    platform_args = []
    iou_array = np.asarray([[i, j, boxes_1_ids[i], calculate_iou(box1, box2)]
                          for i, box1 in enumerate(boxes_1)
                          for j, box2 in enumerate(boxes_2)
                          if calculate_iou(box1, box2) > iou_min])

    # TODO filter small platform first
    if len(iou_array) != 0:
        iou_array = iou_array[np.lexsort((-iou_array[..., -1], iou_array[..., -2]))]
        boxes_1_ids = np.delete(boxes_1_ids, np.where(boxes_1_ids == 0))
        deleted_items = []
        for item in iou_array:
            if check_row_in_2d(item, deleted_items):
                continue
            if item[-2] in boxes_1_ids:
                index_i_1 = np.where(iou_array[..., -2] == item[-2])[0]
                for index in index_i_1:
                    deleted_items.append(iou_array[index])
                iou_array = np.delete(iou_array, index_i_1[1:], axis=0)
                index_i_2 = np.where(iou_array[..., 1] == item[1])[0]
                non_delete_in_2 = np.where(iou_array[..., -2] == item[-2])[0]
                index_i_2 = np.delete(index_i_2, np.where(index_i_2 == non_delete_in_2))
                for index in index_i_2:
                    deleted_items.append(iou_array[index])
                iou_array = np.delete(iou_array, index_i_2, axis=0)

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


def draw_box_on_image(image, boxes: np.ndarray, ids=None, expansion_factor=None, color=(0, 255, 0), thickness=4):
    if boxes.ndim == 1:
        boxes = np.expand_dims(boxes, axis=1)

    width = boxes[..., 2] - boxes[..., 0]
    height = boxes[..., 3] - boxes[..., 1]

    if expansion_factor == 'auto':
        half_width_expand_size = 5
        half_height_expand_size = 5
    elif isinstance(expansion_factor, int):
        half_width_expand_size = expansion_factor
        half_height_expand_size = expansion_factor
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
        if ids is not None:
            font = cv2.FONT_HERSHEY_SIMPLEX  # 定义字体
            org = (box[0], box[1] - 8)
            cv2.putText(image, f'{int(ids[i])}', org, fontFace=font, fontScale=1, color=color, thickness=thickness)
            # 图像，文字内容，坐标(右上角坐标) ，字体，大小，颜色，字体厚度


def draw_box_on_one_image(output_path, annotations_list: np.ndarray, ori_image, ori_image_stem,
                          geo_transform, projection, write_tif=True):
    if len(annotations_list) != 0:
        boxes = annotations_list[..., 1:5]
        labels = annotations_list[..., 0]
        # ids = annotations_list[..., 6].astype(np.intp)
        if ori_image.ndim == 2:
            ori_image = cv2.cvtColor(ori_image, cv2.COLOR_GRAY2RGB)

        # boxes_label_1 = boxes[labels == 1]
        boxes_label_2 = boxes[labels == 2]
        # ids_label_1 = ids[labels == 1]
        # ids_label_2 = ids[labels == 2]
        ids_label_2 = None
        # draw_box_on_image(ori_image, boxes_label_1, None, expansion_factor=4, color=(0, 255, 0), thickness=4)
        draw_box_on_image(ori_image, boxes_label_2, ids_label_2, expansion_factor=4, color=(0, 0, 255), thickness=4)

    # 保存结果图像
    if write_tif:
        driver = gdal.GetDriverByName('GTiff')

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
                    select_band = out_tiff.GetRasterBand(i + 1)
                    select_band.WriteArray(ori_image[:, :, i])
            else:
                select_band = out_tiff.GetRasterBand(1)
                select_band.WriteArray(ori_image)

            # Write the data to disk
            out_tiff.FlushCache()

def calculate_size_score(size):
    # 300: 1
    if size >= 0:
        if size <= 60:
            score = size / 60
        else:
            score = 1.0
    else:
        raise RuntimeError('size must >= 0')
    return score


def calculate_time_score(days: int):
    # 0: 0.02, 50: 1
    if days >= 0:
        if days <= 9:
            score = days / 9.0
        else:
            score = 1.0
    else:
        raise RuntimeError('stay days must >= 0')
    return score


def calculate_iou_score(iou_list: Sequence | np.ndarray):
    if any(iou_list) < 0:
        raise RuntimeError('IOU must >= 0')
    exponent = 1 / 2.0
    score = np.mean(np.pow(iou_list, exponent))
    return score


if __name__ == "__main__":
    initial_logging_formatter()
    ori_list = build_sorted_sentinel_1_list(original_image_path)
    original_name_list = [file.filename for file in ori_list]
    # annotations_name_list = [os.path.splitext(annotation_name)[0]
    #                          for annotation_name in natsorted(os.listdir(output_combine_label_path))
    #                          if os.path.splitext(annotation_name)[1] == '.txt']

    annotations_name_list = [file.filename.replace('tif', 'txt') for file in ori_list]

    out_annotations_list = [arange_label(f'{output_combine_label_path}/{annotations_name}',
                                          ori_list[i].shape)
                            for i, annotations_name in enumerate(annotations_name_list)]
    acquire_time_list = [item.acquire_time for item in ori_list]
    platform_count_list = np.zeros(len(ori_list) - 2)
    ship_count_list = np.zeros(len(ori_list) - 2)
    max_platform_id = 0

    for i in tqdm(range(len(ori_list) - 1)):
        out_annotations_list[i], out_annotations_list[i + 1], _, max_platform_id = (
            valid_box_on_2_images(out_annotations_list[i], out_annotations_list[i + 1], max_platform_id))

    remove_ids = []
    # filter IOU and time
    for i in tqdm(range(1, max_platform_id + 1)):
        annotations_i = []
        acquire_time_i = []
        for acquire_time, annotations in zip(acquire_time_list, out_annotations_list):
            for annotation in annotations:
                if annotation[-1] == i:
                    annotations_i.append(annotation)
                    acquire_time_i.append(acquire_time)
                    break
            # annotations_i = [annotation for annotations in out_annotations_list for annotation in annotations if annotation[-1] == i]
        # if i == 123:
        #     logging.info(f'{annotations_i = }')
        #     logging.info(f'{acquire_time_i = }')

        platform_ious = np.zeros(len(annotations_i) - 1, dtype=np.float32)
        platform_i_bboxes_array = np.asarray(
            [item[..., 1:5] for item in annotations_i]).squeeze()

        if platform_i_bboxes_array.ndim < 2:
            platform_i_bboxes_array = np.concatenate(
                (np.reshape(platform_i_bboxes_array, (1, 4)), np.reshape(platform_i_bboxes_array, (1, 4))), axis=0)
        platform_ious = [calculate_iou(platform_i_bboxes_array[i], platform_i_bboxes_array[i + 1]) for i in
                            range(len(platform_i_bboxes_array) - 1)]
        platform_size = np.mean([(item[2] - item[0]) * (item[3] - item[1]) for item in platform_i_bboxes_array])
        # logging.info(f'{platform_size = }')
        # if i == 123:
        #     logging.info(f'{platform_ious = }')

        iou_score = calculate_iou_score(platform_ious)
        time_score = calculate_time_score(round_day(acquire_time_i[-1] - acquire_time_i[0]))
        p1 = iou_score * time_score
        if round_day(acquire_time_i[-1] - acquire_time_i[0]) < 30 or p1 < 0.2 or calculate_size_score(platform_size) < 0.2:
            remove_ids.append(i)

    logging.info(f'{remove_ids = }')
    logging.info(f'{len(remove_ids) = }')
    if len(remove_ids) > 0:
        remove_index = np.asarray(remove_ids) - 1
        print(f'{max_platform_id = }')
        map_list = np.zeros((max_platform_id - len(remove_ids), 2), dtype=np.intp)
        print(f'{len(map_list) = }')
        map_list[..., 0] = np.reshape(np.delete(range(1, max_platform_id + 1), remove_index), -1)
        modified_map_list = map_list.copy()
        for i, item in enumerate(map_list):
            j = item[0]
            index = np.searchsorted(remove_ids, j)
            modified_map_list[i, 1] = index

        print(f'{modified_map_list = }')
        # filter IOU and time
        for i in tqdm(range(1, len(ori_list) - 1)):
            pass

        # filter size
        for i in tqdm(range(1, len(ori_list) - 1)):
            pass
        print(f'{out_annotations_list[1] = }')
        modified_out_annotations_list = out_annotations_list.copy()
        # refresh ids
        for i in tqdm(range(len(ori_list))):
            for j in range(len(out_annotations_list[i])):
                item = out_annotations_list[i][j]

                if item[0] == 2:
                    id = int(item[-1])
                    if id in remove_ids:
                        modified_out_annotations_list[i][j][0] = 1
                        modified_out_annotations_list[i][j][-1] = 0
                    else:
                        index = np.searchsorted(modified_map_list[..., 0], id)
                        modified_out_annotations_list[i][j][-1] -= modified_map_list[index, 1]

    else:
        modified_out_annotations_list = out_annotations_list
    print(f'{modified_out_annotations_list[1] = }')
    pbar = tqdm(range(1, len(ori_list) - 1))
    pbar.set_description(f'writing images')
    for i in pbar:
        ori_image_stem = os.path.splitext(ori_list[i].filename)[0]
        ori_image_name = ori_list[i].filename
        info = modified_out_annotations_list[i].copy()
        info[..., 1:5] = number2yolo(ori_list[i].shape, info[..., 1:5])
        # logging.info(f'{info = }')
        write_txt_label(f'{modified_label_path}/{ori_image_stem}.txt', info)

        ori_image = read_image_as_ndarray(f'{original_image_path}/{ori_image_name}',
                                          as_rgb=True, channel_combination=(0,0,0), ndarray_dtype=np.uint8)
        # logging.info(f'{ori_image.shape = }')
        geo_transform = ori_list[i].geo_transform
        projection = ori_list[i].projection
        draw_box_on_one_image(output_path, modified_out_annotations_list[i], ori_image, ori_image_stem,
                              geo_transform, projection, write_tif=True)