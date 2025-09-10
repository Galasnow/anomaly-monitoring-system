import csv
import logging
import os
import re
import time
import datetime
import imagesize
from typing import Callable
import numpy as np
import scipy
from natsort import natsorted
from numpy.ma.extras import average

from util.labels import yolo2number, image_coordinates_2_latitude_longitude
from osgeo import ogr, osr, gdal

gdal.UseExceptions()

import albumentations as A
from albumentations.pytorch import ToTensorV2


def initial_logging_formatter():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # 设置打印级别
    formatter = logging.Formatter('%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s')

    # 设置屏幕打印的格式
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)


class Averager:

    def __init__(self):
        self.total = 0
        self.count = 0

    def send(self, val):
        self.total += val
        self.count += 1

    def value(self):
        if self.count == 0:
            return 0
        return self.total / self.count

    def reset(self):
        self.total = 0
        self.count = 0


def collate_fn(batch):
    return tuple(zip(*batch))  # The'*' operator allows us to accept an arbitrary number of arguments


def get_train_transform():
    return A.Compose([
        A.Flip(p=0.5),  # Flip with a probability of 50%
        A.RandomRotate90(p=0.5),
        A.MotionBlur(p=0.2),
        A.MedianBlur(blur_limit=3, p=0.1),  # blur_limit is the maximum kernel/aperature size
        A.Blur(blur_limit=3, p=0.1),
        ToTensorV2(p=1.0)  # Transform to Tensor
    ], bbox_params={
        'format': 'pascal_voc',
        'label_fields': ['labels']
    })


def get_valid_transform():
    return A.Compose([  # Just transform to tensor, make appropriate bounding box changes, and return
        ToTensorV2(p=1.0)
    ], bbox_params={
        'format': 'pascal_voc',
        'label_fields': ['labels']
    })


def time_it(func: Callable):
    """ decorator used to calculate time, use @time_it in front of any function definition """

    def wrapper(*args, **kwargs):
        time_start = time.time()
        ret = func(*args, **kwargs)
        time_end = time.time()
        logging.info(f'consumed time of "{getattr(func, "__name__")}" is : {str(time_end - time_start)} s')
        return ret

    return wrapper


def create_folder(path: str):
    existence = os.path.exists(path)
    if not existence:
        os.makedirs(path)


def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0
    width_1 = box1[2] - box1[0]
    height_1 = box1[3] - box1[1]

    width_2 = box2[2] - box2[0]
    height_2 = box2[3] - box2[1]

    area1 = width_1 * height_1
    area2 = width_2 * height_2
    union = area1 + area2 - intersection

    iou = float(intersection / union)
    return iou


def check_row_in_2d(ele, test_array):
    # https://stackoverflow.com/questions/25823608/find-matching-rows-in-2-dimensional-numpy-array
    return np.any(np.all((test_array == ele), axis=1))


def convert_np_dtype_to_gdal_type(dtype):
    match dtype:
        case 'uint8':
            gdal_type = gdal.GDT_Byte
        case 'int8':
            gdal_type = gdal.GDT_Int8
        case 'uint16':
            gdal_type = gdal.GDT_UInt16
        case 'int16':
            gdal_type = gdal.GDT_Int16
        case 'uint32':
            gdal_type = gdal.GDT_UInt32
        case 'int32':
            gdal_type = gdal.GDT_Int32
        case 'uint64':
            gdal_type = gdal.GDT_UInt64
        case 'int64':
            gdal_type = gdal.GDT_Int64
        case 'float32':
            gdal_type = gdal.GDT_Float32
        case 'float64':
            gdal_type = gdal.GDT_Float64
        case _:
            raise RuntimeError('Unknown numpy data type')
    return gdal_type


