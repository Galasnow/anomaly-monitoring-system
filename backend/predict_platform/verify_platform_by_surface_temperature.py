import logging
import os
import csv
import re
import warnings
import datetime

import cv2
import numpy as np
from matplotlib import pyplot as plt

from natsort import natsorted
from osgeo import gdal
from tqdm import tqdm

from config import original_image_path
from dataset import support_file_list
from landsat_st_preprocess import date_to_new_format, invalid_value, process_landsat_st, \
    percent_average
from util.labels import get_latitude_longitude, latitude_longitude_2_image_coordinates
from utils import create_folder


def sort_by_time(landsat_st_file_list):
    st_time_array = np.zeros_like(landsat_st_file_list)
    for i, st_file in enumerate(landsat_st_file_list):

        pattern = r'LC(.*)_(.*)_(.*)'

        stem, _ = os.path.splitext(st_file)
        acquire_time_select = re.search(pattern, stem)
        if acquire_time_select:
            acquire_time = str(acquire_time_select.group(3))
            year = int(acquire_time[:4])
            month = int(acquire_time[4:6])
            day = int(acquire_time[6:8])
        else:
            raise RuntimeError('acquire time not found !')

        st_time = datetime.date(year, month, day)
        st_time_array[i] = st_time
    sorted_index = np.argsort(st_time_array)
    landsat_st_file_list = list(np.asarray(landsat_st_file_list, dtype = datetime.date)[sorted_index])
    return landsat_st_file_list


def read_csv(path):
    csv_reader = csv.reader(open(path, mode='r'))
    out_list = []
    for row in csv_reader:
        out_list.append(row)
    out_list.pop(0)
    return out_list


def generate_mask(image_shape, rectangles):
    mask = np.zeros(image_shape, dtype=np.uint8)
    # pts = np.array([[[1200, 50], [1200, 1400], [50, 1400], [50, 3200], [1000, 3200], [1000, 4500],
    #                  [3700, 4500], [4650, 700], [2300, 700], [2300, 50]]],
    #                dtype=np.int32)
    rectangles = np.reshape(rectangles, (-1, 4, 2))
    mask = cv2.fillPoly(mask, rectangles, color=(255, 255, 255))
    new_mask = np.asarray(mask, dtype=np.bool_)
    return new_mask


def generate_temperature_delta_1(image, item, target_area, polygon_mask, output_path):
    # file = gdal.Open(f'{path}/{item}')
    # image = file.ReadAsArray()
    # geo_transform = file.GetGeoTransform()
    stem = os.path.splitext(item)[0]
    out_file = process_landsat_st(image, stem, output_path)

    platform_mask = target_area.copy()
    kernel = np.ones((3, 3), np.uint8)
    buffered_target_area = (cv2.dilate(target_area.astype(np.uint8), kernel, iterations=5)).astype(np.bool_)

    water_mask = np.logical_xor(target_area, buffered_target_area)
    water_mask = np.logical_xor(water_mask, polygon_mask)
    # logging.info(np.sum(platform_mask))
    # logging.info(np.sum(water_mask))
    select_area_platform = out_file[platform_mask]
    big = percent_average(select_area_platform, [0.5, 0.9])
    select_area_water = out_file[water_mask]
    small = percent_average(select_area_water, [0.5, 0.9])

    # logging.info(f'big = {big}, small = {small}')

    if big != invalid_value and small != invalid_value:
        delta = big - small
    else:
        delta = invalid_value

    return big, small, delta


