import logging
import os
from typing import Sequence

import cv2
import imagesize
import numpy as np
import torch
from natsort import natsorted
from osgeo import gdal
from tqdm import tqdm

from config import DEVICE, NUM_CLASSES, input_path, original_image_path, output_grid_label_path, DETECTION_THRESHOLD, \
    support_file_list
from model import create_model
from util.labels import number2yolo, write_txt_label, latitude_longitude_2_image_coordinates, convert_boxes
from utils import read_polygon_shapefile, create_folder


def read_original_image_list(original_image_path, support_file_list):
    original_list = []
    original_image_name_list = [image_name for image_name in natsorted(os.listdir(original_image_path))
                       if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    pbar = tqdm(original_image_name_list)
    pbar.set_description(f'Loading original images')
    for original_image_name in pbar:
        geo_transform = None
        projection = None
        if os.path.splitext(original_image_name)[-1] in ['.tif', '.tiff']:
            tiff_file = gdal.Open(f'{original_image_path}/{original_image_name}')
            geo_transform = tiff_file.GetGeoTransform()
            projection = tiff_file.GetProjection()

        original_list.append(
            {'image_original_stem': os.path.splitext(original_image_name)[0],
             'image_original_name': original_image_name,
             'shape': imagesize.get(f'{original_image_path}/{original_image_name}'),
             'geo_transform': geo_transform,
             'projection': projection,
        })

    # logging.info(f'original_list = {original_list}')
    return original_list


def read_grid_image_list(grid_image_path, original_image_path, support_file_list):
    grid_list = []
    grid_image_name_list = [image_name for image_name in natsorted(os.listdir(grid_image_path))
                       if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]

    pbar = tqdm(grid_image_name_list)
    pbar.set_description(f'Loading grid images')
    for grid_image_name in pbar:
        stem, _ = os.path.splitext(grid_image_name)
        name_l = stem.split('_')
        # geo_transform = None
        # projection = None
        # if os.path.splitext(grid_image_name)[-1] in ['.tif', '.tiff']:
        #     with gdal.Open(f'{grid_image_path}/{grid_image_name}') as tiff_file:
        #         geo_transform = tiff_file.GetGeoTransform()
        #         projection = tiff_file.GetProjection()

        # original_image_name = grid_image_name.replace(f'_{name_l[-4]}_{name_l[-3]}_{name_l[-2]}_{name_l[-1]}', '')
        grid_list.append(
        {
        'grid_image_name': grid_image_name,
        'grid_image_stem': stem,
        'image_original_stem': stem.replace(f'_{name_l[-4]}_{name_l[-3]}_{name_l[-2]}_{name_l[-1]}', ''),
        #  'image_original_name':
        #      original_image_name,
        #  'original_shape': imagesize.get(f'{original_image_path}/{original_image_name}'),
         'shape': imagesize.get(f'{grid_image_path}/{grid_image_name}'),
         'x_start': int(name_l[-4]),
        #  'x_stop': int(name_l[-3]),
         'y_start': int(name_l[-2]),
        #  'y_stop': int(name_l[-1]),
        #  'geo_transform': geo_transform,
        #  'projection': projection,
         }
        )
    # logging.info(f'grid_list = {grid_list}')
    # image_original_stem_list = [image['image_original_stem'] for image in grid_list]
    # unique_image_original_stem_list = natsorted(list(set(image_original_stem_list)))
    # rearranged_grid_image_list = [[grid_image for grid_image in grid_list
    #                                if grid_image['image_original_stem'] == unique_image_original_stem]
    #                               for unique_image_original_stem in unique_image_original_stem_list]
    # return rearranged_grid_image_list
    return grid_list, grid_image_name_list


def generate_cluster(grid_image_list):
    image_original_stem_list = [image['image_original_stem'] for image in grid_image_list]
    unique_image_original_stem_list = natsorted(list(set(image_original_stem_list)))
    rearranged_grid_image_list = [[grid_image for grid_image in grid_image_list
                                   if grid_image['image_original_stem'] == unique_image_original_stem]
                                  for unique_image_original_stem in unique_image_original_stem_list]
    logging.info(len(rearranged_grid_image_list))
    return rearranged_grid_image_list, unique_image_original_stem_list


def build_mask(original_image_shape, geo_transform, input_shp_file_path=None):
    mask = np.zeros(original_image_shape, dtype=np.uint8)

    # input_shp_file_path = r'F:\zhongyan\ship_drilling_platform\wenlai\shapefile'
    # geo_coordinates = read_polygon_shapefile(input_shp_file_path)
    # image_coordinates = latitude_longitude_2_image_coordinates(geo_transform, geo_coordinates)
    # logging.info(image_coordinates)
    # pts = np.expand_dims(image_coordinates, axis=0)
    geo_coordinates_pts = read_polygon_shapefile(input_shp_file_path)
    image_coordinates = latitude_longitude_2_image_coordinates(geo_transform, geo_coordinates_pts)
    # logging.info(image_coordinates)
    image_pts = np.expand_dims(image_coordinates, axis=0)
    mask = cv2.fillPoly(mask, image_pts, color=(255, 255, 255))
    new_mask = np.asarray(mask, dtype=np.bool_)
    # pts = np.array([[[1200, 50], [1200, 1400], [50, 1400], [50, 3200], [1000, 3200], [1000, 4500],
    #                  [3700, 4500], [4650, 700], [2300, 700], [2300, 50]]],
    #                dtype=np.int32)
    #
    # logging.info(pts.shape)
    # mask = cv2.fillPoly(mask, pts, color=(255, 255, 255))
    # new_mask = np.asarray(mask, dtype=np.bool_)
    return new_mask


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


def load_and_preprocess_image(image_path, input_size=(1024, 1024), gap_size=64):
    preprocessed_image_list = []
    _, suffix = os.path.splitext(image_path)
    if suffix in ['.tif', '.tiff'] :
        with gdal.Open(image_path) as tiff_file:
            img = tiff_file.ReadAsArray().astype(np.float32)
            # img = cv2.cvtColor(tiff_file.ReadAsArray().astype(np.float32), cv2.COLOR_GRAY2RGB)
            # print(f'{img.shape = }')
            if img.ndim == 3:
                img = np.transpose(img, (1, 2, 0))
            else:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            if img.shape[-1] == 2:
                if img.ndim == 3:
                    # img = np.transpose(img, (1, 2, 0))
                    if img.shape[-1] == 2:
                        # warnings.warn('2 channel image to 3 channel')
                        new_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.float32)
                        new_img[:, :, 0] = img[:, :, 0]
                        new_img[:, :, 1] = img[:, :, 1]
                        new_img[:, :, 2] = img[:, :, 1]
                        img = new_img
                else:
                    new_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.float32)
                    new_img[:, :, 0] = img[:, :, 0]
                    new_img[:, :, 1] = img[:, :, 0]
                    new_img[:, :, 2] = img[:, :, 0]
                    img = new_img
    else:
        img = cv2.imread(image_path).astype(np.float32)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0
    if img.shape[1] != input_size[0] and img.shape[0] != input_size[1]:
        if img.shape[1] < input_size[0] and img.shape[0] < input_size[1]:
            img_new = np.zeros((input_size, 3), dtype=np.float32)
            img_new[0: img.shape[1], 0: img.shape[0], :] = img
            img = img_new

            preprocessed_image_list.append({
                'image': img,
                'x_start': 0,
                'y_start': 0,
            })
        else:
            # crop images
            windows = generate_grid(img.shape, input_size, gap_size)
            for window in windows:
                crop_img = copy_image(img, input_size, window, fill_value=(0, 0, 0))
                crop_img = np.transpose(crop_img, (2, 0, 1))
                crop_img = np.expand_dims(crop_img, 0)
                preprocessed_image_list.append({
                    'image': crop_img,
                    'x_start': window['x_start'],
                    'y_start': window['y_start'],
                })
    else:
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, 0)
        preprocessed_image_list.append({
            'image': img,
            'x_start': 0,
            'y_start': 0,
        })

    return preprocessed_image_list


