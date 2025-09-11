import logging
import os
from typing import Sequence

import cv2
import numpy as np
# import torch
from osgeo import gdal

from util.image_io import export_image

gdal.UseExceptions()
from tqdm import tqdm

from config import support_file_list
from util.labels import yolo2number, number2yolo, read_txt_label, write_txt_label


def generate_new_geo_transform(window, original_geo_transform, offset: int):
    new_geo_transform = list(original_geo_transform)
    new_geo_transform[0] = new_geo_transform[0] + new_geo_transform[1] * float(window['x_start'] + offset)
    new_geo_transform[3] = new_geo_transform[3] + new_geo_transform[5] * float(window['y_start'] + offset)
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
                if image.ndim == 3:
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
    elif image.ndim == 3:
        if fill_value is None:
            out_image = image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop'], :]
        else:
            out_image = cv2.copyMakeBorder(
                image[window['y_start']:window['y_stop'], window['x_start']:window['x_stop'], :],
                0, y_fill_height, 0, x_fill_width,
                cv2.BORDER_CONSTANT, value=fill_value)
    else:
        raise RuntimeError("image's dimension is not 2 or 3 !")

    return out_image


def get_valid_label(bboxes_number, window, image_shape):
    if bboxes_number.ndim == 1:
        bboxes_number = np.expand_dims(bboxes_number, axis=1)
    out_bbox = []
    for item in bboxes_number:
        drop_out = False
        # if window['x_start'] <= item[1] and window['y_start'] <= item[2] and window['x_stop'] >= item[3] and window['y_stop'] >= item[4]:
        #     new_item = item.copy()
        #     new_item[1] -= window['x_start']
        #     new_item[2] -= window['y_start']
        #     new_item[3] -= window['x_start']
        #     new_item[4] -= window['y_start']
        #     out_bbox.append(new_item)
        # inside_flag = ((window['x_start'] <= item[1] and window['y_start'] <= item[2]) or
        #                (window['x_stop'] >= item[3] and window['y_start'] <= item[2]) or
        #                (window['x_stop'] >= item[3] and window['y_stop'] >= item[4]) or
        #                (window['x_start'] <= item[1] and window['y_stop'] >= item[4]))
        outside_flag = window['x_start'] > item[3] or window['y_start'] > item[4] or window['x_stop'] < item[1] or window['y_stop'] < item[2]
        # print(inside_flag)
        # print(outside_flag)
        if not outside_flag:
            new_item = item.copy()
            new_item[1] = np.max((0, item[1] - window['x_start']))
            new_item[2] = np.max((0, item[2] - window['y_start']))
            new_item[3] = np.min((image_shape[0], item[3] - window['x_start']))
            new_item[4] = np.min((image_shape[1], item[4] - window['y_start']))
            if (new_item[3] - new_item[1]) < 0.2 * (item[3] - item[1]) or (new_item[4] - new_item[2]) < 0.2 * (item[4] - item[2]):
                drop_out = True
                continue
            else:
                out_bbox.append(new_item)
    # logging.info(f'out_bbox = {out_bbox}')
    # print(f'out_bbox = {out_bbox}')
    return np.asarray(out_bbox)


def crop_image_by_grid(input_image_path: str, input_label_path: str, output_image_path: str, output_label_path: str,
                       crop_size: Sequence[int], gap_size: int, show=False, **kwargs):
    output_format = 'tif'
    fill_value = None
    for key, value in kwargs.items():
        if key == 'output_format':
            if value in support_file_list:
                output_format = value
            else:
                raise RuntimeError(f'"output_format" keyword argument must in {support_file_list}')
        elif key == 'fill_value':
            fill_value = value

    (image, file_name_stem, geo_transform, projection) = read_image(input_image_path)

    # print(image.shape)
    # logging.info(input_label_path)
    bbox_yolo = read_txt_label(input_label_path)
    # logging.info(bbox_yolo)
    bbox_number = bbox_yolo.copy()
    bbox_number[..., 1:5] = yolo2number([image.shape[1], image.shape[0]], bbox_yolo[..., 1:5])
    # logging.info(image.shape)
    # logging.info(bbox_number)
    # logging.info(new_bbox_number)
    # time.sleep(1)
    windows = generate_grid(image.shape, crop_size, gap_size)

    for window in windows:
        out_image = copy_image(image, crop_size, window, fill_value)
        out_label = get_valid_label(bbox_number, window, [out_image.shape[1], out_image.shape[0]])
        if len(out_label) != 0:
            out_label[..., 1:] = number2yolo(crop_size, out_label[..., 1:])
            # if len(out_label) != 0:
                # logging.info(out_label)
                # logging.info(file_name_stem)
            out_label_stem = f'{file_name_stem}_{window['x_start']}_{window['x_stop']}_{window['y_start']}_{window['y_stop']}'
            write_txt_label(f'{output_label_path}/{out_label_stem}.txt', out_label)
            new_geo_transform = generate_new_geo_transform(window, geo_transform, offset=0)
            export_image(out_image, output_image_path, file_name_stem, window, offset=0,
                         crop_size=crop_size, gap_size=gap_size, geo_transform=new_geo_transform, projection=projection, **kwargs)


