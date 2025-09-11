import logging
import os

import numpy as np
import cv2
import torch
from osgeo import gdal
from torchvision.ops import nms
from tqdm import tqdm

from util.labels import number2yolo, yolo2number, remove_invalid_tensor_by_mask, \
    write_txt_label, move_boxes

from config import original_image_path, input_path, output_grid_label_path, input_shp_path, NMS_THRESHOLD, \
    output_combine_label_path, support_file_list
from predict import read_original_image_list, read_grid_image_list, generate_cluster, build_mask
from util.labels import read_txt_label
from utils import initial_logging_formatter


def arrange_label(label_path, image_shape):
    bbox = read_txt_label(label_path)
    bbox[..., 1:5] = yolo2number(image_shape, bbox[..., 1:5])
    # logging.info(bbox)
    return bbox


if __name__ == "__main__":
    initial_logging_formatter()
    ori_list = read_original_image_list(original_image_path, support_file_list)

    # grid_image_name_list = [image_name for image_name in natsorted(os.listdir(input_image_path))
    #                    if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    grid_list, _ = read_grid_image_list(input_path, original_image_path, support_file_list)
    grid_list_cluster, unique_image_original_stem_list = generate_cluster(grid_list)
    label_name_list = [label_name for label_name in os.listdir(output_grid_label_path)]
    # label_name_list, grid_label_list = read_grid_label_list(input_label_path, input_image_path, grid_image_name_list, None)
    # logging.info(image_name_list)
    # length = len(label_name_list)
    # logging.info(length)
    # batch_size = int(len(label_name_list) / len(ori_list))
    # logging.info(batch_size)
    # annotations_list = [arrange_label(f'{output_grid_label_path}/{label_name_list[i]}', grid_list[i]['shape']) for i in range(len(label_name_list))]
    # logging.info(annotations_list)
    out_annotations_list = [np.array([]) for _ in range(len(ori_list))]

    for i, cluster in enumerate(tqdm(grid_list_cluster)):
        # grid_image_name_list = [image['grid_image_name'] for image in cluster]
        # grid_image_stem_list = [image['grid_image_stem'] for image in cluster]
        annotations_list = [arrange_label(f'{output_grid_label_path}/{cluster[j]['grid_image_stem']}.txt',
                                          cluster[j]['shape']) for j in range(len(cluster))]
        # logging.info(annotations_list)
        # logging.info(len(annotations_list))
        # mask = build_mask(original_image_shape)
        geo_transform = ori_list[i]['geo_transform']
        original_image_shape = ori_list[i]['shape']
        logging.info(f'{original_image_shape = }')
        mask = build_mask([original_image_shape[1], original_image_shape[0]], geo_transform, input_shp_path)
        # batch_size = int(len(grid_list) / len(ori_list))

        # out_annotations_list = [np.array([]) for _ in range(len(ori_list))]

        for j in range(len(annotations_list)):
            # logging.info(cluster[j]['x_start'], cluster[j]['y_start'])
            if annotations_list[j].size != 0:
                move_boxes(annotations_list[j][..., 1:5], cluster[j]['x_start'],
                                cluster[j]['y_start'])
        annotations_list = [x for x in annotations_list if x.size != 0]
        if len(annotations_list) == 0:
            write_txt_label(f'{output_combine_label_path}/{ori_list[i]['image_original_stem']}.txt',
                            [])
            continue
        all_annotations_list = torch.as_tensor(np.concatenate(annotations_list, axis=0))
        # logging.info(all_annotations_list)
        valid_annotations_list = remove_invalid_tensor_by_mask(all_annotations_list, mask)
        # valid_annotations_list = all_annotations_list
        # new_annotation_list = remove_invalid_annotations(new_annotation_list, (340, 160))
        # logging.info(valid_annotation_list)
        nms_index = nms(valid_annotations_list[..., 1:5], valid_annotations_list[..., 5], NMS_THRESHOLD)
        out_annotations_list = valid_annotations_list[nms_index].cpu().numpy()
        ids = np.zeros((len(out_annotations_list), 1))
        out_annotations_list = np.concatenate((out_annotations_list, ids), axis=1)

        ori_image_stem = f'{ori_list[i]['image_original_stem']}'
        ori_image_name = f'{ori_list[i]['image_original_name']}'
        _, suffix = os.path.splitext(ori_image_name)
        if suffix in ['.tif', '.tiff']:
            tiff_file = gdal.Open(f'{original_image_path}/{ori_image_name}')
            ori_image = tiff_file.ReadAsArray().astype(np.float32)
        else:
            ori_image = cv2.imread(f'{original_image_path}/{ori_image_name}').astype(np.float32)

        # geo_transform = ori_list[i]['geo_transform']
        projection = ori_list[i]['projection']
        # draw_box_on_one_image(output_preview_path, out_annotations_list, ori_image, ori_image_stem, geo_transform, projection,
        #                        write_tif=False)

        # info = out_annotations_list
        out_annotations_list[:, 1:5] = number2yolo(ori_list[i]['shape'], out_annotations_list[:, 1:5])
        # logging.info(f'info = {info}')
        write_txt_label(f'{output_combine_label_path}/{ori_list[i]['image_original_stem']}.txt', out_annotations_list)