def get_boxes_per_image(model, image_path, use_onnxruntime_inference):
    # image_info = get_image_info(image_name)
    preprocessed_image_list = load_and_preprocess_image(image_path, input_size=(1024, 1024))
    # logging.info(f'image_name = {image_name}')
    # logging.info(np.mean(img))
    full_annotations_list = []
    for preprocessed_image in preprocessed_image_list:
        annotations = torch.tensor([], device=DEVICE)
        if use_onnxruntime_inference:
            preds = model.run(None, {model.get_inputs()[0].name: preprocessed_image['image']})
            if preds[2].size != 0:
                scores = preds[2]
                indices_over = np.where(scores >= DETECTION_THRESHOLD)
                boxes_temp = convert_boxes(preds[0][indices_over],
                                           preprocessed_image['x_start'], preprocessed_image['y_start'])
                labels = preds[1][indices_over]
                scores = preds[2][indices_over]
                annotations = torch.as_tensor(
                    np.concatenate((np.expand_dims(labels, 1), boxes_temp, np.expand_dims(scores, 1)),
                                   axis=1), device=DEVICE)
        else:
            image = torch.as_tensor(preprocessed_image['image'], dtype=torch.float, device=DEVICE)
            with torch.no_grad():
                preds = model(image)
                preds_dict = preds[0]

            if preds_dict['scores'].numel() != 0:
                scores: torch.Tensor = preds_dict['scores']
                indices_over = torch.where(scores >= DETECTION_THRESHOLD)
                boxes_temp = convert_boxes(preds_dict['boxes'][indices_over],
                                           preprocessed_image['x_start'], preprocessed_image['y_start'])
                labels = preds_dict['labels'][indices_over]
                scores = preds_dict['scores'][indices_over]
                annotations = torch.as_tensor(
                    torch.cat((labels.unsqueeze(1), boxes_temp, scores.unsqueeze(1)), dim=1)
                    , device=DEVICE)
        full_annotations_list.append(annotations)
    full_annotations_tensor = torch.as_tensor(torch.cat(full_annotations_list, dim=0))
    return full_annotations_tensor


if __name__ == "__main__":

    use_onnxruntime_inference = False
    print('Use pytorch inference')
    model = create_model(num_classes=NUM_CLASSES)
    model.load_state_dict(
        torch.load(f'./run/2025-03-27_16-08-11/best_model.pth', map_location=DEVICE, weights_only=True))  # final#红海108-all  178-2个 140-1个
    model.eval()  # 确保模型处于评估模式
    model.to(DEVICE)

    grid_list, grid_image_name_list = read_grid_image_list(input_path, original_image_path, support_file_list)
    pbar = tqdm(grid_image_name_list)
    pbar.set_description(f'Predicting')
    for i, image_name in enumerate(pbar):
        annotations = get_boxes_per_image(model, f'{input_path}/{image_name}', use_onnxruntime_inference)
        annotations[..., 1:5] = number2yolo(grid_list[i]['shape'], annotations[..., 1:5])
        write_txt_label(f'{output_grid_label_path}/{grid_list[i]['grid_image_stem']}.txt', annotations)

