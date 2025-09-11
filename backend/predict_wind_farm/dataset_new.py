import os

import cv2
import numpy as np
import torch
from osgeo import gdal
from pycocotools.coco import COCO
from torch.utils.data import Dataset
import albumentations as A

from config import support_file_list
from util.image_io import read_image_as_ndarray


def augment():
    transform_styles = A.Compose([
        # A.RandomBrightnessContrast(brightness_limit=(-0.01, 0.01), contrast_limit=(-0.01, 0.01),
        #                            brightness_by_max=False, ensure_safe_range=True, p=0),
        A.RandomGamma(gamma_limit=(95, 105), p=0.5),
        A.ElasticTransform(alpha=10, sigma=10, p=0.5),
        A.GridElasticDeform(num_grid_xy=(2, 2), magnitude=1, p=0.5),
        A.Affine(scale=(0.95, 1.05), translate_percent=(-0.5, 0.5), rotate=(0, 0), keep_ratio=True, fill=0,
                 p=0.5),
        A.RandomRotate90(p=0.4),
    ], bbox_params=A.BboxParams(format='pascal_voc', min_visibility=0.1, label_fields=['class_labels']))
    return transform_styles


def check_bbox(xmin, ymin, xmax, ymax, image_shape):
    """
    xmin, ymin, xmax, ymax,
    [h, w]
    """
    if xmin >= 0 and ymin >= 0 and xmax <= image_shape[1] and ymax <= image_shape[0] and xmax > xmin and ymax > ymin:
        return True
    else:
        return False


class CocoDetection(Dataset):
    def __init__(self, root, annotation, transforms=False):
        self.root = root
        self.transforms = transforms
        self.coco = COCO(annotation)
        self.ids = list(sorted(self.coco.imgs.keys()))
        self.image_names = sorted([image_name for image_name in os.listdir(self.root)
                            if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list])
        # print(self.image_names)

    def __getitem__(self, index):
        coco = self.coco
        img_id = self.ids[index]
        ann_ids = coco.getAnnIds(imgIds=img_id)
        annotations = coco.loadAnns(ann_ids)

        #  path = coco.loadImgs(img_id)[0]['file_name']
        path = f'{self.root}/{self.image_names[index]}'
        # print(path)
        # img = cv2.imread(path).astype(np.float32)

        img = read_image_as_ndarray(path, channel_combination=(0,1,1))

        boxes = []
        labels = []
        areas = []
        iscrowd = []
        # print(annotations)
        for ann in annotations:
            xmin = ann['bbox'][0]
            ymin = ann['bbox'][1]
            xmax = xmin + ann['bbox'][2]
            ymax = ymin + ann['bbox'][3]
            if check_bbox(xmin, ymin, xmax, ymax, img.shape):
                boxes.append([xmin, ymin, xmax, ymax])
                labels.append(ann['category_id'])
                # areas.append(ann['area'])
                iscrowd.append(ann['iscrowd'])
            else:
                continue
        if self.transforms:
            trans = augment()
            # logging.info(np.mean(img))
            transformed = trans(image=img, bboxes=boxes, class_labels=labels)
            if len(transformed['bboxes']) != 0:
                img = transformed['image']
                boxes = transformed['bboxes']
                labels = transformed['class_labels']

        img = np.transpose(img / 255.0, (2, 0, 1))
        img = torch.as_tensor(img, dtype=torch.float32)

        if len(boxes) != 0:
            boxes = torch.as_tensor(boxes, dtype=torch.float32)
            labels = torch.as_tensor(labels, dtype=torch.int64)
            areas = ((boxes[..., 3] - boxes[..., 1]) * (boxes[..., 2] - boxes[..., 0]))
            iscrowd = torch.as_tensor(iscrowd, dtype=torch.int64)
            image_id = torch.tensor([img_id], dtype=torch.int64)
            target = {"boxes": boxes, "labels": labels, "image_id": image_id, "area": areas, "iscrowd": iscrowd}
        else:
            # boxes = torch.zeros((0, 4), dtype=torch.float32),
            # labels = torch.zeros(0, dtype=torch.int64),
            # areas = torch.zeros(0, dtype=torch.float32),
            # iscrowd = torch.zeros(0, dtype=torch.int64),
            # image_id = torch.tensor([-1], dtype=torch.int64),  # 使用-1表示负样本
            target = {
                "boxes": torch.zeros((0, 4), dtype=torch.float32),
                "labels": torch.zeros(0, dtype=torch.int64),
                "image_id": torch.tensor([-1]),  # 使用-1表示负样本
                "area": torch.zeros(0, dtype=torch.float32),
                "iscrowd": torch.zeros(0, dtype=torch.int64)
            }
        # target = {"boxes": boxes, "labels": labels, "image_id": image_id, "area": areas, "iscrowd": iscrowd}
        return img, target

    def __len__(self):
        return len(self.ids)