def delete_non_max_items(original_array: np.ndarray, delete_column=(0, 1), score_column=-1):
    """
    delete non max pairs according score column
    :param original_array:
    :param delete_column:
    :param score_column:
    :return:

    example:
    input: [[0, 1, 0.2]
            [1, 0, 0.1]
            [0, 2, 0.3]
            [1, 2, 0.4]]
    output: [[0, 2, 0.3]
             [1, 2, 0.4]]
    """
    original_array = original_array[np.argsort(-original_array[..., score_column])]

    unique_value_of_column_1, counts_of_column_1 = np.unique(original_array[..., delete_column[0]], return_counts=True)
    repeated_unique_value_of_column_1 = unique_value_of_column_1[np.where(counts_of_column_1 > 1)]
    unique_value_of_column_2, counts_of_column_2 = np.unique(original_array[..., delete_column[1]], return_counts=True)
    repeated_unique_value_of_column_2 = unique_value_of_column_2[np.where(counts_of_column_2 > 1)]
    for item in original_array:
        # delete non-max match pairs in one loop to avoid deleting some effective match pairs
        if item[0] in repeated_unique_value_of_column_1:
            index_i_1 = np.where(original_array[..., delete_column[0]] == item[0])[0]
            original_array = np.delete(original_array, index_i_1[1:], axis=0)
        if item[1] in repeated_unique_value_of_column_2:
            index_i_2 = np.where(original_array[..., delete_column[1]] == item[1])[0]
            original_array = np.delete(original_array, index_i_2[1:], axis=0)

    return original_array


# def cal_pr_curve_area(pr_list):
#     ap = 0
#     # accumulate all areas of trapeziums
#     for i in range(pr_list.shape[0] - 1):
#         h_i = pr_list[i + 1][1] - pr_list[i][1]
#         ap += (pr_list[i + 1][0] + pr_list[i][0]) * h_i / 2
#
#     return ap


def divide_annotations(annotations, category_list, sorted=True):
    """label, box, score"""
    new_annotations = [[] for _ in range(len(category_list))]
    for i in range(len(category_list)):
        new_annotations[i] = annotations[np.where(annotations[..., 0] == category_list[i])]
        if sorted:
            new_annotations[i] = new_annotations[i][np.argsort(-new_annotations[i][:, -1])]
    return new_annotations


def calculate_map(dts, gts, category_list):
    """label, box, score"""
    # logging.info(f'dts = {dts}')
    dts_sort = divide_annotations(dts, category_list)
    # logging.info(f'dts = {dts}')
    # logging.info(f'gts = {gts}')
    gts_sort = divide_annotations(gts, category_list, sorted=False)
    logging.info(f'gts_sort = {gts_sort}')
    # dts_sort = dts[np.argsort(-dts[:, -1])]
    logging.info(f'dts_sort = {dts_sort}')

    iou_threshold_list = np.linspace(0.5, 0.95, 10, endpoint=True)
    # logging.info(f'iou_threshold_list = {iou_threshold_list}')
    category_count = len(category_list)
    tp_array = np.zeros((category_count, 10, 1))
    fp_array = np.zeros((category_count, 10, 1))
    fn_array = np.zeros((category_count, 10, 1))
    for j in range(category_count):
        for i, iou_threshold in enumerate(iou_threshold_list):
            # if gts.size == 0:
            #     continue
            # for confidence_threshold in confidence_threshold_list:
            tps = []
            gts_copy = gts_sort[j].copy()
            # logging.info(f'confidence = {confidence_threshold}')
            # # dts_copy = dts_sort[j][np.where(dts_sort[j][:, -1] >= confidence_threshold)]
            # logging.info(f'dts_sort[j] = {dts_sort[j]}')
            # dts_copy = list(filter(lambda x:x[-1] >= confidence_threshold, dts_sort[j]))
            dts_copy = dts_sort[j].copy()
            # logging.info(f'dts_copy = {dts_copy}')
            # logging.info(f'gts_copy = {gts_copy}')
            for _, dt in enumerate(dts_copy):
                # logging.info(f'dt = {dt}')
                # logging.info(f'gts_copy = {gts_copy}')
                if gts_copy.size == 0:
                    continue
                max_iou_gt = np.argmax([calculate_iou(dt[1:-1], gt[1:]) for gt in gts_copy])
                max_iou = np.max([calculate_iou(dt[1:-1], gt[1:]) for gt in gts_copy])
                # logging.info(max_iou_gt)
                # logging.info(f'max_iou = {max_iou}')
                # if dt[0] == gts_copy[max_iou_gt][0] and max_iou >= iou_threshold:
                if max_iou >= iou_threshold:
                    tps.append(dt)
                    gts_copy = np.delete(gts_copy, max_iou_gt, axis=0)

            tps = np.asarray(tps)
            fps = np.asarray([dt for dt in dts_copy if not check_row_in_2d(dt, tps)])
            fns = np.asarray(gts_copy)
            # logging.info(f'tps = {tps}')
            # logging.info(f'fps = {fps}')
            # logging.info(f'fns = {fns}')
            tp = tps.shape[0]
            fp = fps.shape[0]
            fn = fns.shape[0]
            tp_array[j, i, 0] = tp
            fp_array[j, i, 0] = fp
            fn_array[j, i, 0] = fn
            # logging.info(tp, fp, fn)
            # if tp + fp != 0 and tp + fn != 0:
            #     precision = tp / (tp + fp)
            #     recall = tp / (tp + fn)
            #     pr_list.append([precision, recall])

            # pr_list.append([0, 1])
            # pr_list.append([1, 0])
            # pr_list = np.unique(np.asarray(pr_list), axis=0)
            # logging.info(f'pr_list = {pr_list}')
            # pr_list = pr_list[np.argsort(pr_list[:, -1])]
            # logging.info(f'pr_list = {pr_list}')

    return tp_array, fp_array, fn_array