def xyxy2x1y1x2y2x3y3x4y4(input_array):
    """
    x_min, y_min, x_max, y_max
    -->
    x1, y1, x2, y2, x3, y3, x4, y4
    """
    ex_flag = False
    if input_array.ndim == 1:
        ex_flag = True
        input_array = np.expand_dims(input_array, axis=0)
    output_array = np.zeros((input_array.shape[0], 8), dtype=input_array.dtype)
    for i, item in enumerate(input_array):
        output_array[i, 0] = input_array[i, 0]
        output_array[i, 1] = input_array[i, 1]
        output_array[i, 2] = input_array[i, 2]
        output_array[i, 3] = input_array[i, 1]
        output_array[i, 4] = input_array[i, 2]
        output_array[i, 5] = input_array[i, 3]
        output_array[i, 6] = input_array[i, 0]
        output_array[i, 7] = input_array[i, 3]
    if ex_flag:
        output_array = np.squeeze(output_array, axis=0)
    return output_array


if __name__ == "__main__":
    # a = np.array([1, 1, 1, 2])
    # b = np.array([2,3,4,1])
    # logging.info(np.expand_dims(a, axis=1))
    # logging.info(np.concatenate((np.expand_dims(a, axis=1), np.expand_dims(b, axis=1)), axis=1))
    # a = np.array([[1, 1, -999, 2],[-999, 2, -999, 1]])
    # logging.info(np.where(a==-999))
    # logging.info(np.delete(a, np.where(a==-999), axis=None))
    # logging.info(a[np.where(a!=-999)])

    paths = ['D:/zhongyan/gee_download_wenlai/landsat/119057', 'D:/zhongyan/gee_download_wenlai/landsat/120058']

    polygon_shp = r'H:\zhongyan\gee_download_wenlai\landsat\target_area\target_area.shp'
    platform_coordinates_by_id_file = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\test_set\malaysia_wenlai\platform_summary_by_id.csv'
    platform_coordinates_by_day_file = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\test_set\malaysia_wenlai\platform_summary_by_date.csv'
    ship_coordinates_by_day_file = r'H:\zhongyan\ship_drilling_platform\predict_platform\datasets\test_set\malaysia_wenlai\ship_summary_by_date.csv'

    platform_coordinates_by_id = read_csv(platform_coordinates_by_id_file)
    platform_coordinates_by_day = read_csv(platform_coordinates_by_day_file)
    ship_coordinates_by_day = read_csv(ship_coordinates_by_day_file)
    logging.info(platform_coordinates_by_id[0])
    # logging.info(datetime.datetime.strptime(platform_coordinates_by_day[0][0], '%Y-%m-%d'))

    platform_ids = [platform_coordinates_by_id[i][0] for i in
                    range(len(platform_coordinates_by_id))]
    platform_ids = natsorted(np.unique(platform_ids))

    ship_s1_date_str_list = [ship_coordinates_by_day[i][0] for i in
                             range(len(ship_coordinates_by_day))]
    # ship_s1_date_list = [datetime.strptime(ship_coordinates_by_day[i][0], '%Y-%m-%d') for i in
    #                      range(len(ship_coordinates_by_day))]
    # ship_s1_date_list = np.unique(ship_s1_date_list)
    # logging.info(ship_s1_date_list)

    original_image_names = [image_name for image_name in natsorted(os.listdir(original_image_path))
                            if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    # platform_ids = np.delete(platform_ids, [0,1,2,3,4,5,6,7,8,9])
    # logging.info(platform_ids)
    # platform_ids = np.asarray(platform_ids, dtype=np.intp)
    platform_ids = platform_ids[27:28]
    # logging.info(platform_ids)
    pattern = r'LC(.*)_(.*)_(.*)'
    for j in tqdm(platform_ids):
        # logging.info(j)
        finish_flag = False
        index_platform = [i for i, item in enumerate(platform_coordinates_by_id) if item[0] == j]
        # logging.info(index_platform)
        # logging.info(len(index_platform))
        select_platform_i_record_list = platform_coordinates_by_id[index_platform[0]: index_platform[-1] + 1]
        # logging.info(select_platform_i_record_list)
        # logging.info(len(select_platform_i_record_list))

        platform_i_s1_date_str_list = [select_platform_i_record_list[i][1] for i in
                                     range(len(select_platform_i_record_list))]
        platform_i_s1_date_list = [datetime.datetime.strptime(select_platform_i_record_list[i][1], '%Y-%m-%d') for i in
                                 range(len(select_platform_i_record_list))]
        platform_i_s1_date_list = np.unique(platform_i_s1_date_list)
        # logging.info(platform_i_s1_date_list)

        for path in paths:
            output_path = f'{path}/output/'
            create_folder(output_path)
            # landsat_st_file_list = [file_name for file_name in os.listdir(path) if file_name.endswith('ST_B10.TIF')]
            # time_range = (datetime.date(2017, 1, 1), datetime.date(2025, 1, 1))
            time_range = (platform_i_s1_date_list[0], platform_i_s1_date_list[-1])
            landsat_st_file_list = [file_name for file_name in os.listdir(path) if
                                    file_name.startswith('LC') & file_name.endswith('tif')]
            # logging.info(landsat_st_file_list)
            landsat_st_file_list = sort_by_time(landsat_st_file_list)
            # logging.info(landsat_st_file_list)
            time = natsorted([os.path.splitext(file_name)[0].split('_')[-1] for file_name in landsat_st_file_list])
            time_datetime_list = natsorted(
                [datetime.datetime.strptime(date_to_new_format(date), '%Y/%m/%d') for date in time])
            insert_place_start = np.searchsorted(time_datetime_list, time_range[0], side='left')
            insert_place_end = np.searchsorted(time_datetime_list, time_range[1], side='right')
            # logging.info(insert_place_start, insert_place_end)

            # time_filter = (insert_place_start, insert_place_end)
            landsat_st_file_list = landsat_st_file_list[insert_place_start: insert_place_end + 1]
            # time = time[insert_place_start: insert_place_end + 1]
            time_datetime_list = time_datetime_list[insert_place_start: insert_place_end + 1]
            # logging.info(time)
            # logging.info(time_datetime_list)
            center_list = np.full(len(time_datetime_list), invalid_value, dtype=np.float32)
            periphery_list = np.full(len(time_datetime_list), invalid_value, dtype=np.float32)
            delta_list = np.full(len(time_datetime_list), invalid_value, dtype=np.float32)

            for i, st_file in enumerate(landsat_st_file_list):
                stem, _ = os.path.splitext(st_file)
                acquire_time_select = re.search(pattern, stem)
                if acquire_time_select:
                    acquire_time = str(acquire_time_select.group(3))
                    year = int(acquire_time[:4])
                    month = int(acquire_time[4:6])
                    day = int(acquire_time[6:8])
                else:
                    raise RuntimeError('acquire time not found !')

                st_time = datetime.date(year, month, day)
                # logging.info(st_time)
                insert_place = np.searchsorted(platform_i_s1_date_list, st_time, side='left')
                # logging.info(insert_place)
                selected_s1_date: datetime.date = platform_i_s1_date_list[min(int(insert_place), len(platform_i_s1_date_list) - 1)]
                # logging.info(selected_s1_date)

                with gdal.Open(f'{path}/{st_file}') as file:
                    image = file.ReadAsArray()
                    geo_transform_landsat = file.GetGeoTransform()

                # for k, date in enumerate(platform_i_s1_date_list):
                platform_s1_date_str_list = [platform_coordinates_by_day[i][0] for i in
                                             range(len(platform_coordinates_by_day))]

                ship_s1_date_str_list = [ship_coordinates_by_day[i][0] for i in
                                         range(len(ship_coordinates_by_day))]

                index_platform = [i for i, item in enumerate(platform_s1_date_str_list) if
                                  item == datetime.datetime.strftime(selected_s1_date, '%Y-%m-%d')]
                # logging.info(index_platform)
                # logging.info(len(index_platform))
                select_platform_record_list = platform_coordinates_by_day[index_platform[0]: index_platform[-1] + 1]
                # logging.info(select_platform_record_list)
                # logging.info(len(select_platform_record_list))

                target_platform_record_list = [item for item in select_platform_record_list if item[1] == j][0]
                # logging.info(f'target_platform_record_list = {target_platform_record_list}')

                with gdal.Open(f'{original_image_path}/{original_image_names[insert_place]}') as tiff_file:
                    geo_transform_s1 = tiff_file.GetGeoTransform()
                # logging.info(geo_transform)
                target_area_geo = np.asarray(target_platform_record_list[4:8], dtype=np.float32)
                # logging.info(f'target_area_geo = {target_area_geo}')
                target_area_geo[0:2] = get_latitude_longitude(geo_transform_s1, target_area_geo[0:2])
                target_area_geo[2:4] = get_latitude_longitude(geo_transform_s1, target_area_geo[2:4])

                target_area_image = target_area_geo.copy()
                target_area_image[..., 0:2] = latitude_longitude_2_image_coordinates(geo_transform_landsat,
                                                                                     target_area_geo[..., 0:2])
                target_area_image[..., 2:4] = latitude_longitude_2_image_coordinates(geo_transform_landsat,
                                                                                     target_area_geo[..., 2:4])
                target_area_image = np.asarray(target_area_image, dtype=np.intp)
                # logging.info(f'target_area_image = {target_area_image}')
                if -999 in target_area_image:
                    warnings.warn('invalid target area')
                    break

                select_platform_record_list = [item for item in select_platform_record_list if item[1] != j]

                # logging.info(len(select_platform_record_list))
                index_ship = [i for i, item in enumerate(ship_s1_date_str_list) if
                              item == datetime.datetime.strftime(selected_s1_date, '%Y-%m-%d')]
                # logging.info(index_ship)
                # logging.info(len(index_ship))
                select_ship_record_list = ship_coordinates_by_day[index_ship[0]: index_ship[-1] + 1]
                # logging.info(select_ship_record_list)
                # logging.info(len(select_ship_record_list))

                barrier = select_platform_record_list + select_ship_record_list
                # logging.info(f'barrier = {barrier}')
                # logging.info(len(barrier))

                barrier = np.asarray(barrier)
                barrier = np.asarray(barrier[..., 4:8], dtype=np.float32)
                # barrier = np.asarray(barrier, dtype=np.float32)

                barrier[..., 0:2] = get_latitude_longitude(geo_transform_s1, barrier[..., 0:2])
                barrier[..., 2:4] = get_latitude_longitude(geo_transform_s1, barrier[..., 2:4])
                # barrier[..., 4:6] = get_latitude_longitude(geo_transform_s1, barrier[..., 4:6])

                barrier_image = barrier.copy()
                barrier_image[..., 0:2] = latitude_longitude_2_image_coordinates(geo_transform_landsat, barrier[..., 0:2])
                barrier_image[..., 2:4] = latitude_longitude_2_image_coordinates(geo_transform_landsat, barrier[..., 2:4])
                barrier_image = np.asarray(barrier_image, dtype=np.intp)

                # logging.info(f'barrier_image = {barrier_image}')
                invalid_index = np.where((barrier_image[..., 0] == -999) | (barrier_image[..., 1] == -999) |
                                         (barrier_image[..., 2] == -999) | (barrier_image[..., 3] == -999))
                barrier_image = np.delete(barrier_image, invalid_index, axis=0)
                # logging.info(target_area_image)
                target_area_image = xyxy2x1y1x2y2x3y3x4y4(target_area_image)
                # logging.info(f'target_area_image = {target_area_image}')

                barrier_image = xyxy2x1y1x2y2x3y3x4y4(barrier_image)
                # logging.info(f'barrier_image = {barrier_image}')
                mask = generate_mask(image.shape[1:], barrier_image)

                target_area = np.zeros(image.shape[1:], dtype=np.uint8)
                pts = np.reshape(target_area_image, (-1, 2))
                image_pts = np.expand_dims(pts, axis=0)
                # logging.info(image_pts)
                # logging.info(image_pts.shape)
                target_area = cv2.fillPoly(target_area, image_pts, color=(255, 255, 255))
                target_area = np.asarray(target_area, dtype=np.bool_)
                # logging.info(target_area.shape)
                # logging.info(np.sum(target_area))
                if np.sum(target_area) == 0:
                    warnings.warn('no enough target area')
                    break

                center_list[i], periphery_list[i], delta_list[i] = (
                    generate_temperature_delta_1(image, st_file, target_area, mask, output_path))
                finish_flag = True

                # logging.info(f'barrier = {barrier}')
                # logging.info(f'target_area_geo = {target_area_geo}')

                # for item in barrier:
                #     logging.info(item)
            if finish_flag:
                logging.info(f'j = {j}')
                invalid_index = (delta_list == invalid_value)
                delta_list_valid = np.delete(delta_list, invalid_index)
                center_list_valid = np.delete(center_list, invalid_index)
                periphery_list_valid = np.delete(periphery_list, invalid_index)
                # logging.info(f'delta_list_valid = {delta_list_valid}')
                time_datetime_list_valid = np.delete(time_datetime_list, invalid_index)
                if len(delta_list_valid) == 0:
                    warnings.warn(f'no effect data for platform {j}')
                    break
                # logging.info(f'delta_list_valid = {delta_list_valid}')
                u = np.concatenate((np.expand_dims(time_datetime_list_valid, axis=1),
                                    np.expand_dims(center_list_valid, axis=1),
                                    np.expand_dims(periphery_list_valid, axis=1),
                                    np.expand_dims(delta_list_valid, axis=1)
                                    ), axis=1)
                # logging.info(u)
                new_u = np.array(sorted(u, key=lambda t: t[0]))

                logging.info(f'sorted result = {new_u}')

                plt.plot(new_u[..., 0], new_u[..., 1], linewidth=2, color='red', marker='o', label='center')
                plt.plot(new_u[..., 0], new_u[..., 2], linewidth=2, color='blue', marker='o', label='periphery')
                # plt.axhline(y=2, color='yellow', label='reference threshold line')
                plt.ylabel('Top 10% to 50% temperature / °C')
                plt.xlabel('date')
                plt.legend()
                fig = plt.gcf()
                fig.set_size_inches(16, 9)
                # plt.figure(figsize=(16, 9))

                # gcf: Get Current Figure
                # fig = plt.gcf()

                plt.savefig(
                    f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_verify_result/{j}_top_10_to_50_temperature.png',
                    dpi=200, pad_inches=0.01)
                plt.close()

                # plt.plot(time_datetime_list_valid, delta_list_valid, linewidth=2.5, marker='o', label='temperature')
                plt.plot(new_u[..., 0], new_u[..., 3], linewidth=2, color='green', marker='o',
                         label='center - periphery')
                # plt.axhline(y=2, color='yellow', label='reference threshold line')
                plt.ylabel('Delta top 10% to 50% temperature  / °C')
                plt.xlabel('date')

                plt.legend()
                fig = plt.gcf()
                fig.set_size_inches(16, 9)

                plt.savefig(
                    f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_verify_result/{j}_delta_top_10_to_50_temperature.png',
                    dpi=200, pad_inches=0.01)
                plt.close()

                out_record_temperature_csv_file = f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_{j}_temperature_verify.csv'
                with open(out_record_temperature_csv_file, mode='w+', newline='') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=['id', 'date',
                                                                  'center_mean_top_10%_to_50%_temperature',
                                                                  'periphery_mean_top_10%_to_50%_temperature',
                                                                  'delta_mean_top_10%_to_50%_temperature'
                                                                  ])
                    writer.writeheader()
                    for w in range(new_u.shape[0]):
                        row = {'date': new_u[w, 0],
                               'id': j,
                               'center_mean_top_10%_to_50%_temperature': new_u[w, 1],
                               'periphery_mean_top_10%_to_50%_temperature': new_u[w, 2],
                               'delta_mean_top_10%_to_50%_temperature': new_u[w, 3]
                               }
                        writer.writerow(row)
                break