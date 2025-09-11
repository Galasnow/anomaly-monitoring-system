import logging
import os
import time
from typing import Sequence

import cv2
import numpy as np
# import torch
from osgeo import gdal

from utils import create_folder

gdal.UseExceptions()
from tqdm import tqdm

from config import support_file_list


def generate_new_geo_transform(window, original_geo_transform, offset: int):
    new_geo_transform = list(original_geo_transform)
    new_geo_transform[0] = new_geo_transform[0] + new_geo_transform[1] * (window['x_start'] + offset)
    new_geo_transform[3] = new_geo_transform[3] + new_geo_transform[5] * (window['y_start'] + offset)
    return new_geo_transform


def generate_grid(image_shape: Sequence[int], crop_size: Sequence[int], gap_size: int):
    w = image_shape[1]
    h = image_shape[0]

    x_split = range(0, w, (crop_size[0] - gap_size))
    y_split = range(0, h, (crop_size[1] - gap_size))
    logging.debug(f'x_split = {x_split}')
    logging.debug(f'y_split = {y_split}')

    windows = []
    for x_start in x_split:
        x_stop = min(x_start + crop_size[0], w)
        for y_start in y_split:
            y_stop = min(y_start + crop_size[1], h)
            window = {'x_start': x_start,
                      'x_stop': x_stop,
                      'y_start': y_start,
                      'y_stop': y_stop
                      }
            windows.append(window)

    logging.debug(f'windows = {windows}')
    return windows