@time_it
def calculate_all_map(image_names, image_shape, labels_path, dts_list, category_list):
    # gts_list = [[] for _ in range(len(image_names))]
    # for i, image_name in enumerate(image_names):
    #     image_stem, _ = os.path.splitext(image_name)
    #     label = read_txt_label(f'{labels_path}/{image_stem}')
    #     gts_r = label
    #     gts_r[:, 1:] = yolo2number(image_shape, label[:, 1:])
    #     gts_list[i] = gts_r
    labels_names = natsorted(os.listdir(labels_path))
    gts_list = [np.asarray([]) for _ in range(len(labels_names))]
    for i, label_name in enumerate(labels_names):
        with open(f'{labels_path}/{label_name}', 'r') as label_file:
            # logging.info(np.array(label_file.read().split()))
            content = np.array(label_file.read().split()).reshape(-1, 5).astype(float)
            content[..., 0].astype(int)
            gts_r = content
            gts_r[..., 1:] = yolo2number(image_shape, content[..., 1:])
            gts_list[i] = gts_r

    # logging.info(f'dts_list = {dts_list}')
    # logging.info(f'gts_list = {gts_list}')

    category_count = len(category_list)

    iou_threshold_number = 10
    images_number = len(image_names)
    recall_threshold_number = 101
    precisions_array = np.zeros((category_count, iou_threshold_number, recall_threshold_number))
    recalls_array = np.zeros((category_count, iou_threshold_number))
    scores_array = np.zeros((category_count, iou_threshold_number, recall_threshold_number))

    total_result = np.zeros((category_count, 10, 3, len(gts_list)))
    total_tp = np.zeros((category_count, 10, len(gts_list)))

    total_map = np.zeros(category_count)
    # for i in range(len(gts_list)):
    #  total_map += calculate_map(dts_list[i], gts_list[i])
    for i in range(len(gts_list)):
        tp_i, fp_i, fn_i = calculate_map(dts_list[i], gts_list[i], category_list)
        logging.info(f'tp_i = {tp_i}')
        logging.info(f'fp_i = {fp_i}')
        logging.info(f'fn_i = {fn_i}')
        u = np.concatenate((tp_i, fp_i, fn_i), axis=2)
        #  logging.info(f'u = {u}')
        #  logging.info(u.shape)
        total_result[:, :, :, i] = u

    # logging.info(f'total_result = {total_result}')
    new_total_result = np.cumsum(total_result, axis=3)
    logging.info(f'new_total_result = {new_total_result}')
    logging.info(new_total_result.shape)

    tp_1 = new_total_result[:, :, 0, :]
    # logging.info(f'tp_1 = {tp_1}')
    # logging.info(tp_1.shape)
    fp_1 = new_total_result[:, :, 1, :]
    # logging.info(f'fp_1 = {fp_1}')
    # logging.info(fp_1.shape)
    fn_1 = new_total_result[:, :, 2, :]
    # logging.info(f'fn_1 = {fn_1}')
    # logging.info(fn_1.shape)

    precision_1 = tp_1 / (tp_1 + fp_1 + np.spacing(1))
    recall_1 = tp_1 / (tp_1 + fn_1 + np.spacing(1))
    # logging.info(f'precision_1 = {precision_1}')
    # logging.info(f'recall_1 = {recall_1}')
    # shape = precision_1.shape
    # pr = np.concatenate(precision_1.reshape(shape[0],shape[1],shape[2],1), recall_1.reshape(shape[0],shape[1],shape[2],1))
    # logging.info(f'pr = {pr}')

    recalls_array[0, :] = recall_1[0, :, -1]
    recalls_array[1, :] = recall_1[1, :, -1]
    # logging.info(recalls_array)

    iou_threshold_list = np.linspace(0.5, 0.95, 10, endpoint=True)
    recall_threshold_list = np.linspace(0, 1, 101, endpoint=True)
    # logging.info(f'iou_threshold_list = {iou_threshold_list}')
    for i, cat in enumerate(category_list):
        for j, iou_threshold in enumerate(iou_threshold_list):
            rc = recall_1[i, :, -1]
            pr_list = precision_1[i, j]
            q = np.zeros((101,))

            # logging.info(f'pr_list = {pr_list}')
            for k in range(images_number - 1, 0, -1):
                if pr_list[k] > pr_list[k - 1]:
                    pr_list[k - 1] = pr_list[k]
            logging.info(f'pr_list = {pr_list}')
            inds = np.searchsorted(rc, recall_threshold_list, side='left')
            logging.info(inds)
            try:
                for ri, pi in enumerate(inds):
                    q[ri] = pr_list[pi]
            except ArithmeticError:
                pass
            logging.info(q)
            precisions_array[i, j, :] = q

    logging.info(f'precision_array = {precisions_array}')
    for i, cat in enumerate(category_list):
        ap50 = np.mean(precisions_array[i][0])
        logging.info(f'ap50 = {ap50}')
        ap75 = np.mean(precisions_array[i][5])
        logging.info(f'ap75 = {ap75}')
        ap50_95 = np.mean(precisions_array[i])
        logging.info(f'ap50_95 = {ap50_95}')

    # total_map /= len(gts_list)
    # logging.info(f'total_map = {total_map}')
    # full_map = np.mean(total_map)
    # logging.info(f'full_map = {full_map}')


