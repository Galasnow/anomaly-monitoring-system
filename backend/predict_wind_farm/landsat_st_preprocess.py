import logging
import os
from datetime import datetime
from typing import Sequence

import cv2
import numpy as np
from matplotlib import pyplot as plt
from natsort import natsorted
from osgeo import gdal
from tqdm import tqdm

from predict import build_mask
from utils import create_folder

gdal.UseExceptions()

invalid_value = -999

def date_to_new_format(date: str):
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    return f'{year}/{month}/{day}'


def percent_average(temperature: np.ndarray, pick_range: Sequence[float]):
    values_valid = temperature[temperature != invalid_value]
    # logging.info(values_valid)
    values_valid_sorted = np.sort(values_valid)
    size1 = values_valid_sorted.size
    drop_min_number = max(int(size1 * pick_range[0]), 1)
    drop_max_number = max(int(size1 * (1 - pick_range[1])), 1)
    #  logging.info(size1, drop_min_number, drop_max_number)
    if size1 - drop_max_number - drop_min_number <= 0:
        return invalid_value
    middle_percent = values_valid_sorted[drop_min_number + 1: size1 - drop_max_number + 1]

    return np.mean(middle_percent)


def process_landsat_st(image, stem, output_path):
    # logging.info(image.shape)
    qa_image = image[1, :, :]
    ''' Clear with lows set / Dilated cloud over land / Mid conf cloud / Water with lows set / Dilated cloud over water / Mid conf cloud over water / '''
    # mask = (qa_image == 21824) | (qa_image == 21826) | (qa_image == 22080) | (qa_image == 21888) | (qa_image == 21890) | (qa_image == 22144)m
    mask = (qa_image == 21824) | (qa_image == 21888)
    # logging.info(f'sum of mask = {np.sum(mask)}')
    # logging.info(f'valid percent of pixels = {100 * np.sum(mask) / image.size}%')
    # logging.info(mask)
    st_image = image[0, :, :]

    out_file = np.where((293 <= st_image) & (st_image <= 61440) & mask, st_image * 0.00341802 + 149 - 273.15, invalid_value)
    out_file_name = f'{stem}_modify'
    # driver = gdal.GetDriverByName('GTiff')
    # # ########### ?
    # with driver.Create(f'{output_path}/{out_file_name}.tif', out_file.shape[1], out_file.shape[0], 1,
    #                    gdal.GDT_Float32) as out_tiff:
    #     # Set the geotransform and projection information for the out TIFF based on the input tif
    #     out_tiff.SetGeoTransform(geo_transform)
    #     out_tiff.SetProjection(projection)
    #     # Write the out array to the first band of the new TIFF
    #     out_tiff.GetRasterBand(1).WriteArray(out_file)
    #
    #     # Write the data to disk
    #     out_tiff.FlushCache()

    # cv2.imwrite(f'{output_path}/{out_file_name}.jpg', out_file, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

    return out_file


def generate_temperature_delta(path, item, polygon_shp, output_path):
    file = gdal.Open(f'{path}/{item}')
    image = file.ReadAsArray()
    geo_transform = file.GetGeoTransform()
    stem = os.path.splitext(item)[0]
    out_file = process_landsat_st(image, stem, output_path)

    polygon_mask = build_mask(image.shape[1:], geo_transform, polygon_shp)

    # platform_mask = polygon_mask & ((qa_image == 21824) | (qa_image == 21826) | (qa_image == 22080))
    # water_mask = polygon_mask & ((qa_image == 21888) | (qa_image == 21890) | (qa_image == 22144))
    # logging.info(np.sum(water_mask))
    # select_area = out_file[platform_mask]
    # big = five_percent_average(select_area)
    # select_area = out_file[water_mask]
    # small = five_percent_average(select_area)
    kernel = np.ones((3, 3), np.uint8)
    # logging.info(polygon_mask)
    # logging.info(polygon_mask.dtype)
    # logging.info(polygon_mask.astype(np.uint8))
    # logging.info(np.sum(polygon_mask))
    buffered_polygon_mask = (cv2.dilate(polygon_mask.astype(np.uint8), kernel, iterations=5)).astype(np.bool_)
    # logging.info(buffered_polygon_mask)
    # logging.info(np.sum(buffered_polygon_mask))
    platform_mask = np.logical_and(polygon_mask, buffered_polygon_mask)
    water_mask = np.logical_xor(polygon_mask, buffered_polygon_mask)
    select_area = out_file[platform_mask]
    big = percent_average(select_area, [0.5, 0.9])
    select_area = out_file[water_mask]
    small = percent_average(select_area, [0.5, 0.9])

    logging.info(f'big = {big}, small = {small}')

    if big != invalid_value and small != invalid_value:
        out_p = big - small
    else:
        out_p = invalid_value

    return out_p