def batch_crop_image_by_grid(input_image_path: str, input_label_path: str, *args, **kwargs):
    image_name_list = [image_name for image_name in os.listdir(input_image_path)
                       if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    for image_name in tqdm(image_name_list):
        image_stem, _ = os.path.splitext(image_name)
        crop_image_by_grid(f'{input_image_path}/{image_name}', f'{input_label_path}/{image_stem}.txt', *args, **kwargs)


def create_folder(path: str):
    existence = os.path.exists(path)
    if not existence:
        os.makedirs(path)


if __name__ == "__main__":
    # input_image_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/JPEGImages_1'
    # input_label_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/Annotations_yolo'
    # output_image_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp/images'
    # output_label_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp/labels'

    # input_image_path = r'H:\zhongyan\gee_download_weizhou\crop_jpg\temp'
    # input_label_path = r'H:\zhongyan\gee_download_weizhou\crop_jpg\labels'
    # output_image_path = r'H:\zhongyan\gee_download_weizhou\crop_jpg\temp_grid'
    # output_label_path = r'H:\zhongyan\gee_download_weizhou\crop_jpg\temp_grid_label'

    # input_image_path = r'H:\zhongyan\gee_download_wenlai\crop_1'
    # input_label_path = r'H:\zhongyan\gee_download_wenlai\labels'
    # output_image_path = r'H:\zhongyan\gee_download_wenlai\temp_grid'
    # output_label_path = r'H:\zhongyan\gee_download_wenlai\temp_grid_label'
    # output_format = 'jpg'

    # input_image_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp_images'
    # input_label_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp_labels'
    # output_image_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp\images'
    # output_label_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp\labels'
    # output_format = 'tif'

    # input_image_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\marked_images'
    # input_label_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp_labels'
    # output_image_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\grid_marked_images'
    # output_label_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\grid_marked_labels'
    # output_format = 'tif'

    # input_image_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\marked_images'
    # input_label_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp_labels'
    # output_image_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp\images'
    # output_label_path = r'H:\zhongyan\gee_download_weizhou\S1_modified\temp\labels'
    # output_format = 'tif'
    # crop_size = (256, 256)
    # gap_size = 128

    # input_image_path = r'H:\zhongyan\gee_download_weizhou_new\temp_images'
    # input_label_path = r'H:\zhongyan\gee_download_weizhou_new\temp_labels'
    # output_image_path = r'H:\zhongyan\gee_download_weizhou_new\temp\images'
    # output_label_path = r'H:\zhongyan\gee_download_weizhou_new\temp\labels'
    # output_format = 'tif'

    input_image_path = r'H:\zhongyan\wind_farm\2_channel_images'
    input_label_path = r'H:\zhongyan\wind_farm\marked_labels'
    output_image_path = r'H:\zhongyan\wind_farm\temp\images'
    output_label_path = r'H:\zhongyan\wind_farm\temp\labels'
    output_format = 'tif'

    crop_size = (1024, 1024)
    gap_size = 0

    if not os.path.isabs(input_image_path):
        current_path = os.path.abspath(__file__)
        input_image_path = os.path.join(current_path, input_image_path)
    if output_image_path is None:
        output_image_path = f'{input_image_path}/output'
    create_folder(output_image_path)
    create_folder(output_label_path)

    if os.path.isdir(input_image_path):
        # path
        batch_crop_image_by_grid(input_image_path, input_label_path, output_image_path, output_label_path, crop_size, gap_size,
                                 show=False, output_format=output_format, jpg_quality=100, fill_value=(0,0,0))
    elif os.path.isfile(input_image_path):
        crop_image_by_grid(input_image_path, input_label_path, output_image_path, output_label_path, crop_size, gap_size,
                           show=True, output_format=output_format, jpg_quality=100, fill_value=(0,0,0))