def get_platform_coordinates(result_list, max_platform_id):
    # logging.info(max_platform_id)
    result_flatten = [ele_1d for ele_2d in result_list for ele_1d in ele_2d]
    platform_boxes = [np.array([]) for _ in range(max_platform_id)]
    platform_coordinates = np.zeros((max_platform_id, 3))
    platform_coordinates[:, 0] = np.arange(1, max_platform_id + 1, dtype=np.intp)
    for i in range(max_platform_id):
        platform_boxes[i] = np.array([result_item[1:5] for result_item in result_flatten if
                                      result_item[-1] == i + 1])
        platform_boxes_x = (platform_boxes[i][..., 2] + platform_boxes[i][..., 0]) / 2
        platform_boxes_y = (platform_boxes[i][..., 3] + platform_boxes[i][..., 1]) / 2
        platform_coordinates[i][1] = np.mean(platform_boxes_x)
        platform_coordinates[i][2] = np.mean(platform_boxes_y)

    return platform_coordinates


def get_platform_ship_coordinates_by_day(result_list, ori_list):
    platform_coordinates_by_day = [[] for _ in range(len(result_list))]
    ship_coordinates_by_day = [[] for _ in range(len(result_list))]
    for i in range(len(result_list)):
        geo_transform = ori_list[i]['geo_transform']
        result_day_i = result_list[i]
        for result in result_day_i:
            obj_id = result[-1]
            image_x_min = result[1]
            image_y_min = result[2]
            image_x_max = result[3]
            image_y_max = result[4]

            geo_x_min, geo_y_min = image_coordinates_2_latitude_longitude(geo_transform, (image_x_min, image_y_min))
            geo_x_max, geo_y_max = image_coordinates_2_latitude_longitude(geo_transform, (image_x_max, image_y_max))
            if obj_id != 0:
                platform_coordinates_by_day[i].append([ori_list[i]['acquire_time'], obj_id,
                                                       (image_x_min + image_x_max) / 2, (image_y_min + image_y_max) / 2,
                                                       image_x_min, image_y_min, image_x_max, image_y_max,
                                                       (geo_x_min + geo_x_max) / 2, (geo_y_min + geo_y_max) / 2,
                                                       geo_x_min, geo_y_min, geo_x_max, geo_y_max,
                                                       ])
            else:
                ship_coordinates_by_day[i].append([ori_list[i]['acquire_time'], obj_id,
                                                   (image_x_min + image_x_max) / 2, (image_y_min + image_y_max) / 2,
                                                   image_x_min, image_y_min, image_x_max, image_y_max,
                                                   (geo_x_min + geo_x_max) / 2, (geo_y_min + geo_y_max) / 2,
                                                   geo_x_min, geo_y_min, geo_x_max, geo_y_max,
                                                   ])
            # logging.info(j)
            # logging.info(platform_coordinates_by_day[i])
            platform_coordinates_by_day[i].sort(key=lambda x: x[0])
            # logging.info(platform_coordinates_by_day[i])
    return platform_coordinates_by_day, ship_coordinates_by_day


