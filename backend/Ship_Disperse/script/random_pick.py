import logging
import os
import shutil

import numpy as np

from utils import create_folder


def move_to_new(src_path, target_path, names):
    for name in names:
        shutil.move(f'{src_path}/{name}', f'{target_path}/{name}')


if __name__ == "__main__":
    input_image_path = 'F:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp_1/images'
    input_label_path = 'F:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/temp_1/labels'
    output_path = 'F:/datasets/Official-SSDD-OPEN/BBox_RBox_PSeg_SSDD/voc_style/jpeg_grid_new/'
    output_train_image_path = f'{output_path}/images/train'
    output_train_label_path = f'{output_path}/labels/train'
    output_val_image_path = f'{output_path}/images/val'
    output_val_label_path = f'{output_path}/labels/val'

    split = ['train', 'val']
    for i in split:
        create_folder(f'{output_path}/images/{i}/')
        create_folder(f'{output_path}/labels/{i}/')

    image_names = os.listdir(input_image_path)
    label_names = os.listdir(input_label_path)
    logging.info(len(image_names))
    logging.info(len(label_names))
    total_number = len(image_names)
    ratio = 0.8
    train_number = int(total_number * ratio)
    val_number = int(total_number - train_number)
    logging.info(train_number)
    logging.info(val_number)

    train_pick = np.sort(np.random.choice(np.arange(0, total_number, dtype=np.intp), train_number, replace=False))
    logging.info(train_pick)
    logging.info(len(train_pick))
    train_image_names = np.array(image_names)[train_pick]
    logging.info(train_image_names)
    train_label_names = np.array(label_names)[train_pick]
    logging.info(train_image_names)
    move_to_new(input_image_path, output_train_image_path, train_image_names)
    move_to_new(input_label_path, output_train_label_path, train_label_names)

    val_image_names = os.listdir(input_image_path)
    val_label_names = os.listdir(input_label_path)

    move_to_new(input_image_path, output_val_image_path, val_image_names)
    move_to_new(input_label_path, output_val_label_path, val_label_names)