if __name__ == "__main__":
    # a = np.array([1, 1, 1, 2])
    # b = np.array([2,3,4,1])
    # logging.info(np.expand_dims(a, axis=1))
    # logging.info(np.concatenate((np.expand_dims(a, axis=1), np.expand_dims(b, axis=1)), axis=1))
    # a = np.array([[1, 1, -999, 2],[-999, 2, -999, 1]])
    # logging.info(np.where(a==-999))
    # logging.info(np.delete(a, np.where(a==-999), axis=None))
    # logging.info(a[np.where(a!=-999)])

    path = 'F:/zhongyan/gee_download_wenlai/landsat/119057'
    output_path = f'{path}/output/'
    create_folder(output_path)
    # landsat_st_file_list = [file_name for file_name in os.listdir(path) if file_name.endswith('ST_B10.TIF')]
    time_range = (datetime(2017, 1 , 1), datetime(2025, 1, 1))
    landsat_st_file_list = [file_name for file_name in os.listdir(path) if file_name.startswith('LC') & file_name.endswith('tif')]
    time = natsorted([os.path.splitext(file_name)[0].split('_')[-1] for file_name in landsat_st_file_list])
    time_datetime_list = natsorted([datetime.strptime(date_to_new_format(date), '%Y/%m/%d') for date in time])
    insert_place_start = np.searchsorted(time_datetime_list, time_range[0], side='left')
    insert_place_end = np.searchsorted(time_datetime_list, time_range[1], side='right')
    # logging.info(insert_place_start, insert_place_end)

    time_filter = (insert_place_start, insert_place_end)
    landsat_st_file_list = landsat_st_file_list[insert_place_start: insert_place_end + 1]
    time = time[insert_place_start: insert_place_end + 1]
    time_datetime_list = time_datetime_list[insert_place_start: insert_place_end + 1]
    logging.info(time)
    logging.info(time_datetime_list)

    polygon_shp = r'F:\zhongyan\gee_download_wenlai\landsat\target_area\target_area.shp'

    temperature_list = np.zeros(len(landsat_st_file_list))
    for i, item in enumerate(tqdm(landsat_st_file_list)):
        temperature_list[i] = generate_temperature_delta(path, item, polygon_shp, output_path)
    # logging.info(f'temperature_list = {temperature_list}')

    invalid_index = (temperature_list == invalid_value)
    temperature_list_valid = np.delete(temperature_list, invalid_index)
    time_datetime_list_valid = np.delete(time_datetime_list, invalid_index)
    # logging.info(f'temperature_list_valid = {temperature_list_valid}')
    u = np.concatenate((np.expand_dims(time_datetime_list_valid, axis=1), np.expand_dims(temperature_list_valid, axis=1)), axis=1)
    # logging.info(u)
    new_u = np.array(sorted(u, key=lambda t: t[0]))

    logging.info(new_u)
    # plt.plot(time_datetime_list_valid, temperature_list_valid, linewidth=2.5, marker='o', label='temperature')
    plt.plot(new_u[..., 0], new_u[..., 1], linewidth=2, marker='o', label='temperature difference')
    plt.axhline(y=2, color='yellow', label='reference threshold line')
    plt.ylabel('Temperature difference / °C')
    plt.xlabel('date')
    plt.legend()
    plt.show()