import logging

import torch
import cv2
import numpy as np
import os

from pycocotools.coco import COCO

from config import CLASSES, RESIZE_TO, DEVICE, train_image_dir, train_label_dir, support_file_list
from torch.utils.data import Dataset

from util.labels import yolo2number, read_txt_label
import albumentations as A

from utils import initial_logging_formatter


def arange_label(label_path, image_shape):
    bbox_yolo = read_txt_label(label_path)

    out_list = yolo2number(image_shape, bbox_yolo[..., 1:])
    out_list[..., 0][np.where(out_list[..., 0] < 0)] = 0
    out_list[..., 1][np.where(out_list[..., 1] < 0)] = 0
    out_list[..., 2][np.where(out_list[..., 2] > image_shape[1])] = image_shape[1]
    out_list[..., 3][np.where(out_list[..., 3] > image_shape[0])] = image_shape[0]
    # logging.info(out_list)
    return out_list


def augment():
    transform_styles = A.Compose([
        # A.RandomBrightnessContrast(brightness_limit=(-0.01, 0.01), contrast_limit=(-0.01, 0.01),
        #                            brightness_by_max=False, ensure_safe_range=True, p=0),
        A.RandomGamma(gamma_limit=(95, 105), p=0.5),
        A.Affine(translate_percent=(-0.2, 0.2), scale=(0.95, 1.05), rotate=(0, 0),
                 p=0.5),
        A.RandomRotate90(p=0.4),
    ], bbox_params=A.BboxParams(format='pascal_voc', min_visibility=0.1, label_fields=['class_labels']))
    return transform_styles


class PlatformDataset(Dataset):
    def __init__(self, dir_path, label_path, ann_path, height, width, classes, device, transforms=None, aug=True):
        self.transforms = transforms
        self.dir_path = dir_path
        self.height = height
        self.width = width
        self.device = torch.device('cpu')
        self.aug = aug
        self.class_names = 'ship'
        self.coco_api = COCO(ann_path)
        self.cat_ids = [1]
        # self.image_paths = glob.glob(f'{self.dir_path}*.jpg') #Grab all images in assigned path
        self.image_paths = [image_name for image_name in os.listdir(dir_path)
                            if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]
        self.all_images = sorted([p.replace('\\', '/').split('/')[-1] for p in self.image_paths])
        # self.all_images = sorted(self.all_images)

        self.class_dict = {}
        for i in range(1, len(classes)):
            self.class_dict[classes[i]] = i

        # Grab all annotations, store them in memory for quick access
        tmp = set(self.all_images)

        # with open('../data/annotations_ship_dataset_v0.csv', newline='') as f:
        self.annotations = {
            img: [arange_label(f'{label_path}/{os.path.splitext(img)[0]}.txt', (height, width)), 'ship'] for img in
            tmp}

        # with open(annotations_file_path, newline='') as f:
        #     reader = csv.reader(f)
        #     l = list(reader)
        #     self.annotations = {img: [annot[2:] for annot in l if annot[1] == img] for img in tmp}
        # logging.info(self.image_paths)
        # logging.info(self.annotations)

    def __len__(self):
        return len(self.all_images)

    def __getitem__(self, idx):
        # np.ascontiguousarray()
        # Reconstruct image path
        iname = self.all_images[idx]

        # logging.info(f'iname = {iname}')
        ipath = os.path.join(self.dir_path, iname)

        # Read the image
        img = cv2.imread(ipath)

        coords_l, cls = self.annotations[iname]
        boxes = coords_l
        # print(boxes)
        # boxes[:, 0][torch.where(boxes[:, 0] < 0)] = 0
        # boxes[:, 1][torch.where(boxes[:, 1] < 0)] = 0
        # boxes[:, 2][torch.where(boxes[:, 2] > img.shape[1])] = img.shape[1]
        # boxes[:, 3][torch.where(boxes[:, 3] > img.shape[0])] = img.shape[0]
        # print(boxes)
        labels = np.full(len(boxes), fill_value=self.class_dict[cls], dtype=np.intp)

        # Convert to appropriate channel order and set the datatype to float (it was previously uint)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        img = img.astype(np.float32)
        if self.aug:
            trans = augment()
            # logging.info(np.mean(img))
            transformed = trans(image=img, bboxes=boxes, class_labels=labels)
            img = transformed['image']
            boxes = transformed['bboxes']
            labels = transformed['class_labels']
            # logging.info(np.mean(img))

        # Resize and normalize image
        # img_resized = cv2.resize(img, (self.width, self.height))
        img_resized = np.transpose(img / 255.0, (2, 0, 1))

        # logging.info(f'boxes = {boxes}')

        # logging.info(labels)
        # Convert to tensors of appropriate data type
        boxes = torch.as_tensor(boxes, dtype=torch.float32, device=self.device)
        labels = torch.as_tensor(labels, dtype=torch.int64, device=self.device)
        area = ((boxes[..., 3] - boxes[..., 1]) * (boxes[..., 2] - boxes[..., 0]))
        iscrowd = torch.zeros((boxes.shape[0],), dtype=torch.int64, device=self.device)
        img_id = torch.tensor([idx], device=self.device)

        # Prepare the final dictionary
        target = dict()
        target['boxes'] = boxes
        target['labels'] = labels
        target['area'] = area
        target['iscrows'] = iscrowd
        target['image_id'] = img_id

        # Lastly, let's apply the transforms and return the transformed image along with the transformed target dictionary
        # if self.transforms:
        #     transf = self.transforms(image=img_resized, bboxes=target['boxes'], labels=labels)
        #     img_resized = transf['image']  # Grab transformed image
        #     target['boxes'] = torch.tensor(transf['bboxes'], device=self.device)  # Grab transformed bounding boxes

        img_tensor = torch.as_tensor(img_resized, device=self.device)
        return img_tensor, target


def visualize_sample(image, target):
    # logging.info(image.shape)
    boxes = target['boxes']
    labels = target['labels']

    for i in range(len(boxes)):
        box, label = boxes[i], CLASSES[labels[i]]
        cv2.rectangle(image, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 1)
        cv2.putText(image, label, (int(box[0]), int(box[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Image', image)
    cv2.waitKey(0)


if __name__ == '__main__':
    initial_logging_formatter()
    # Instantiate a dataset
    dataset = PlatformDataset(train_image_dir, train_label_dir, RESIZE_TO, RESIZE_TO, CLASSES, DEVICE, transforms=None,
                              aug=True)

    # self, dir_path, label_path, height, width, classes, device, transforms = None, aug = True
    # Function to visualize a single sample

    # Visualize a few samples to confirm data is loaded correctly
    NUM_SAMPLES_TO_VISUALIZE = 100
    random_pick_list = np.random.randint(0, len(dataset), NUM_SAMPLES_TO_VISUALIZE)
    for i in random_pick_list:
        image, target = dataset[i]
        image = image.cpu().numpy()
        image = np.transpose(image, (1, 2, 0))
        visualize_sample(image, target)
