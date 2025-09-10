import os

import cv2
from natsort import natsorted

from config import support_file_list
from util.labels import *
from modify_type import draw_box_on_image, EXPANSION_FACTOR

def draw_rectangle(image, box, color=(0,255,0)):

    return


if __name__ == "__main__":
    # train_image_dir = r'./datasets/images/train'
    # train_label_dir = r'./datasets/labels/train'
    # train_image_dir = r'F:\zhongyan\gee_download_weizhou\crop_jpg\temp_grid'
    # train_label_dir = r'F:\zhongyan\gee_download_weizhou\crop_jpg\temp_grid_label'
    # train_image_dir = r'F:\zhongyan\gee_download_wenlai\temp_grid'
    # train_label_dir = r'F:\zhongyan\gee_download_wenlai\temp_grid_label'
    train_image_dir = r'D:\datasets\Official-SSDD-OPEN\BBox_RBox_PSeg_SSDD\voc_style\jpeg_grid_new\temp_1\images'
    train_label_dir = r'D:\datasets\Official-SSDD-OPEN\BBox_RBox_PSeg_SSDD\voc_style\jpeg_grid_new\temp_1\labels'
    logging.info(f'Loading images')
    image_name_list = [image_name for image_name in natsorted(os.listdir(train_image_dir))
                            if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
    for image_name in image_name_list:
        logging.info(image_name)
        image = cv2.imread(f'{train_image_dir}/{image_name}')
        stem, _ = os.path.splitext(image_name)

        label = read_txt_label(f'{train_label_dir}/{stem}.txt')
        logging.info(image.shape)
        label_number = yolo2number(image.shape[0:2], label[..., 1:])
        # logging.info(label_number)
        ids=[1]
        draw_box_on_image(image, label_number, ids, expansion_factor=EXPANSION_FACTOR)

        cv2.namedWindow('show')
        cv2.imshow('show', image)
        cv2.waitKey(0)