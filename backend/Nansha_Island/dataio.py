# -*- coding: utf-8 -*-

import torchvision.transforms as transforms
import torch.utils as utils
from skimage import io

import matplotlib.pyplot as plt
import numpy as np
import os
import cv2
from PIL import Image

#随机裁剪
class RandomCrop(object):
    """Crop randomly the image in a sample
    Args:
        output_size (tuple or int): Desired ouput size, if int, square crop
        is made.
    """
    def __init__(self, output_size):
        assert isinstance(output_size, (int, tuple))
        if isinstance(output_size, int):
            self.output_size = (output_size, output_size)
        else:
            assert len(output_size) == 2
            self.output_size = output_size

    def __call__(self, sample):
        image = sample['image']
        h, w = image.shape[1:3]
        new_h, new_w = self.output_size

        top = np.random.randint(0, h - new_h)
        left = np.random.randint(0, w - new_w)

        image = image[:, top:top + new_h, left:left + new_w]
        if 'label' in sample:
            label = sample['label']
            label = label[:, top:top + new_h, left:left + new_w]
            return {'image': image, 'label': label}
        return {'image': image}


class BuildingDataset(utils.data.Dataset):
    def __init__(self, root_dir, transform=None, mode='train'):
        self.root_dir = root_dir
        self.transform = transform
        self.mode = mode

        self.train_data = []
        files = os.listdir(os.path.join(self.root_dir, "image/"))
        for item in files:
            if item.endswith(".tif"):
                self.train_data.append(item.split(".tif")[0])

    def __len__(self):
        return len(self.train_data)

    def __getitem__(self, index):
        prefix = self.root_dir
        img_name = prefix + "image/" + self.train_data[index] + ".tif"
        image = io.imread(img_name)
        image = image.astype(np.float32) / (255 * 0.5) - 1

        sample = {'image': image.transpose(2, 0, 1)}

        if self.mode == 'train':
            label_name = prefix + "label/" + self.train_data[index] + ".tif"
            img = cv2.imread(label_name, 0)
            label = img.astype(np.float32) / 255.0
            label = label.reshape(label.shape[0], label.shape[1], 1)
            sample['label'] = label.transpose(2, 0, 1)

        if self.transform:
            sample = self.transform(sample)

        return sample
