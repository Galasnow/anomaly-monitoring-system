import logging
import os
import random

import numpy as np
import cv2
import torch
from natsort import natsorted
from tqdm import tqdm

from utils import create_folder

support_file_list = ['jpg', 'png', 'jp2', 'tif', 'tiff']

def read_txt_label_1(path, col=5):
    with open(path, 'r') as label_file:
        content = np.array(label_file.read().split()).reshape(-1, col).astype(float)
        content[..., 0].astype(int)
    return content


def write_txt_label_new(output_label_path, label):
    is_torch = isinstance(label, torch.Tensor)
    if is_torch:
        label = label.cpu().numpy()
    with open(output_label_path, 'w') as label_file:
        if np.array(label).ndim == 1:
            np.expand_dims(label, axis=1)
        for lb in label:
            formatted_coords = [f"{coord:.6g}" for coord in lb[1:]]
            label_file.write(f"{int(lb[0])} {' '.join(formatted_coords)}\n")


def convert_label(original_label, offset_x, offset_y, input_size, output_size):
    ratio = input_size / output_size
    original_label[..., -2:] *= ratio
    original_label[..., 1] = (original_label[..., 1] * input_size + offset_x) / output_size
    original_label[..., 2] = (original_label[..., 2] * input_size + offset_y) / output_size
    return original_label


if __name__ == "__main__":
    concatenate_size = (4, 4)
    concatenate_number = concatenate_size[0] * concatenate_size[1]
    input_size = (256, 256)
    output_size = (input_size[0] * concatenate_size[0], input_size[1] * concatenate_size[1])
    input_image_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp/images'
    input_label_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp/labels'
    output_image_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp_1/images'
    output_label_path = 'D:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp_1/labels'

    create_folder(output_image_path)
    create_folder(output_label_path)

    image_name_list = [image_name for image_name in natsorted(os.listdir(input_image_path))
                       if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    label_name_list = [label_name for label_name in natsorted(os.listdir(input_label_path))]
    # logging.info(image_name_list[10])
    # logging.info(label_name_list[10])
    # logging.info(image_name_list)
    length = len(image_name_list)
    logging.info(length)

    ids = list(range(0, length))
    random.shuffle(ids)
    new_length = length // concatenate_number
    drop_out = length - concatenate_number * new_length
    if drop_out != 0:
        del ids[-drop_out:]
    # logging.info(ids)
    concatenate_array = np.reshape(ids, (new_length, concatenate_number))
    # logging.info(concatenate_array)
    for i, concatenate_item in enumerate(tqdm(concatenate_array)):
        label_all = []
        result = np.zeros((output_size[0], output_size[1], 3))
        for j in range(concatenate_size[0]):
            for k in range(concatenate_size[1]):
                # logging.info(f'{input_image_path}/{image_name_list[concatenate_item[j * concatenate_size[1] + k]]}')
                # logging.info(f'{input_label_path}/{label_name_list[concatenate_item[j * concatenate_size[1] + k]]}')
                image = cv2.imread(f'{input_image_path}/{image_name_list[concatenate_item[j * concatenate_size[1] + k]]}')
                label = read_txt_label_1(f'{input_label_path}/{label_name_list[concatenate_item[j * concatenate_size[1] + k]]}')
                stem, _ = os.path.splitext(f'{image_name_list[concatenate_item[j * concatenate_size[1] + k]]}')
                pre_anno = stem.split('_')[0]
                convert_label(label, input_size[1] * k, input_size[0] * j, input_size[0], output_size[0])
                label_all.append(label)
                result[input_size[1] * j: input_size[1] * (j + 1), input_size[1] * k: input_size[1] * (k + 1), :] = image
        # logging.info(label_all)
        label_all = np.concatenate(label_all)
        # logging.info(label_all)
        cv2.imwrite(f'{output_image_path}/{i}.jpg', result)
        write_txt_label_new(f'{output_label_path}/{i}.txt', label_all)
