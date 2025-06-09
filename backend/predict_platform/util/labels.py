import logging
import warnings
from typing import Sequence
# from pyproj import Transformer
import numpy as np
import torch
from tqdm import tqdm


# from pathlib import Path
# from ultralytics.util.ops import xywh2xyxy, xyxy2xywh


# def read_txt_label(image_name, col=5):
#     with open(f'{image_name}.txt', 'r') as label_file:
#         content = np.array(label_file.read().split()).reshape(-1, col).astype(float)
#         content[..., 0].astype(int)
#         content[..., -1].astype(int)
#     return content


def read_txt_label(path):
    if not path.endswith(".txt"):
        path = f'{path}.txt'
        warnings.warn('output path is not end with ".txt". Auto add ".txt" at end of path')
    with open(path, 'r') as label_file:
        content = [x.split() for x in label_file.read().strip().splitlines() if len(x)]
        content = np.asarray(content, dtype=np.float32)
    return content


def write_txt_label(path, label):
    is_torch = isinstance(label, torch.Tensor)
    if is_torch:
        label = label.cpu().numpy()
    if not path.endswith(".txt"):
        path = f'{path}.txt'
        warnings.warn('output path is not end with ".txt". Auto add ".txt" at end of path')
    with open(path, 'w') as label_file:
        if np.array(label).ndim == 1:
            np.expand_dims(label, axis=1)
        for lb in label:
            formatted_coords = [f"{coord:.6g}" for coord in lb[1:]]
            label_file.write(f"{int(lb[0])} {' '.join(formatted_coords)}\n")


def arrange_label(label_path, image_shape):
    bbox = read_txt_label(label_path)
    bbox[..., 1:5] = yolo2number(image_shape, bbox[..., 1:5])
    # logging.info(bbox)
    return bbox


def remove_invalid_annotations(label, image_shape):
    is_torch = isinstance(label, torch.Tensor)
    invalid_annotation_args = []
    for i, lb in enumerate(label):
        if lb[1] < 0 or lb[2] < 0 or lb[3] > image_shape[0] or lb[4] > image_shape[1]:
            invalid_annotation_args.append(i)
    if is_torch:
        index = torch.tensor(np.delete(np.arange(label.size(0)), invalid_annotation_args), dtype=torch.long,
                             device=label.device)
        label = label[index]
    else:
        label = np.delete(label, invalid_annotation_args, axis=0)
    return label


def remove_invalid_tensor_by_mask(tensors: torch.Tensor, mask: np.ndarray):
    invalid_tensor_args = []
    # image_range = np.zeros_like(mask, dtype=np.bool_)
    for i, tensor in enumerate(tensors):
        rectangle_range_detect = np.zeros_like(mask, dtype=np.bool_)
        x1 = int(tensor[1])
        y1 = int(tensor[2])
        x2 = int(tensor[3])
        y2 = int(tensor[4])
        # rectangle_range_detect = image_range.copy()
        rectangle_range_detect[y1:y2, x1:x2] = True
        if np.any(np.logical_xor(np.logical_and(rectangle_range_detect, mask), rectangle_range_detect)):
            invalid_tensor_args.append(i)

    if invalid_tensor_args:
        index = torch.as_tensor(np.delete(np.arange(tensors.size(0)), invalid_tensor_args), dtype=torch.int,
                             device=tensors.device)
        tensors = tensors[index]
    # tensors = np.delete(tensors, invalid_tensor_args)
    return tensors


def yolo2number(image_shape: Sequence[int], box: torch.Tensor | np.ndarray):
    """
    image_shape: (w, h)
    box: (center_x, center_y, w, h)
    """
    is_torch = isinstance(box, torch.Tensor)
    if is_torch:
        if box.numel() == 0:
            return box
    else:
        if box.shape[0] == 0:
            return box
    box_number = box.clone().cpu().numpy() if is_torch else box
    w = box[..., 2] * float(image_shape[0])
    h = box[..., 3] * float(image_shape[1])
    center_x = box[..., 0] * float(image_shape[0])
    center_y = box[..., 1] * float(image_shape[1])

    box_number[..., 0] = center_x - w / 2
    box_number[..., 1] = center_y - h / 2
    box_number[..., 2] = center_x + w / 2
    box_number[..., 3] = center_y + h / 2
    return torch.as_tensor(box_number, device=box.device, dtype=torch.float32) if is_torch else np.asarray(box_number)


def number2yolo(image_shape: Sequence[int], box_number: torch.Tensor | np.ndarray):
    """
    image_shape: (w, h)
    box_number: (xmin, ymin, xmax, ymax)
    """
    is_torch = isinstance(box_number, torch.Tensor)
    if is_torch:
        if box_number.numel() == 0:
            return box_number
    else:
        if box_number.shape[0] == 0:
            return box_number
    box = box_number.clone().cpu().numpy() if is_torch else box_number

    center_x = (box[..., 2] + box[..., 0]) / float(image_shape[0] * 2)
    center_y = (box[..., 3] + box[..., 1]) / float(image_shape[1] * 2)
    w = (box[..., 2] - box[..., 0]) / float(image_shape[0])
    h = (box[..., 3] - box[..., 1]) / float(image_shape[1])

    box = np.asarray(box, dtype=np.float32)
    box[..., 0] = center_x
    box[..., 1] = center_y
    box[..., 2] = w
    box[..., 3] = h
    return torch.as_tensor(box, device=box_number.device, dtype=torch.float32) if is_torch else np.asarray(box)


def convert_boxes(boxes, x_offset: int, y_offset: int):
    boxes[..., 0] += x_offset
    boxes[..., 1] += y_offset
    boxes[..., 2] += x_offset
    boxes[..., 3] += y_offset
    return boxes


