import cv2
import onnxruntime
from osgeo import gdal

from modify_type import draw_box_on_one_image
from predict import get_boxes_all_images, read_original_image_list, read_grid_image_list, build_mask

gdal.UseExceptions()

from model import create_model
from config import NUM_CLASSES, DEVICE, NMS_THRESHOLD
from torchvision.ops import nms
from util.labels import *
from utils import *

support_file_list = ['jpg', 'png', 'jp2', 'tif', 'tiff']
# 定义扩大倍数
EXPANSION_FACTOR = 1.5  # 1.0表示不扩大，大于1.0表示扩大

# 设置随机种子以确保一致性
torch.manual_seed(42)
np.random.seed(42)


def inference_one_place(original_image_path, input_path, input_shp_path, model_path, output_path, output_label_path):
    half_gap_size = 32
    # original_image_shape = (4402, 2783)     # (4700, 4700)
    category_list = [1, 2]

    if DEVICE == torch.device('cuda'):
        use_onnxruntime_inference = False
        logging.info('Use Pytorch Inference')
        model = create_model(num_classes=NUM_CLASSES)
        model.load_state_dict(
            # torch.load(f'C:/Sentinel-1_output/model_e108.pth', map_location=DEVICE))  # final#红海108-all  178-2个 140-1个
            torch.load(model_path, map_location=DEVICE, weights_only=True))  # final#红海108-all  178-2个 140-1个
        model.eval()  # 确保模型处于评估模式
        model.to(DEVICE)
    else:
        use_onnxruntime_inference = True
        logging.info('Use ONNXRuntime Inference')
        # model = onnxruntime.InferenceSession("F:/zhongyan/faster_rcnn.onnx")
        model = onnxruntime.InferenceSession(model_path)

    logging.info(f'Loading original images')
    ori_list = read_original_image_list(original_image_path, support_file_list)
    logging.info(f'Loading grid images')
    grid_list = read_grid_image_list(input_path, original_image_path, support_file_list)
    # crearranged_grid_image_list = generate_cluster(grid_list)
    # logging.info(grid_list[0])
    logging.info(f'Begin inference')
    for i, cluster in enumerate(tqdm(grid_list)):
        # logging.info(cluster)
        grid_image_name_list = [image['grid_image_name'] for image in cluster]
        geo_transform = ori_list[i]['geo_transform']
        original_image_shape = ori_list[i]['shape']
        mask = build_mask(original_image_shape, geo_transform, input_shp_path)

        annotations_list = get_boxes_all_images(model, input_path, grid_image_name_list, use_onnxruntime_inference)

        # out_annotations_list = [np.array([]) for _ in range(len(ori_list))]

        for j in range(len(annotations_list)):
            if annotations_list[j].numel() != 0:
                convert_boxes(annotations_list[j][..., 1:5], cluster[j]['x_start'],
                              cluster[j]['y_start'], half_gap_size)

        all_annotation_list = torch.cat(annotations_list)
        valid_annotation_list = remove_invalid_tensor_by_mask(all_annotation_list, mask)
        # new_annotation_list = remove_invalid_annotations(new_annotation_list, (340, 160))
        nms_index = nms(valid_annotation_list[..., 1:5], valid_annotation_list[..., 5], NMS_THRESHOLD)
        out_annotations_list = valid_annotation_list[nms_index].cpu().numpy()

        ori_image_stem = f'{ori_list[i]['image_original_stem']}'
        ori_image_name = f'{ori_list[i]['image_original_name']}'
        _, suffix = os.path.splitext(ori_image_name)
        if suffix in ['.tif', '.tiff']:
            tiff_file = gdal.Open(f'{original_image_path}/{ori_image_name}')
            ori_image = tiff_file.ReadAsArray()
        else:
            ori_image = cv2.imread(f'{original_image_path}/{ori_image_name}')

        geo_transform = ori_list[i]['geo_transform']
        projection = ori_list[i]['projection']
        draw_box_on_one_image(output_path, out_annotations_list, ori_image, ori_image_stem, geo_transform, projection,
                              write_tif=True)

        info = out_annotations_list.copy()
        info[:, 1:5] = number2yolo(ori_list[i]['shape'], info[:, 1:5])
        # logging.info(f'info = {info}')
        write_txt_label(f'{output_label_path}/{ori_list[i]['image_original_stem']}', info)


if __name__ == "__main__":
    # model_path = './run/2025-01-06_14-28-50/best_model.pth'
    model_path = './run/2025-01-06_14-28-50/faster_rcnn_optimize_simplify.onnx'


    # original_image_path = f'./datasets/test_set/weizhou/original_images'
    # input_path = f'./datasets/test_set/weizhou/grid_images'
    # input_shp_path = f'./datasets/test_set/weizhou/weizhou_range/weizhou_oil_field.shp'
    # output_path = f'./datasets/test_set/weizhou/preview'
    # output_label_path = f'./datasets/test_set/weizhou/labels'
    # inference_one_place(original_image_path, input_path, input_shp_path, model_path, output_path, output_label_path)
    #
    # original_image_path = f'./datasets/test_set/malaysia_wenlai/original_images'
    # input_path = f'./datasets/test_set/malaysia_wenlai/grid_images'
    # input_shp_path = f'./datasets/test_set/malaysia_wenlai/malaysia_wenlai_range/malaysia_range_2.shp'
    # output_path = f'./datasets/test_set/malaysia_wenlai/preview'
    # output_label_path = f'./datasets/test_set/malaysia_wenlai/labels'
    # inference_one_place(original_image_path, input_path, input_shp_path, model_path, output_path, output_label_path)

    # original_image_path = f'./datasets/test_set/vietnam/original_images'
    # input_path = f'./datasets/test_set/vietnam/grid_images'
    # input_shp_path = f'./datasets/test_set/vietnam/vietnam_range/vietnam.shp'
    # output_path = f'./datasets/test_set/vietnam/preview'
    # output_label_path = f'./datasets/test_set/vietnam/labels'
    # inference_one_place(original_image_path, input_path, input_shp_path, model_path, output_path, output_label_path)

    # # model_path = f'model_e108.pth'
    model_path = 'faster_rcnn_optimize_simplify.onnx'
    original_image_path = f'./datasets/test_set/malaysia_wenlai/original_images'
    input_path = f'./datasets/test_set_256/malaysia_wenlai/grid_images'
    input_shp_path = f'./datasets/test_set_256/malaysia_wenlai/malaysia_wenlai_range/malaysia_range_2.shp'
    output_path = f'./datasets/test_set_256/malaysia_wenlai/preview'
    output_label_path = f'./datasets/test_set_256/malaysia_wenlai/labels'
    inference_one_place(original_image_path, input_path, input_shp_path, model_path, output_path, output_label_path)

    # original_image_path = f'./datasets/test_set/vietnam/original_images'
    # input_path = f'./datasets/test_set_256/vietnam/grid_images'
    # input_shp_path = f'./datasets/test_set_256/vietnam/vietnam_range/vietnam.shp'
    # output_path = f'./datasets/test_set_256/vietnam/preview'
    # output_label_path = f'./datasets/test_set_256/vietnam/labels'
    # inference_one_place(original_image_path, input_path, input_shp_path, model_path, output_path, output_label_path)


