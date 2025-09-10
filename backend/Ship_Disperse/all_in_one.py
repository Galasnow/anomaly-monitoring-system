import csv
import datetime
import logging
import os
import re
from typing import List

import cv2
import numpy as np
import torch
from imagesize import imagesize
from matplotlib import pyplot as plt
from natsort import natsorted
from osgeo import gdal, ogr, osr
from torchvision.ops import nms
from tqdm import tqdm

from config import DEVICE, NUM_CLASSES, support_file_list, NMS_THRESHOLD
from model import create_model
from modify_type import read_image_as_ndarray, valid_box_on_2_images, draw_box_on_one_image
from predict import read_grid_image_list, get_boxes_per_image, read_original_image_list, generate_cluster, build_mask
from auto_crop import batch_crop_image_by_grid
from summarize_platform import write_csv
from util.labels import number2yolo, write_txt_label, arrange_label, convert_boxes, remove_invalid_tensor_by_mask, \
    read_txt_label, yolo2number, image_coordinates_2_latitude_longitude
from utils import create_folder, initial_logging_formatter, get_platform_ship_coordinates_by_id, \
    get_platform_ship_coordinates_by_day, get_platform_coordinates, get_platform_sizes, calculate_iou, write_shp_file, \
    build_sorted_sentinel_1_list

stem_path = '../public/Ship_Disperse'

