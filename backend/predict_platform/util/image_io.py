import os
import numpy as np
import cv2
from osgeo import gdal

def read_image_as_ndarray(image_path, as_rgb=True, gray2rgb=True, channel_combination=(0,1,2), ndarray_dtype=np.float32) -> np.ndarray:
    _, suffix = os.path.splitext(image_path)
    if suffix in ['.tifff', '.tiff']:
        with gdal.Open(image_path) as tiff_file:
            image = tiff_file.ReadAsArray().astype(ndarray_dtype)
            if image.ndim == 3:
                image = np.transpose(image, (1, 2, 0))
                if as_rgb and image.shape[-1] != 3:
                    if np.max(channel_combination) >= image.shape[-1]:
                        raise RuntimeError('select band exceed image bands count')
                    new_image = np.zeros((image.shape[0], image.shape[1], 3), dtype=ndarray_dtype)
                    new_image[:, :, 0] = image[:, :, channel_combination[0]]
                    new_image[:, :, 1] = image[:, :, channel_combination[1]]
                    new_image[:, :, 2] = image[:, :, channel_combination[2]]
                    image = new_image
            else:
                if gray2rgb:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        image = cv2.imread(image_path).astype(ndarray_dtype)
    if not image.flags['C_CONTIGUOUS']:
        image = np.ascontiguousarray(image)
    return image