def read_image(input_path: str):
    stem, suffix = os.path.splitext(input_path)
    file_name_stem = stem.split('/')[-1]
    geo_transform = None
    projection = None
    match suffix:
        case '.jpg' | '.png':
            image = cv2.imread(input_path)
        case '.jp2':  # Sentinel-2
            image = cv2.imread(input_path, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
        case '.tif' | '.tiff':
            with gdal.Open(input_path) as tiff_file:
                geo_transform = tiff_file.GetGeoTransform()
                projection = tiff_file.GetProjection()
                logging.info(geo_transform)
                image = tiff_file.ReadAsArray()
                if image.ndim >= 3:
                    image = np.transpose(image, (1, 2, 0))
        case _:
            raise RuntimeError('Unknown file type!')
    return image, file_name_stem, geo_transform, projection


def copy_image(image, crop_size: Sequence[int], window, fill_value=None):
    crop_width = window['x_stop'] - window['x_start']
    crop_height = window['y_stop'] - window['y_start']
    x_fill_width = crop_size[0] - crop_width
    y_fill_height = crop_size[1] - crop_height
    if image.ndim == 2:
        if fill_value is None:
            out_image = image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop']]
        else:
            out_image = cv2.copyMakeBorder(
                image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop']],
                0, y_fill_height, 0, x_fill_width,
                cv2.BORDER_CONSTANT, value=fill_value)
            # out_image = cv2.copyMakeBorder(
            #     image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop']],
            #     0, y_fill_height, 0, x_fill_width,
            #     #cv2.BORDER_CONSTANT, value=fill_value)
            #     cv2.BORDER_REFLECT)
    elif image.ndim == 3:
        if fill_value is None:
            out_image = image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop'], :]
        else:
            out_image = cv2.copyMakeBorder(
                image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop'], :],
                0, y_fill_height, 0, x_fill_width,
                cv2.BORDER_CONSTANT, value=fill_value)
            # out_image = cv2.copyMakeBorder(
            #     image[:, window['y_start']:window['y_stop'], window['x_start']:window['x_stop']],
            #     0, y_fill_height, 0, x_fill_width,
            #     #cv2.BORDER_CONSTANT, value=fill_value)
            #     cv2.BORDER_REFLECT)
    else:
        raise RuntimeError("image's dimension is not 2 or 3 !")

    return out_image


def convert_np_dtype_to_gdal_type(dtype):
    match dtype:
        case 'uint8':
            gdal_type = gdal.GDT_Byte
        case 'int8':
            gdal_type = gdal.GDT_Int8
        case 'uint16':
            gdal_type = gdal.GDT_UInt16
        case 'int16':
            gdal_type = gdal.GDT_Int16
        case 'uint32':
            gdal_type = gdal.GDT_UInt32
        case 'int32':
            gdal_type = gdal.GDT_Int32
        case 'uint64':
            gdal_type = gdal.GDT_UInt64
        case 'int64':
            gdal_type = gdal.GDT_Int64
        case 'float32':
            gdal_type = gdal.GDT_Float32
        case 'float64':
            gdal_type = gdal.GDT_Float64
        case _:
            raise RuntimeError('Unknown numpy data type')
    return gdal_type


def export_image(out_image, output_path: str, file_name_stem: str, window, offset=0, **kwargs):
    out_image_stem = f'{file_name_stem}_{window['x_start']}_{window['x_stop']}_{window['y_start']}_{window['y_stop']}'
    output_format = 'tif'
    jpg_quality = 95
    jp2_compression = 950
    crop_size = None
    geo_transform = None
    projection = None
    for key, value in kwargs.items():
        if key == 'output_format':
            if value in ['jpg', 'png', 'jp2', 'tif']:
                output_format = value
            else:
                raise RuntimeError('"output_format" keyword argument must be "jpg", "png", "jp2" or "tif"')
        elif key == 'jpg_quality':
            if 0 < value <= 100:
                jpg_quality = value
            else:
                raise RuntimeError('"jpg_quality" keyword argument range from 1 to 100')
        elif key == 'jp2_compression':
            if 0 <= value <= 1000:
                jp2_compression = value
            else:
                raise RuntimeError('"jp2_compression" keyword argument range from 0 to 1000')
        elif key == 'crop_size':
            crop_size = value
        elif key == 'geo_transform':
            geo_transform = value
        elif key == 'projection':
            projection = value

    match output_format:
        case 'jpg':
            if out_image.ndim == 3 and out_image.shape[0] > 3:
                out_image = out_image[:, :, 0:3]
            cv2.imwrite(f'{output_path}/{out_image_stem}.jpg', out_image,
                        [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])
        case 'png':
            # TODO
            cv2.imwrite(f'{output_path}/{out_image_stem}.png', out_image)
        case 'jp2':
            # TODO
            cv2.imwrite(f'{output_path}/{out_image_stem}.jp2', out_image,
                        [int(cv2.IMWRITE_JPEG2000_COMPRESSION_X1000), jp2_compression])
        case 'tif':
            driver = gdal.GetDriverByName('GTiff')
            if out_image.ndim == 3:
                band_count = out_image.shape[-1]
            else:
                band_count = 1
            # Create a new GeoTIFF file to store the result
            out_gdal_type = convert_np_dtype_to_gdal_type(out_image.dtype)
            with driver.Create(f'{output_path}/{out_image_stem}.tif', crop_size[0], crop_size[1], band_count,
                               out_gdal_type) as out_tiff:
                # Set the geotransform and projection information for the out TIFF based on the input tif
                output_geo_transform = generate_new_geo_transform(window, geo_transform, offset)
                out_tiff.SetGeoTransform(output_geo_transform)
                out_tiff.SetProjection(projection)

                # Write the out array to the first band of the new TIFF
                if out_image.ndim == 3:
                    for i in range(out_image.shape[-1]):
                        out_tiff.GetRasterBand(i + 1).WriteArray(out_image[:, :, i])
                else:
                    out_tiff.GetRasterBand(1).WriteArray(out_image)

                # Write the data to disk
                out_tiff.FlushCache()
        case _:
            raise RuntimeError('Unknown file type!')


def crop_image_by_grid(input_image_path: str, output_image_path: str,
                       crop_size: Sequence[int], gap_size: int, **kwargs):
    swap_rb_channel = False
    output_format = 'tif'
    fill_value = None
    for key, value in kwargs.items():
        if key == 'swap_rb_channel':
            if isinstance(value, bool):
                swap_rb_channel = value
            else:
                raise RuntimeError('"swap_rb_channel" keyword argument must be True or False')
        elif key == 'output_format':
            if value in support_file_list:
                output_format = value
            else:
                raise RuntimeError(f'"output_format" keyword argument must in {support_file_list}')
        elif key == 'fill_value':
            fill_value = value

    (image, file_name_stem, geo_transform, projection) = read_image(input_image_path)
    if swap_rb_channel:
        image[[0, 2], :, :] = image[[2, 0], :, :]

    windows = generate_grid(image.shape, crop_size, gap_size)

    for window in windows:
        out_image = copy_image(image, crop_size, window, fill_value)
        export_image(out_image, output_image_path, file_name_stem, window, offset=0,
                     crop_size=crop_size, gap_size=gap_size, geo_transform=geo_transform, projection=projection,
                     **kwargs)


def batch_crop_image_by_grid(input_image_path: str, output_image_path: str, *args, **kwargs):
    image_name_list = [image_name for image_name in os.listdir(input_image_path)
                       if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    pbar = tqdm(image_name_list)
    pbar.set_description(f'Cropping images')
    for image_name in pbar:
        image_stem, _ = os.path.splitext(image_name)
        crop_image_by_grid(f'{input_image_path}/{image_name}', output_image_path, *args, **kwargs)


if __name__ == "__main__":
    input_image_path = r'D:\zhongyan\test_area\original_images'
    output_image_path = r'D:\zhongyan\test_area\grid_images'
    output_format = 'tif'

    crop_size = (1024, 1024)
    gap_size = 64

    if not os.path.isabs(input_image_path):
        current_path = os.path.abspath(__file__)
        input_image_path = os.path.join(current_path, input_image_path)
    if output_image_path is None:
        output_image_path = f'{input_image_path}/output'
    create_folder(output_image_path)

    if os.path.isdir(input_image_path):
        # path
        batch_crop_image_by_grid(input_image_path, output_image_path, crop_size, gap_size, output_format=output_format,
                                 jpg_quality=100, fill_value=(0, 0, 0))
    elif os.path.isfile(input_image_path):
        crop_image_by_grid(input_image_path, output_image_path, crop_size, gap_size,
                           output_format=output_format, jpg_quality=100, fill_value=(0, 0, 0))