if __name__ == "__main__":
    current_file_path = os.path.abspath(__file__)
    current_path = os.path.dirname(current_file_path)

    # stem_path = os.path.join(current_path, f'/public/Ship_Disperse')

    output_stem_path = f'{stem_path}/output'
    # input_path = f'{stem_path}/grid_images'
    ground_truth_path = f'{stem_path}/labels_t'
    output_path = f'{output_stem_path}/predict'
    output_preview_path = f'{output_stem_path}/preview'
    output_combine_label_path = f'{output_stem_path}/labels/combine'
    original_image_path = f'{stem_path}/original_images'
    modified_label_path = f'{output_stem_path}/labels/modified'

    output_shp_path = f'{output_stem_path}/shapefile'

    output_shp_path_by_day = f'{output_stem_path}/by_day'

    create_folder(output_path)
    create_folder(output_combine_label_path)
    create_folder(modified_label_path)
    create_folder(output_shp_path)
    create_folder(output_shp_path_by_day)

    crop_size = (1024, 1024)
    gap_size = 64

    if not os.path.isabs(original_image_path):
        input_image_path = os.path.join(current_path, original_image_path)

    ###########################################################################
    use_onnxruntime_inference = False
    print('Use pytorch inference')
    model = create_model(num_classes=NUM_CLASSES)
    model_path = os.path.join(current_path, f'./run/2025-06-14_13-56-02/best_model.pth')
    model.load_state_dict(
        torch.load(model_path, map_location=DEVICE,
                    weights_only=True))
    model.eval()  # 确保模型处于评估模式
    model.to(DEVICE)

    original_list = build_sorted_sentinel_1_list(original_image_path)
    logging.info(f'{original_list = }')
    pbar = tqdm(range(len(original_list)))
    pbar.set_description(f'Predicting')
    for i in pbar:
        geo_transform = original_list[i].geo_transform
        # modified_input_shp_path = os.path.join(current_path, input_shp_path)
        # mask = build_mask(list(reversed(original_list[i].shape)), geo_transform, modified_input_shp_path)
        annotations_list = get_boxes_per_image(model, f'{original_image_path}/{original_list[i].filename}',
                                               use_onnxruntime_inference)
        # valid_annotations_list = remove_invalid_tensor_by_mask(annotations_list, mask)
        valid_annotations_list = annotations_list
        # valid_annotations_list = all_annotations_list
        # print(f'{valid_annotations_list = }')
        if len(valid_annotations_list) != 0:
            nms_index = nms(valid_annotations_list[..., 1:5], valid_annotations_list[..., 5], NMS_THRESHOLD)
            out_annotations_list = valid_annotations_list[nms_index].cpu().numpy()
            ids = np.zeros((len(out_annotations_list), 1))
            out_annotations_list = np.concatenate((out_annotations_list, ids), axis=1)
            out_annotations_list[..., 1:5] = number2yolo(original_list[i].shape, out_annotations_list[..., 1:5])
            write_txt_label(f'{output_combine_label_path}/{original_list[i].filename_stem}.txt', out_annotations_list)
        else:
            with open(f'{output_combine_label_path}/{original_list[i].filename_stem}.txt', 'w'):
                pass

    ##
    ori_list = build_sorted_sentinel_1_list(original_image_path)
    original_name_list = [file.filename for file in ori_list]

    annotations_name_list = [os.path.splitext(annotation_name)[0]
                             for annotation_name in natsorted(os.listdir(output_combine_label_path))
                             if os.path.splitext(annotation_name)[1] == '.txt']

    out_annotations_list = [arrange_label(f'{output_combine_label_path}/{annotations_name}.txt',
                                          ori_list[i].shape)
                            for i, annotations_name in enumerate(annotations_name_list)]
    acquire_time_list = [item.acquire_time for item in ori_list]
    # platform_count_list = np.zeros(len(ori_list) - 2)
    ship_count_list = np.zeros(len(ori_list) - 2)

    modified_out_annotations_list = out_annotations_list.copy()


    for i in tqdm(range(len(ori_list))):
        ori_image_stem = os.path.splitext(ori_list[i].filename)[0]
        ori_image_name = ori_list[i].filename
        info = modified_out_annotations_list[i].copy()
        info[..., 1:5] = number2yolo(ori_list[i].shape, info[..., 1:5])
        # logging.info(f'{info = }')
        write_txt_label(f'{modified_label_path}/{ori_image_stem}.txt', info)

        _, suffix = os.path.splitext(ori_image_name)
        ori_image = read_image_as_ndarray(f'{original_image_path}/{ori_image_name}',
                                          as_rgb=True, channel_combination=(0,0,0), ndarray_dtype=np.uint8)
        geo_transform = ori_list[i].geo_transform
        projection = ori_list[i].projection
        draw_box_on_one_image(output_path, modified_out_annotations_list[i], ori_image, ori_image_stem, geo_transform,
                              projection, write_tif=True)

    ###############################################################################################################
    initial_logging_formatter()

    ori_list = []
    original_image_names = [image_name for image_name in natsorted(os.listdir(original_image_path))
                            if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]

    pattern = r'1SDV_(.*)T(.*)T'

    for original_image_name in original_image_names:
        stem, _ = os.path.splitext(original_image_name)
        acquire_time_select = re.search(pattern, stem)
        geo_transform = None
        # projection = None
        if acquire_time_select:
            acquire_time = str(acquire_time_select.group(1))
            year = int(acquire_time[:4])
            month = int(acquire_time[4:6])
            day = int(acquire_time[6:8])
        else:
            raise RuntimeError('acquire time not found !')

        if os.path.splitext(original_image_name)[-1] in ['.tif', '.tiff']:

            with gdal.Open(f'{original_image_path}/{original_image_name}') as tiff_file:
                geo_transform = tiff_file.GetGeoTransform()
                # projection = tiff_file.GetProjection()
        ori_list.append({'image_original_stem': stem,
                         # 'image_original_name': original_image_name,
                         'shape': imagesize.get(f'{original_image_path}/{original_image_name}'),
                         'geo_transform': geo_transform,
                         # 'projection': projection,
                         'acquire_time': datetime.date(year, month, day)
                         })
    logging.info(len(ori_list))
    # ori_list.pop(0)
    # ori_list.pop(-1)
    acquire_time_list = [ori_list_item['acquire_time'] for ori_list_item in ori_list]

    result_list = []
    max_platform_id = 0
    for i in range(len(ori_list)):
        result = read_txt_label(f'{modified_label_path}/{ori_list[i]['image_original_stem']}.txt')
        result[..., 1:5] = yolo2number(ori_list[i]['shape'], result[..., 1:5])

        max_platform_id = int(np.max((np.max(result[..., -1]), max_platform_id)))

        result_list.append(result)
    # logging.info(f'result_list = {result_list}')
    # logging.info(len(result_list))
    get_platform_ship_coordinates_by_id(result_list, ori_list, max_platform_id)

    platform_coordinates_by_day, ship_coordinates_by_day = get_platform_ship_coordinates_by_day(result_list,
                                                                                                ori_list)
    platform_coordinates = get_platform_coordinates(result_list, max_platform_id)
    # logging.info(f'platform_coordinates = {platform_coordinates}')

    geo_transform_list = [item['geo_transform'] for item in ori_list]
    ##########



    ship_counts = [np.sum(result_list[i][..., 0] == 1) for i in range(len(ori_list))]

    anomaly_events = acquire_time_list.copy()
    no_anomaly_index = []
    anomaly_index = np.zeros(len(ship_counts))
    anomaly_counts = ship_counts.copy()
    for i in range(len(ship_counts)):
        if ship_counts[i] > 3:
            no_anomaly_index.append(i)
        else:
            anomaly_index[i] = 1
    # no_anomaly_index.append(len(ship_counts) - 1)
    anomaly_events = np.delete(anomaly_events, no_anomaly_index)
    anomaly_counts = np.delete(anomaly_counts, no_anomaly_index)
    print(f'{anomaly_events = }')
    print(f'{anomaly_counts = }')
    output_csv_file = f'{output_stem_path}/ship_number.csv'
    with open(output_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['date', 'number', 'anomaly'])
        writer.writeheader()
        for i in range(len(ship_counts)):
            row = {'date': acquire_time_list[i].strftime("%Y/%m/%d"), 'number': ship_counts[i],
                   'anomaly': anomaly_index[i]}
            writer.writerow(row)

    content = [row for day_item in ship_coordinates_by_day for row in day_item]
    output_summary_csv_file = f'{output_stem_path}/ship_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_summary_csv_file, head)

    fig, ax1 = plt.subplots()
   
    events_str: List[str | None] = [None for i in range(len(acquire_time_list))]
    for i, item_d in enumerate(acquire_time_list):
        events_str[i] = item_d.strftime('%Y-%m-%d')

    logging.info(f'event_str = {events_str}')

    ax1.plot(acquire_time_list, ship_counts, linewidth=5, color='red', marker=None, label='船舶数量')
    ax1.scatter(anomaly_events, anomaly_counts, facecolors='#FAFA33', edgecolor='black', marker='o', s=200,
                linewidths=1.5,
                zorder=2)

    with open(f'{output_stem_path}/finish.txt', 'w') as finish_txt_file:
        pass
