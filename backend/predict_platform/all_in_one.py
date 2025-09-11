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
from modify_type import valid_box_on_2_images, draw_box_on_one_image
from predict import read_grid_image_list, get_boxes_per_image, read_original_image_list, generate_cluster, build_mask
from auto_crop import batch_crop_image_by_grid
from summarize_platform import calculate_iou_score, search_special_events, write_csv, calculate_time_score, \
    calculate_size_score
from util.image_io import read_image_as_ndarray
from util.labels import number2yolo, write_txt_label, arange_label, convert_boxes, remove_invalid_tensor_by_mask, \
    read_txt_label, yolo2number, image_coordinates_2_latitude_longitude
from utils import create_folder, initial_logging_formatter, get_platform_ship_coordinates_by_id, \
    get_platform_ship_coordinates_by_day, get_platform_coordinates, get_platform_sizes, calculate_iou, write_shp_file, \
    generate_trend_by_date, build_sorted_sentinel_1_list

stem_path = '../public/sk10_platform'

if __name__ == "__main__":
    current_file_path = os.path.abspath(__file__)
    current_path = os.path.dirname(current_file_path)

    # stem_path = os.path.join(current_path, f'/public/sk10_platform')

    output_stem_path = f'{stem_path}/output'
    # input_path = f'{stem_path}/grid_images'
    ground_truth_path = f'{stem_path}/labels_t'
    output_path = f'{output_stem_path}/predict'
    output_preview_path = f'{output_stem_path}/preview'
    output_combine_label_path = f'{output_stem_path}/labels/combine'
    original_image_path = f'{stem_path}/original_images'
    modified_label_path = f'{output_stem_path}/labels/modified'

    # input_shp_path = os.path.join(current_path, f'/malaysia_range_for_test/malaysia_range_for_test.shp')
    input_shp_path = f'./malaysia_range_for_test/malaysia_range_for_test.shp'
    output_shp_path_stable = f'{output_stem_path}/shapefile_stable'
    output_shp_path_occur = f'{output_stem_path}/shapefile_occur'
    output_shp_path_disappear = f'{output_stem_path}/shapefile_disappear'
    output_shp_path_occur_and_disappear = f'{output_stem_path}/shapefile_occur_and_disappear'
    output_shp_path_by_day = f'{output_stem_path}/by_day'
    # print(f'{output_stem_path}/finish.txt')

    # create_folder(input_path)
    create_folder(output_path)
    create_folder(output_combine_label_path)
    create_folder(modified_label_path)
    create_folder(output_shp_path_stable)
    create_folder(output_shp_path_occur)
    create_folder(output_shp_path_disappear)
    create_folder(output_shp_path_occur_and_disappear)
    create_folder(output_shp_path_by_day)

    crop_size = (1024, 1024)
    gap_size = 64

    if not os.path.isabs(original_image_path):
        input_image_path = os.path.join(current_path, original_image_path)

    ###########################################################################
    use_onnxruntime_inference = False
    print('Use pytorch inference')
    model = create_model(num_classes=NUM_CLASSES)
    model_path = os.path.join(current_path, f'./run/2025-03-27_16-08-11/best_model.pth')
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
        modified_input_shp_path = os.path.join(current_path, input_shp_path)
        mask = build_mask(list(reversed(original_list[i].shape)), geo_transform, modified_input_shp_path)
        annotations_list = get_boxes_per_image(model, f'{original_image_path}/{original_list[i].filename}',
                                               use_onnxruntime_inference)
        valid_annotations_list = remove_invalid_tensor_by_mask(annotations_list, mask)
        # valid_annotations_list = all_annotations_list
        # logging.info(f'{valid_annotation_list = }')
        nms_index = nms(valid_annotations_list[..., 1:5], valid_annotations_list[..., 5], NMS_THRESHOLD)
        out_annotations_list = valid_annotations_list[nms_index].cpu().numpy()
        ids = np.zeros((len(out_annotations_list), 1))
        out_annotations_list = np.concatenate((out_annotations_list, ids), axis=1)
        out_annotations_list[..., 1:5] = number2yolo(original_list[i].shape, out_annotations_list[..., 1:5])
        write_txt_label(f'{output_combine_label_path}/{original_list[i].filename_stem}.txt', out_annotations_list)

    ##
    ori_list = build_sorted_sentinel_1_list(original_image_path)
    original_name_list = [file.filename for file in ori_list]

    annotations_name_list = [os.path.splitext(annotation_name)[0]
                             for annotation_name in natsorted(os.listdir(output_combine_label_path))
                             if os.path.splitext(annotation_name)[1] == '.txt']

    out_annotations_list = [arange_label(f'{output_combine_label_path}/{annotations_name}.txt',
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

        platform_ious = np.zeros(len(annotations_i) - 1, dtype=np.float32)
        platform_i_bboxes_array = np.asarray(
            [item[..., 1:5] for item in annotations_i]).squeeze()

        if platform_i_bboxes_array.ndim < 2:
            platform_i_bboxes_array = np.concatenate(
                (np.reshape(platform_i_bboxes_array, (1, 4)), np.reshape(platform_i_bboxes_array, (1, 4))), axis=0)
        platform_ious = [calculate_iou(platform_i_bboxes_array[i], platform_i_bboxes_array[i + 1]) for i in
                            range(len(platform_i_bboxes_array) - 1)]
        platform_size = np.mean([(item[2] - item[0]) * (item[3] - item[1]) for item in platform_i_bboxes_array])

        iou_score = calculate_iou_score(platform_ious)
        time_score = calculate_time_score((acquire_time_i[-1] - acquire_time_i[0]).days)
        p1 = iou_score * time_score
        if p1 < 0.5 or calculate_size_score(platform_size) < 0.5:
            remove_ids.append(i)

    remove_index = np.asarray(remove_ids) - 1

    map_list = np.zeros((max_platform_id - len(remove_ids), 2), dtype=np.intp)
    map_list[..., 0] = np.reshape(np.delete(range(1, max_platform_id + 1), remove_index), -1)
    modified_map_list = map_list.copy()
    for i, item in enumerate(map_list):
        j = item[0]
        index = np.searchsorted(remove_ids, j)
        modified_map_list[i, 1] = index

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

    for i in tqdm(range(1, len(ori_list) - 1)):
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
    ori_list.pop(0)
    ori_list.pop(-1)
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
    platform_geo_location = platform_coordinates.copy()
    platform_geo_location[..., 1:] = image_coordinates_2_latitude_longitude(geo_transform_list,
                                                                            platform_coordinates[..., 1:])
    logging.info(f'platform_geo_location = {platform_geo_location}')
    platform_sizes = get_platform_sizes(result_list, max_platform_id)
    logging.info(f'platform_sizes = {platform_sizes}')

    platform_annotations = [[np.array([]) for j in range(len(ori_list))] for i in range(max_platform_id)]
    platform_lifetime = np.zeros((max_platform_id, len(ori_list)), dtype=np.bool_)
    for i in range(max_platform_id):
        for j in range(len(ori_list)):
            platform_annotations[i][j] = result_list[j][np.where(result_list[j][:, -1] == i + 1)]
            platform_lifetime[i][j] = True if (platform_annotations[i][j].size != 0) else False

    platform_ious = [[np.array([]) for j in range(len(ori_list))] for i in range(max_platform_id)]
    for i in range(max_platform_id):
        print(i)
        platform_i_bboxes_array = np.asarray(
            [item[..., 1:5] for item in platform_annotations[i] if len(item) != 0]).squeeze()
        print(platform_i_bboxes_array)
        platform_ious[i] = [calculate_iou(platform_i_bboxes_array[i], platform_i_bboxes_array[i + 1]) for i in
                            range(len(platform_i_bboxes_array) - 1)]
        # calculate_iou()
        print(platform_ious[i])
        pass
    iou_scores = [calculate_iou_score(platform_ious[i]) for i in range(max_platform_id)]
    print(iou_scores)

    # logging.info(classification_list)
    # logging.info(stable_count)
    # logging.info(occur_count)
    # logging.info(disappear_count)
    stable_index = np.where((platform_lifetime[..., 0] == True) & (platform_lifetime[..., -1] == True))[0]
    # logging.info(stable_index)
    occur_and_disappear_index = np.where((platform_lifetime[..., 0] == False) & (platform_lifetime[..., -1] == False))[
        0]
    occur_index = np.where((platform_lifetime[..., 0] == False) & (platform_lifetime[..., -1] == True))[0]
    disappear_index = np.where((platform_lifetime[..., 0] == True) & (platform_lifetime[..., -1] == False))[0]
    platform_geo_location_stable = platform_geo_location[stable_index, ...]
    platform_geo_location_occur = platform_geo_location[occur_index, ...]
    platform_geo_location_disappear = platform_geo_location[disappear_index, ...]
    platform_geo_location_occur_and_disappear = platform_geo_location[occur_and_disappear_index, ...]
    logging.info(f'count of stable platform = {len(platform_geo_location_stable)}')
    logging.info(f'count of occurred platform = {len(platform_geo_location_occur)}')
    logging.info(f'count of disappeared platform = {len(platform_geo_location_disappear)}')
    logging.info(f'count of occurred and disappeared platform = {len(platform_geo_location_occur_and_disappear)}')
    logging.info(platform_geo_location_occur)
    logging.info(platform_geo_location_occur_and_disappear)

    occur_array = []
    disappear_array = []
    for i in range(len(platform_geo_location_occur[..., 0])):
        id = int(platform_geo_location_occur[..., 0][i])
        time_line = platform_lifetime[id - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == False and time_line[w + 1] == True:
                occur_array.append(
                    [acquire_time_list[w + 1], platform_geo_location_occur[i][1], platform_geo_location_occur[i][2],
                     id])

    for i in range(len(platform_geo_location_disappear[..., 0])):
        id = int(platform_geo_location_disappear[..., 0][i])
        time_line = platform_lifetime[id - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == True and time_line[w + 1] == False:
                disappear_array.append(
                    [acquire_time_list[w + 1], platform_geo_location_disappear[i][1],
                     platform_geo_location_disappear[i][2], id])

    for i in range(len(platform_geo_location_occur_and_disappear[..., 0])):
        id = int(platform_geo_location_occur_and_disappear[..., 0][i])
        time_line = platform_lifetime[id - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == False and time_line[w + 1] == True:
                occur_array.append([acquire_time_list[w + 1], platform_geo_location_occur_and_disappear[i][1],
                                    platform_geo_location_occur_and_disappear[i][2], id])
            if time_line[w] == True and time_line[w + 1] == False:
                disappear_array.append([acquire_time_list[w + 1], platform_geo_location_occur_and_disappear[i][1],
                                        platform_geo_location_occur_and_disappear[i][2], id])

    logging.info(f'occur_array = {np.array(occur_array)}')
    logging.info(f'platform_geo_location_occur = {platform_geo_location_occur}')

    special_array = search_special_events(occur_array, disappear_array, platform_geo_location)

    output_shp_path = output_shp_path_stable
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_stable'
    write_shp_file(csv_path, platform_geo_location_stable, output_shp_path, layer_name)

    output_shp_path = output_shp_path_occur
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_occur'
    write_shp_file(csv_path, platform_geo_location_occur, output_shp_path, layer_name)

    output_shp_path = output_shp_path_disappear
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_disappear'
    write_shp_file(csv_path, platform_geo_location_disappear, output_shp_path, layer_name)

    output_shp_path = output_shp_path_occur_and_disappear
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_occur_and_disappear'
    write_shp_file(csv_path, platform_geo_location_occur_and_disappear, output_shp_path, layer_name)

    time_table: List[list[datetime.date | None]] = [[None, None] for _ in range(max_platform_id)]
    print(f'time_table = {time_table}')

    for i in range(max_platform_id):
        left_index = np.min(np.where(platform_lifetime[i, :]))
        right_index = np.max(np.where(platform_lifetime[i, :]))
        if left_index != 0:
            time_table[i][0] = acquire_time_list[left_index]
        else:
            time_table[i][0] = acquire_time_list[0]

        if right_index != len(acquire_time_list) - 1:
            time_table[i][1] = acquire_time_list[right_index]
        else:
            time_table[i][1] = acquire_time_list[-1]

    logging.info(f'time_table = {time_table}')
    # logging.info(len(time_table))
    logging.info(
        f'id       image_x       image_y       longitude       latitude        occur_time        disappear_time')
    full_result = np.concatenate((platform_coordinates, platform_geo_location[..., 1:], time_table), axis=1)
    logging.info(f'full_result =\n {full_result}')

    platform_counts = [np.sum(result_list[i][..., 0] == 2) for i in range(len(ori_list))]

    anomaly_events = acquire_time_list.copy()
    no_anomaly_index = [0]
    anomaly_index = np.zeros(len(platform_counts))
    anomaly_counts = platform_counts.copy()
    for i in range(1, len(platform_counts) - 1):
        if platform_counts[i] == platform_counts[i - 1]:
            no_anomaly_index.append(i)
        else:
            anomaly_index[i] = 1
    no_anomaly_index.append(len(platform_counts) - 1)
    anomaly_events = np.delete(anomaly_events, no_anomaly_index)
    anomaly_counts = np.delete(anomaly_counts, no_anomaly_index)

    output_csv_file = f'{output_stem_path}/platform_number.csv'
    with open(output_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['date', 'number', 'anomaly'])
        writer.writeheader()
        for i in range(len(platform_counts)):
            row = {'date': acquire_time_list[i].strftime("%Y/%m/%d"), 'number': platform_counts[i],
                   'anomaly': anomaly_index[i]}
            writer.writerow(row)

    content = [row for day_item in platform_coordinates_by_day for row in day_item]
    content.sort(key=lambda x: x[1])
    content = np.asarray(content)
    content[..., [0, 1]] = content[..., [1, 0]]
    output_summary_csv_file = f'{output_stem_path}/platform_summary_by_id.csv'
    head = ['id', 'date',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']
    write_csv(content, output_summary_csv_file, head)

    content = [row for day_item in platform_coordinates_by_day for row in day_item]
    output_summary_csv_file = f'{output_stem_path}/platform_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_summary_csv_file, head)

    content = [row for day_item in ship_coordinates_by_day for row in day_item]
    output_summary_csv_file = f'{output_stem_path}/ship_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_summary_csv_file, head)

    output_summary_csv_file = f'{output_stem_path}/occur.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['type', 'date', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        for item in occur_array:
            if platform_sizes[item[3] - 1, 0] * platform_sizes[item[3] - 1, 1] * 10 * 10 >= 50:
                row = {'type': "occur",
                       'date': item[0],
                       'geo_x_center': item[1],
                       'geo_y_center': item[2],
                       'id': item[3]
                       }
                writer.writerow(row)

    output_shapefile = f'{output_stem_path}/occur_events'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N

    # 创建图层
    layer_name = 'occur_events'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('DATE', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    layer.CreateField(fieldDefn)

    # 添加点要素
    for date, lon, lat, platform in occur_array:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)

        date_str = datetime.datetime.strftime(date, '%Y-%m-%d')

        feature.SetField('DATE', date_str)  # 设置属性字段
        feature.SetField('PLATFORM', platform)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/disappear.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['type', 'date', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        for item in disappear_array:
            row = {'type': "disappear",
                   'date': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'id': item[3]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/disappear_events'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N\

    # 创建图层
    layer_name = 'disappear_events'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('DATE', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    layer.CreateField(fieldDefn)

    # 添加点要素
    for date, lon, lat, platform in disappear_array:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)

        date_str = datetime.datetime.strftime(date, '%Y-%m-%d')

        feature.SetField('DATE', date_str)  # 设置属性字段
        feature.SetField('PLATFORM', platform)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/special.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['date_occur', 'date_disappear', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        ############## filter area
        for item in special_array:
            row = {'date_occur': item[0], 'date_disappear': item[1],
                   'geo_x_center': item[2],
                   'geo_y_center': item[3],
                   'id': item[4]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/special_events'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N\

    # 创建图层
    layer_name = 'special_events'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('DATE_1', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('DATE_2', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    layer.CreateField(fieldDefn)

    # 添加点要素
    for date_occur, date_disappear, lon, lat, platform in special_array:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)

        date_occur_str = datetime.datetime.strftime(date_occur, '%Y-%m-%d')
        date_disappear_str = datetime.datetime.strftime(date_disappear, '%Y-%m-%d')

        feature.SetField('DATE_1', date_occur_str)  # 设置属性字段
        feature.SetField('DATE_2', date_disappear_str)  # 设置属性字段
        feature.SetField('PLATFORM', platform)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': calculate_time_score((time_table[i][1] - time_table[i][0]).days) * calculate_size_score(
                       platform_sizes[i][1] * platform_sizes[i][2] * iou_scores[i])
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', (time_table[i][1] - time_table[i][0]).days)  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         calculate_time_score((time_table[i][1] - time_table[i][0]).days) * calculate_size_score(
                             platform_sizes[i][1] * platform_sizes[i][2]) * iou_scores[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    days_list = np.asarray([int((time_table[i][1] - time_table[i][0]).days) for i in range(max_platform_id)])
    time_score_list = [calculate_time_score((time_table[i][1] - time_table[i][0]).days) for i in range(max_platform_id)]
    size_score_list = [calculate_size_score(platform_sizes[i][1] * platform_sizes[i][2]) for i in
                       range(max_platform_id)]
    p_score_list = np.asarray([iou_scores[i] * time_score_list[i] * size_score_list[i] for i in range(max_platform_id)])

    platform_geo_location_high_conf = platform_geo_location[np.where(p_score_list >= 0.3)]
    print(platform_geo_location_high_conf)
    days_list_high_conf = days_list[np.where(p_score_list >= 0.3)]
    p_score_list_high_conf = p_score_list[np.where(p_score_list >= 0.3)]

    platform_geo_location_high_conf_stable = platform_geo_location_high_conf[
        np.where(days_list_high_conf == np.max(days_list))]
    print(platform_geo_location_high_conf_stable)
    days_list_high_conf_stable = days_list_high_conf[np.where(days_list_high_conf == np.max(days_list))]
    p_score_list_high_conf_stable = p_score_list_high_conf[np.where(days_list_high_conf == np.max(days_list))]

    platform_geo_location_high_conf_move = platform_geo_location_high_conf[
        np.where(days_list_high_conf < np.max(days_list))]
    print(platform_geo_location_high_conf_move)
    days_list_high_conf_move = days_list_high_conf[np.where(days_list_high_conf < np.max(days_list))]
    p_score_list_high_conf_move = p_score_list_high_conf[np.where(days_list_high_conf < np.max(days_list))]

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_high_conf.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_high_conf):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': p_score_list_high_conf[i]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency_high_conf'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency_high_conf'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location_high_conf):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_high_conf[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         p_score_list_high_conf[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_stable.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_high_conf_stable):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': p_score_list_high_conf_stable[i]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency_stable'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency_stable'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location_high_conf_stable):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_high_conf_stable[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         p_score_list_high_conf_stable[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_stable.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_high_conf_stable):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': p_score_list_high_conf_stable[i]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency_move'
    create_folder(output_shapefile)
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency_move'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location_high_conf_move):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_high_conf_move[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         p_score_list_high_conf_move[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    ship_counts = [np.sum(result_list[i][..., 0] == 1) for i in range(len(ori_list))]

    acquire_time_list.pop(0)
    acquire_time_list.pop(-1)
    platform_counts = platform_counts[1:-1]
    fig, ax1 = plt.subplots()
    # fig.autofmt_xdate(rotation=25)

    trend = generate_trend_by_date(platform_counts, acquire_time_list)
    # logging.info(f'trend = {trend}')
    # ax1.xaxis.set_major_locator(years)
    # ax1.xaxis.set_major_locator(months)
    # ax.xaxis.set_minor_locator(months)
    # ax1.xaxis.set_minor_locator(days)
    events_str: List[str | None] = [None for i in range(len(acquire_time_list))]
    for i, item_d in enumerate(acquire_time_list):
        events_str[i] = item_d.strftime('%Y-%m-%d')
    # ax1.set_xticks(range(len(events_str)))
    # time_format = matplotlib.dates.DateFormatter('%Y-%m-%d')
    # ax1.xaxis.set_major_formatter(time_format)
    logging.info(f'event_str = {events_str}')

    ax1.plot(acquire_time_list, platform_counts, linewidth=5, color='red', marker=None, label='油气设施总数量')
    ax1.scatter(anomaly_events, anomaly_counts, facecolors='#FAFA33', edgecolor='black', marker='o', s=200,
                linewidths=1.5,
                zorder=2)

    texts = []

    ax1.set_title('number of platform')
    ax1.set_ylabel('数量')
    ax1.set_yticks(np.arange(min(platform_counts) - 1, max(platform_counts) + 2, 1, dtype=np.intp))
    ax1.set_ylim(min(platform_counts) - 2.5, max(platform_counts) + 0.5)
    ax1.plot(acquire_time_list, trend, linewidth=2.5, label='总数量变化趋势')

    one_day = datetime.timedelta(days=1)
    events_1 = acquire_time_list.copy()
    for index, i in enumerate(acquire_time_list):
        j = i - one_day
        events_1[index] = j

    events_2 = acquire_time_list.copy()
    for index, i in enumerate(acquire_time_list):
        j = i + one_day
        events_2[index] = j

    events_1_str: List[str | None] = [None for i in range(len(events_1))]
    for i, item in enumerate(events_1):
        events_1_str[i] = item.strftime('%Y-%m-%d')

    fig.legend(loc="upper left", bbox_to_anchor=(0.005, 1), bbox_transform=ax1.transAxes)
    # plt.show()

    with open(f'{output_stem_path}/finish.txt', 'w') as finish_txt_file:
        pass