def get_latitude_longitude(geo_transform, image_coordinates):
    ex_flag = False
    if image_coordinates.ndim == 1:
        ex_flag = True
        image_coordinates = np.expand_dims(image_coordinates, axis=0)
    geo_coordinates = image_coordinates.copy()
    for i, item in enumerate(image_coordinates):
        geo_transform_list = list(geo_transform)
        new_image_coordinates_x = geo_transform_list[0] + geo_transform_list[1] * int(item[0])
        new_image_coordinates_y = geo_transform_list[3] + geo_transform_list[5] * int(item[1])

        #transformer = Transformer.from_crs("EPSG:32649", 'EPSG:4326')
        #geo_coordinate = transformer.transform(new_image_coordinates_x,  new_image_coordinates_y)
        #geo_coordinate = (new_image_coordinates_x, new_image_coordinates_y)
        # logging.info(geo_coordinate)
        # geo_coordinates[i, 1:] = np.flip(geo_coordinate)
        geo_coordinates[i, :] = (new_image_coordinates_x, new_image_coordinates_y)
    if ex_flag:
        geo_coordinates = np.squeeze(geo_coordinates, axis=0)
    geo_coordinates.astype(np.float64)
    return geo_coordinates


def image_coordinates_2_latitude_longitude(geo_transforms, image_coordinates):
    ex_flag = False
    image_coordinates = np.asarray(image_coordinates)
    geo_transforms = np.asarray(geo_transforms)
    if image_coordinates.ndim == 1:
        ex_flag = True
        image_coordinates = np.expand_dims(image_coordinates, axis=0)
    if geo_transforms.ndim == 1:
        geo_transforms = np.expand_dims(geo_transforms, axis=0)
    geo_coordinates = np.zeros_like(image_coordinates, dtype=np.float64)
    for i, item in enumerate(image_coordinates):
        geo_transform = geo_transforms[i]
        new_geo_coordinates_x = geo_transform[0] + geo_transform[1] * float(item[0] + 0.5)
        new_geo_coordinates_y = geo_transform[3] + geo_transform[5] * float(item[1] + 0.5)

        #transformer = Transformer.from_crs("EPSG:32649", 'EPSG:4326')
        #geo_coordinate = transformer.transform(new_image_coordinates_x,  new_image_coordinates_y)
        #geo_coordinate = (new_image_coordinates_x, new_image_coordinates_y)
        # logging.info(geo_coordinate)
        # geo_coordinates[i, 1:] = np.flip(geo_coordinate)
        geo_coordinates[i, :] = (new_geo_coordinates_x, new_geo_coordinates_y)
    if ex_flag:
        geo_coordinates = np.squeeze(geo_coordinates, axis=0)
    return geo_coordinates


def latitude_longitude_2_image_coordinates(geo_transform, geo_coordinates, to_int=True):
    # logging.info(geo_coordinates)
    # logging.info(geo_coordinates.ndim)
    ex_flag = False
    if geo_coordinates.ndim == 1:
        ex_flag = True
        geo_coordinates = np.expand_dims(geo_coordinates, axis=0)
    # logging.info(geo_coordinates)
    # image_coordinates = geo_coordinates.astype(np.intp)
    if to_int:
        dtype=np.intp
    else:
        dtype=np.float64
    image_coordinates = np.zeros_like(geo_coordinates, dtype=dtype)
    for i, item in enumerate(geo_coordinates):
        # logging.info(geo_transform)
        # logging.info(item)
        if item[0] >= geo_transform[0] and item[1] <= geo_transform[3]:
            image_coordinates_x = (item[0] - geo_transform[0]) / geo_transform[1] - 0.5
            image_coordinates_y = (item[1] - geo_transform[3]) / geo_transform[5] - 0.5
        else:
            image_coordinates_x = -999
            image_coordinates_y = -999
            if item[0] < geo_transform[0]:
                warnings.warn(f'{item[0]} is smaller than left latitude {geo_transform[0]}')
            elif item[1] > geo_transform[3]:
                warnings.warn(f'{item[1]} is bigger than top longitude {geo_transform[3]}')

        # logging.info(image_coordinates_x, image_coordinates_y)
        if to_int:
            image_coordinates_x = round(image_coordinates_x)
            image_coordinates_y = round(image_coordinates_y)
        image_coordinates[i, :] = (image_coordinates_x, image_coordinates_y)
    # logging.info(f"center's x y = {center_x} {center_y}")
    if ex_flag:
        image_coordinates = np.squeeze(image_coordinates, axis=0)
    return image_coordinates


if __name__ == "__main__":
    path = 'P0000__1024__1024___1536.txt'
    content = read_txt_label('P0000__1024__1024___1536')
    # if isinstance(path, str) and Path(path).suffix == ".txt":  # *.txt file with img/vid/dir on each line
    #     parent = Path(path).parent
    #     path = Path(path).read_text().splitlines()  # list of sources

    out_path = 'test_out'
    write_txt_label(out_path, [1, 0.1213124, 0.11412421, 0.1134124, 0.11314124])

    test_label_1 = np.array([1, 0.1, 0.1, 0.4, 0.4])
    test_label_2 = np.array([[1, 0.1, 0.1, 0.4, 0.4], [2, 0.2, 0.3, 0.6, 0.9]])
    logging.info('?',test_label_1[..., 1:])
    out = yolo2number([100, 100], test_label_1[..., 1:])
    logging.info(out)
    out = yolo2number([100, 100], test_label_2[..., 1:])
    logging.info(out)