def get_platform_ship_coordinates_by_id(result_list, ori_list, max_platform_id):
    platform_coordinates_by_id = [{} for _ in range(max_platform_id)]
    full_acquire_time_list = [ori_list_item['acquire_time'] for ori_list_item in ori_list]
    full_geo_transform_list = [ori_list_item['geo_transform'] for ori_list_item in ori_list]
    for i in range(max_platform_id):
        time_geo_transform_record_list = [[acquire_time, geo_transform, record]
                                          for acquire_time, geo_transform, record_day_i in
                                          zip(full_acquire_time_list, full_geo_transform_list, result_list)
                                          for record in record_day_i if record[-1] == i + 1]

        acquire_time_list = [item[0] for item in time_geo_transform_record_list]
        geo_transform_list = [item[1] for item in time_geo_transform_record_list]
        record_list = [item[2] for item in time_geo_transform_record_list]
        # print(acquire_time_list)
        # print(record_list)
        result = []
        for record, geo_transform in zip(record_list, geo_transform_list):
            image_x_min = record[1]
            image_y_min = record[2]
            image_x_max = record[3]
            image_y_max = record[4]

            geo_x_min, geo_y_min = image_coordinates_2_latitude_longitude(geo_transform, (image_x_min, image_y_min))
            geo_x_max, geo_y_max = image_coordinates_2_latitude_longitude(geo_transform, (image_x_max, image_y_max))

            result.append([image_x_max - image_x_min, image_y_max - image_y_min, geo_x_min, geo_x_max, geo_y_min, geo_y_max])
        result = np.asarray(result)
        average_x_size = np.mean(result[..., 0])
        average_y_size = np.mean(result[..., 1])
        average_x_geo = np.mean(result[..., 2] + result[..., 3]) / 2
        average_y_geo = np.mean(result[..., 4] + result[..., 5]) / 2

        platform_coordinates_by_id[i] = {
            'id': i+1,
            'geo_x_center': average_x_geo,
            'geo_y_center': average_y_geo,
            'average_x_size': average_x_size,
            'average_y_size': average_y_size,
            'first_time': acquire_time_list[0],
            'last_time': acquire_time_list[-1],
            'frequency': len(acquire_time_list),
        }

        logging.info(platform_coordinates_by_id[i])
    return platform_coordinates_by_id


def get_platform_sizes(result_list, max_platform_id):
    logging.info(max_platform_id)
    result_flatten = [ele_1d for ele_2d in result_list for ele_1d in ele_2d]
    platform_boxes = [np.asarray([]) for _ in range(max_platform_id)]
    platform_coordinates = np.zeros((max_platform_id, 3), dtype=np.float64)
    platform_coordinates[:, 0] = np.arange(1, max_platform_id + 1)
    for i in range(max_platform_id):
        platform_boxes[i] = np.asarray([result_item[1:5] for result_item in result_flatten if
                                        result_item[-1] == i + 1])
        platform_boxes_width = platform_boxes[i][:, 2] - platform_boxes[i][:, 0]
        platform_boxes_height = platform_boxes[i][:, 3] - platform_boxes[i][:, 1]
        platform_coordinates[i][1] = np.mean(platform_boxes_width)
        platform_coordinates[i][2] = np.mean(platform_boxes_height)

    return platform_coordinates


def points_to_shapefile(layer_name, points, output_shapefile, target_epsg: int):
    # 创建新的矢量文件
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N

    # 创建图层
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('ID', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    # fieldDefn = ogr.FieldDefn('event_date', ogr.OFTDate)
    # layer.CreateField(fieldDefn)

    # 添加点要素
    for id, lon, lat in points:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(float(lon), float(lat))
        feature = ogr.Feature(layer_defn)
        feature.SetField('ID', str(id + 1))  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)
        # feature = None

    # 释放资源
    # data_source = None


def write_shp_file(csv_path, geo_locations, output_shp_path, layer_name):
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'lon', 'lat'])  # Write header
        for i in range(len(geo_locations)):
            writer.writerow(geo_locations[i])
    points_to_shapefile(layer_name, geo_locations, output_shp_path, 4326)


def func(x, p):
    a, b = p
    return a * x + b


def residuals(p, y, x):
    return y - func(x, p)


def generate_trend_by_date(variable_array, acquire_time_list: list[datetime.date]):
    data_rebuild = np.zeros((len(variable_array), 2))
    data_rebuild[:, 1] = variable_array
    for i, time_i in enumerate(acquire_time_list):
        delta_days = (time_i - acquire_time_list[0]).days
        data_rebuild[i, 0] = delta_days
    p0 = np.asarray(
        [(data_rebuild[-1, 1] - data_rebuild[0, 1]) / (data_rebuild[-1, 0] + np.spacing(1)), data_rebuild[0, 0]])
    trend = scipy.optimize.leastsq(residuals, p0, args=(data_rebuild[:, 1], data_rebuild[:, 0]))  # least_squares()
    a, b = trend[0]
    logging.info([a, b])
    interpolate_data = np.zeros_like(variable_array, dtype=np.float32)
    for i in range(len(interpolate_data)):
        interpolate_data[i] = data_rebuild[i, 0] * a + b
    return interpolate_data


def read_polygon_shapefile(shapefile_path):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    with driver.Open(shapefile_path) as file:
        # 读取元数据
        # logging.info(file)
        layer = file.GetLayer()
        dir(layer)
        n = layer.GetFeatureCount()
        # logging.info(f'feature count = {n}')

        feat = layer.GetFeature(0)
        dir(feat)
        # logging.info(feat)

        geom = feat.GetGeometryRef()
        polygon = geom.GetGeometryRef(0)
        polygon_list = [[polygon.GetX(i), polygon.GetY(i)] for i in range(polygon.GetPointCount())]
        pts = np.array(polygon_list)
        # logging.info(pts)
    return pts

class Sentinel1:
    def __init__(self, file_path: str, pattern=r'1SDV_(.*)T(.*)_(.*)T'):
        self.type = None
        self.filename = os.path.basename(file_path)
        self.filename_stem = os.path.splitext(self.filename)[0]
        with gdal.Open(file_path) as tiff_file:
            self.geo_transform = tiff_file.GetGeoTransform()
            self.projection = tiff_file.GetProjection()
        self.shape = imagesize.get(file_path)
        acquire_time_select = re.search(pattern, self.filename)
        if acquire_time_select:
            acquire_year_month_day_str = str(acquire_time_select.group(1))
            acquire_hour_minute_second_str = str(acquire_time_select.group(2))
            acquire_year_month_day_str_formated = (f'{acquire_year_month_day_str[0:4]}-'
                                                   f'{acquire_year_month_day_str[4:6]}-'
                                                   f'{acquire_year_month_day_str[6:8]}-'
                                                   f'{acquire_hour_minute_second_str[0:2]}-'
                                                   f'{acquire_hour_minute_second_str[2:4]}-'
                                                   f'{acquire_hour_minute_second_str[4:6]}'
                                                   )

            self.acquire_time = datetime.datetime.strptime(acquire_year_month_day_str_formated, '%Y-%m-%d-%H-%M-%S')
        else:
            raise RuntimeError('Acquire time not found for given pattern!')

    def __lt__(self, other):
        return self.acquire_time < other.acquire_time

    def __gt__(self, other):
        return self.acquire_time == other.acquire_time


def build_sorted_sentinel_1_list(path):
    sorted_sentinel_1_list = sorted([Sentinel1(os.path.join(path, filename)) for filename in os.listdir(path)
                                     if (filename.endswith('.tif') and filename.startswith('S1'))])
    return sorted_sentinel_1_list