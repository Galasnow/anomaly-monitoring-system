import re
from typing import List

import cv2
import matplotlib.dates
import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt

from osgeo import gdal

gdal.UseExceptions()

from config import original_image_path, modified_label_path, output_shp_path_occur, output_shp_path_stable, \
    output_shp_path_disappear, output_shp_path_occur_and_disappear, output_shp_path_by_day, output_stem_path, support_file_list
from utils import *
from util.labels import *
import imagesize

mpl.rcParams.update({'font.size': 18,
                     'font.family': 'Microsoft YaHei',
                     'mathtext.fontset': 'stix'})
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


def write_csv(content, csv_file_path, head=None):
    with open(csv_file_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if head is not None:
            writer.writerow(head)
        writer.writerows(content)


def detect_move_position(disappear_platform, occur_platform, resolution=10):
    # logging.info(disappear_platform[..., 0])
    id_disappear = disappear_platform[..., 0].astype(np.intp)

    coordinates_disappear = disappear_platform[..., 1:3].astype(np.float32)
    sizes_disappear = disappear_platform[..., 3:5].astype(np.float32)
    time_disappear = disappear_platform[..., 5]

    id_occur = occur_platform[..., 0].astype(np.intp)
    coordinates_occur = occur_platform[..., 1:3].astype(np.float32)
    sizes_occur = occur_platform[..., 3:5].astype(np.float32)
    time_occur = occur_platform[..., 5]

    prob_list = []
    for i in range(len(disappear_platform)):
        area_1 = sizes_disappear[i][0] * sizes_disappear[0][1]
        contour_1 = np.array([[
            [coordinates_disappear[i][0] - sizes_disappear[i][0] / 2,
             coordinates_disappear[i][1] - sizes_disappear[i][1] / 2],
            [coordinates_disappear[i][0] + sizes_disappear[i][0] / 2,
             coordinates_disappear[i][1] - sizes_disappear[i][1] / 2],
            [coordinates_disappear[i][0] + sizes_disappear[i][0] / 2,
             coordinates_disappear[i][1] + sizes_disappear[i][1] / 2],
            [coordinates_disappear[i][0] - sizes_disappear[i][0] / 2,
             coordinates_disappear[i][1] + sizes_disappear[i][1] / 2],
            [coordinates_disappear[i][0] - sizes_disappear[i][0] / 2,
             coordinates_disappear[i][1] - sizes_disappear[i][1] / 2]
        ]],
            dtype=np.intp)
        time_1 = datetime.datetime.strptime(time_disappear[i], "%Y-%m-%d")
        for j in range(len(occur_platform)):
            time_2 = datetime.datetime.strptime(time_occur[j], "%Y-%m-%d")
            time_delta = time_2 - time_1
            # logging.info(type(time_delta.days))
            if time_delta.days <= 0:
                continue

            area_2 = sizes_occur[j][0] * sizes_occur[j][1]
            size_ratio = area_2 / area_1
            if size_ratio > 1.2 or size_ratio < 0.8:
                continue

            contour_2 = np.array([[
                [coordinates_occur[i][0] - sizes_occur[i][0] / 2, coordinates_occur[i][1] - sizes_occur[i][1] / 2],
                [coordinates_occur[i][0] + sizes_occur[i][0] / 2, coordinates_occur[i][1] - sizes_occur[i][1] / 2],
                [coordinates_occur[i][0] + sizes_occur[i][0] / 2, coordinates_occur[i][1] + sizes_occur[i][1] / 2],
                [coordinates_occur[i][0] - sizes_occur[i][0] / 2, coordinates_occur[i][1] + sizes_occur[i][1] / 2],
                [coordinates_occur[i][0] - sizes_occur[i][0] / 2, coordinates_occur[i][1] - sizes_occur[i][1] / 2]
            ]],
                dtype=np.intp)
            shape_match_ratio = cv2.matchShapes(contour_1, contour_2, 1, 0.0)
            # logging.info(shape_match_ratio)
            if shape_match_ratio > 0.25:
                continue

            distance = resolution * np.sqrt(
                np.square(coordinates_disappear[i][0] - coordinates_occur[j][0]) + np.square(
                    coordinates_disappear[i][1] - coordinates_occur[j][1]))
            if distance / time_delta.days > 5e4:
                continue
            # prob = time_delta.days / (distance + np.spacing(1)) / (np.square(1 - size_ratio) + np.spacing(1)) / (shape_match_ratio + np.spacing(1))
            prob = 1 / (time_delta.days * distance) / (np.square(1 - size_ratio) + np.spacing(1)) / (
                    shape_match_ratio + np.spacing(1))
            prob_list.append([id_disappear[i], id_occur[j], prob])

    prob_match_list = np.array(prob_list)
    # logging.info(f'prob_match_list = {prob_match_list}')
    prob_match_list = delete_non_max_items(prob_match_list, delete_column=(0, 1), score_column=-1)
    prob_match_dict = []
    for item in prob_match_list:
        prob_match_dict.append({'id_disappear': int(item[0]), 'id_occur': int(item[1]), 'prob': item[2]})
    logging.info(f'prob_match_dict =\n {np.array(prob_match_dict)}')
    logging.info(len(prob_match_list))
    return prob_match_list


# def manual_correction(result_list):
#     new_result_list = result_list
#     modify_ids_1 = [36, 70, 77, 84, 87]
#     modify_ids_2 = [37, 79]
#     for i in range(len(result_list)):
#         for item in result_list[i]:
#             if item[-1] in modify_ids_1[1:]:
#                 item[-1] = modify_ids_1[0]
#             if item[-1] in modify_ids_2[1:]:
#                 item[-1] = modify_ids_2[0]


# def plot_area_data(area_csv, start_date='2016/01/01', tolerance=0.005, area_line=None,
#                    accuracy_csv=None):
#     """
#     绘制面积随时间变化的图，并保存异常日期。
#
#     参数：
#     csv_file: str, 包含日期和面积数据的 CSV 文件路径
#     start_date: str, 起始日期，格式为 'YYYY/MM/DD'
#     tolerance: float, 面积增长的误差范围百分比
#     output_file: str, 可选，若提供则保存图像为此路径
#     txt_file: str, 可选，若提供则保存异常日期为此路径
#     output_csv: str, 可选，若提供则保存提取的 CSV 文件
#     """
#     # 读取数据
#     table = pd.read_csv(area_csv)
#     doy = table['date'].astype(str).map(lambda date: cal_DOY_from_start(start_date, date))
#     area = table['area'].values
#
#     # 新增 'abnormal' 列，默认值为 0（正常）
#     table['abnormal'] = 0
#
#     # 检查连续三天面积增长的情况并记录第二天的日期
#     anomaly_dates = []
#     anomaly_doys = []
#     anomaly_areas = []
#     pre_column = [0] * len(area)  # 用于标记是否发生异常，初始化为0
#     true_column = [""] * len(area)  # 初始化 'TRUE' 列为空字符串
#
#     for i in range(1, len(area) - 1):
#         if (area[i] > area[i - 1] * (1 + tolerance)) and (area[i + 1] > area[i] * (1 + tolerance)):
#             anomaly_dates.append(table['date'].iloc[i])
#             anomaly_doys.append(doy.iloc[i])
#             anomaly_areas.append(area[i])
#             table.at[i, 'abnormal'] = 1  # 标记该日期为异常
#
#     # 获取第一个异常日期的索引
#     first_anomaly_index = next((i for i, val in enumerate(table['abnormal']) if val == 1), None)
#
#     # 保存修改后的 CSV 文件
#     table.to_csv(area_csv, index=False, encoding='utf-8-sig')  # 直接保存到原始的 csv_file
#
#     # 提取数据并保存为新的 CSV 文件
#     extracted_data = None  # 定义一个默认的 None 值，避免未定义错误
#
#     if accuracy_csv and first_anomaly_index is not None:
#         # 将 'TRUE' 列添加到原表格
#         table['manual_label'] = true_column  # 新增 'TRUE' 列，内容为空
#         table.drop(columns=['area'], inplace=True)  # 删除 'area' 列
#         table.drop(columns=['abnormal'], inplace=True)  # 删除 'area' 列
#
#         # 根据第一个异常日期的索引提取数据
#         if first_anomaly_index < 10:
#             extracted_data = table.iloc[:20, :]
#         else:
#             # 提取第一行和异常日期前9行以及后10行
#             start_idx = max(first_anomaly_index - 10, 0)
#             end_idx = min(first_anomaly_index + 10, len(table))
#             extracted_data = table.iloc[start_idx:end_idx, :]
#
#         # 保存提取的数据
#         if extracted_data is not None:
#             extracted_data.to_csv(accuracy_csv, index=False, encoding='utf-8-sig')
#
#     # 绘图
#     fig, ax1 = plt.subplots(figsize=(14, 8.5))
#     ax1.plot(doy.values, area, color='red', lw=5, marker=None)  # red
#
#     ax1.set_xticks([0, 365, 730, 1095, 1461, 1826, 2191, 2556, 2922, 3288])
#     ax1.set_ylabel('数量', fontsize=28)
#     ax1.set_xlabel('日期', fontsize=28)
#
#     # 标记异常日期
#     ax1.scatter(anomaly_doys, anomaly_areas, facecolors='#FAFA33', edgecolor='black', marker='o', s=200, linewidths=1.5,
#                 zorder=2)
#
#     # 标注异常日期，根据ID（索引）判断奇偶数，设置不同的偏移量
#     texts = []
#     for idx, (x, y, date) in enumerate(zip(anomaly_doys, anomaly_areas, anomaly_dates)):
#         month_day = "/".join(date.split('/')[1:])  # 去掉年份部分
#
#         # 根据ID判断奇偶数，调整偏移方向
#         if (idx+1) % 2 == 0:  # 偶数ID，向左偏移
#             x_offset = -240
#             y_offset = 0.12
#         else:  # 奇数ID，向右偏移
#             x_offset = 30
#             y_offset = -0.1
#
#         text = ax1.text(x + x_offset, y + y_offset, month_day, fontsize=20, color='#8A2BE2', ha='left', va='center',
#                         rotation=0,fontweight='bold',
#                         bbox=dict(facecolor='white', edgecolor='#4169E1', boxstyle='round,pad=0.001', alpha=0))
#         texts.append(text)
#
#     ax1.axes.xaxis.set_ticklabels(
#         ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"])
#
#     y_max = max(area) * 1.1
#     y_min = math.floor(min(area))
#     ax1.set_ylim([y_min, y_max])
#     ax1.set_xlim([0, 3288])
#
#     plt.yticks(fontsize=28)
#     plt.xticks(fontsize=28)
#
#     # 保存或显示图像
#     if area_line:
#         plt.savefig(area_line, bbox_inches='tight')
#     else:
#         plt.show()


def search_special_events(occur_array, disappear_array, platform_geo_location):
    disappear_ids = [item[-1] for item in disappear_array]
    logging.info(f'disappear_ids = {disappear_ids}')
    special_array = []
    for record_occur in occur_array:
        id = record_occur[-1]
        # logging.info(f'id = {id}')
        if id in disappear_ids:
            index_id = disappear_ids.index(id)
            # logging.info(f'index_id = {index_id}')
            # if index is not None:
            record_disappear = disappear_array[index_id]
            # logging.info(f'record_disappear = {record_disappear}')
            # for record_disappear in disappear_array:
            if (record_disappear[0] - record_occur[0]).days >= 90:
                special_array.append([record_occur[0], record_disappear[0], platform_geo_location[id - 1][1],
                                      platform_geo_location[id - 1][2], id])
    logging.info(f'special_array = {special_array}')
    logging.info(len(special_array))
    return special_array


def calculate_size_score(size):
    if size >= 0:
        if size <= 48:
            score = size / 48.0
        else:
            score = 1.0
    else:
        raise RuntimeError('size must >= 0')
    return score


def calculate_time_score(days):
    if days >= 0:
        if days <= 24:
            score = days / 24.0
        else:
            score = 1.0
    else:
        raise RuntimeError('stay days must >= 0')
    return score


def calculate_iou_score(iou_list: List | np.ndarray):
    if any(iou_list) < 0:
        raise  RuntimeError('IOU must >= 0')
    exponent = 1/4.0
    score = np.mean(np.pow(iou_list, exponent))
    return score


if __name__ == "__main__":
    initial_logging_formatter()
    ori_list = []
    original_image_names = [image_name for image_name in natsorted(os.listdir(original_image_path))
                            if os.path.splitext(image_name)[-1].replace('.', '') in support_file_list]

    pattern = r'1SDV_(.*)T(.*)T'

    for original_image_name in original_image_names:
        stem, _ = os.path.splitext(original_image_name)
        acquire_time_select = re.search(pattern, stem)
        geo_transform = None
        # projection = None
        if acquire_time_select:
            acquire_time = str(acquire_time_select.group(1))
            year = int(acquire_time[:4])
            month = int(acquire_time[4:6])
            day = int(acquire_time[6:8])
        else:
            raise RuntimeError('acquire time not found !')

        if os.path.splitext(original_image_name)[-1] in ['.tif', '.tiff']:
            with gdal.Open(f'{original_image_path}/{original_image_name}') as tiff_file:
                geo_transform = tiff_file.GetGeoTransform()
                # projection = tiff_file.GetProjection()
        ori_list.append({'image_original_stem': stem,
                         # 'image_original_name': original_image_name,
                         'shape': imagesize.get(f'{original_image_path}/{original_image_name}'),
                         'geo_transform': geo_transform,
                         # 'projection': projection,
                         'acquire_time': datetime.date(year, month, day)
                         })
    logging.info(len(ori_list))
    ori_list.pop(0)
    ori_list.pop(-1)
    acquire_time_list = [ori_list_item['acquire_time'] for ori_list_item in ori_list]

    result_list = []
    max_platform_id = 0
    for i in range(len(ori_list)):
        result = read_txt_label(f'{modified_label_path}/{ori_list[i]['image_original_stem']}.txt')
        result[..., 1:5] = yolo2number(ori_list[i]['shape'], result[..., 1:5])

        max_platform_id = int(np.max((np.max(result[..., -1]), max_platform_id)))

        result_list.append(result)
    logging.info(f'max_platform_id = {max_platform_id}')
    # logging.info(f'result_list = {result_list}')
    # logging.info(len(result_list))
    platform_coordinates_by_id = get_platform_ship_coordinates_by_id(result_list, ori_list, max_platform_id)

    platform_coordinates_by_day, ship_coordinates_by_day = get_platform_ship_coordinates_by_day(result_list,
                                                                                                ori_list)
    # platform_coordinates = get_platform_coordinates(result_list, max_platform_id)
    # logging.info(f'platform_coordinates = {platform_coordinates}')
    #
    # geo_transform_list = [item['geo_transform'] for item in ori_list]
    # ##########
    # platform_geo_location = platform_coordinates.copy()
    # platform_geo_location[..., 1:] = image_coordinates_2_latitude_longitude(geo_transform_list,
    #                                                                         platform_coordinates[..., 1:])
    # logging.info(f'platform_geo_location = {platform_geo_location}')

    platform_geo_location = np.asarray([[platform_coordinates['id'], platform_coordinates['geo_x_center'], platform_coordinates['geo_y_center']] for platform_coordinates in platform_coordinates_by_id])
    logging.info(f'platform_geo_location = {platform_geo_location}')
    platform_sizes = get_platform_sizes(result_list, max_platform_id)
    logging.info(f'platform_sizes = {platform_sizes}')

    platform_annotations = [[np.array([]) for j in range(len(ori_list))] for i in range(max_platform_id)]
    platform_lifetime = np.zeros((max_platform_id, len(ori_list)), dtype=np.bool_)
    for i in range(max_platform_id):
        for j in range(len(ori_list)):
            platform_annotations[i][j] = result_list[j][np.where(result_list[j][:, -1] == i + 1)]
            platform_lifetime[i][j] = True if (platform_annotations[i][j].size != 0) else False
    platform_ious = [[np.array([]) for j in range(len(ori_list))] for i in range(max_platform_id)]
    for i in range(max_platform_id):
        print(i)
        platform_i_bboxes_array = np.asarray([item[..., 1:5] for item in platform_annotations[i] if len(item) != 0]).squeeze()
        print(platform_i_bboxes_array)
        if platform_i_bboxes_array.ndim < 2:
            platform_i_bboxes_array = np.concatenate((np.reshape(platform_i_bboxes_array, (1,4)), np.reshape(platform_i_bboxes_array, (1,4))), axis=0)
        platform_ious[i] = [calculate_iou(platform_i_bboxes_array[i], platform_i_bboxes_array[i+1]) for i in range(len(platform_i_bboxes_array) - 1)]
        # calculate_iou()
        print(platform_ious[i])
        pass
    iou_scores = [calculate_iou_score(platform_ious[i]) for i in range(max_platform_id)]
    print(iou_scores)


    # occur_count = np.zeros(len(ori_list))
    # disappear_count = np.zeros(len(ori_list))
    # stable_count = np.zeros(len(ori_list))
    #
    # classification_list = [[[], [], []] for _ in range(len(ori_list))]
    #
    # for j in range(1, len(ori_list) - 1):
    #     for i in range(max_platform_id):
    #         # elif platform_lifetime[i][j - 1] == True and platform_lifetime[i][j] == True and platform_lifetime[i][j + 1] == True:
    #         if platform_lifetime[i][j - 1] == True and platform_lifetime[i][j] == True:
    #             stable_count[j] += 1
    #             classification_list[j][0].append(i + 1)
    #         if platform_lifetime[i][j] == True and platform_lifetime[i][j - 1] == False:
    #             occur_count[j] += 1
    #             classification_list[j][1].append(i + 1)
    #         if platform_lifetime[i][j] == True and platform_lifetime[i][j + 1] == False:
    #             disappear_count[j + 1] += 1
    #             classification_list[j + 1][2].append(i + 1)

    # logging.info(classification_list)
    # logging.info(stable_count)
    # logging.info(occur_count)
    # logging.info(disappear_count)
    stable_index = np.where((platform_lifetime[..., 0] == True) & (platform_lifetime[..., -1] == True))[0]
    # logging.info(stable_index)
    occur_and_disappear_index = np.where((platform_lifetime[..., 0] == False) & (platform_lifetime[..., -1] == False))[
        0]
    occur_index = np.where((platform_lifetime[..., 0] == False) & (platform_lifetime[..., -1] == True))[0]
    disappear_index = np.where((platform_lifetime[..., 0] == True) & (platform_lifetime[..., -1] == False))[0]
    platform_geo_location_stable = platform_geo_location[stable_index, ...]
    platform_geo_location_occur = platform_geo_location[occur_index, ...]
    platform_geo_location_disappear = platform_geo_location[disappear_index, ...]
    platform_geo_location_occur_and_disappear = platform_geo_location[occur_and_disappear_index, ...]
    logging.info(f'count of stable platform = {len(platform_geo_location_stable)}')
    logging.info(f'count of occurred platform = {len(platform_geo_location_occur)}')
    logging.info(f'count of disappeared platform = {len(platform_geo_location_disappear)}')
    logging.info(f'count of occurred and disappeared platform = {len(platform_geo_location_occur_and_disappear)}')
    logging.info(platform_geo_location_occur)
    logging.info(platform_geo_location_occur_and_disappear)

    occur_array = []
    disappear_array = []
    for i in range(len(platform_geo_location_occur[..., 0])):
        id = int(platform_geo_location_occur[..., 0][i])
        time_line = platform_lifetime[id - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == False and time_line[w + 1] == True:
                occur_array.append(
                    [acquire_time_list[w + 1], platform_geo_location_occur[i][1], platform_geo_location_occur[i][2],
                     id])

    for i in range(len(platform_geo_location_disappear[..., 0])):
        id = int(platform_geo_location_disappear[..., 0][i])
        time_line = platform_lifetime[id - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == True and time_line[w + 1] == False:
                disappear_array.append(
                    [acquire_time_list[w + 1], platform_geo_location_disappear[i][1],
                     platform_geo_location_disappear[i][2], id])

    for i in range(len(platform_geo_location_occur_and_disappear[..., 0])):
        id = int(platform_geo_location_occur_and_disappear[..., 0][i])
        time_line = platform_lifetime[id - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == False and time_line[w + 1] == True:
                occur_array.append([acquire_time_list[w + 1], platform_geo_location_occur_and_disappear[i][1],
                                    platform_geo_location_occur_and_disappear[i][2], id])
            if time_line[w] == True and time_line[w + 1] == False:
                disappear_array.append([acquire_time_list[w + 1], platform_geo_location_occur_and_disappear[i][1],
                                        platform_geo_location_occur_and_disappear[i][2], id])

    logging.info(f'occur_array = {np.array(occur_array)}')
    logging.info(f'platform_geo_location_occur = {platform_geo_location_occur}')

    special_array = search_special_events(occur_array, disappear_array, platform_geo_location)

    output_shp_path = output_shp_path_stable
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_stable'
    write_shp_file(csv_path, platform_geo_location_stable, output_shp_path, layer_name)

    output_shp_path = output_shp_path_occur
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_occur'
    write_shp_file(csv_path, platform_geo_location_occur, output_shp_path, layer_name)

    output_shp_path = output_shp_path_disappear
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_disappear'
    write_shp_file(csv_path, platform_geo_location_disappear, output_shp_path, layer_name)

    output_shp_path = output_shp_path_occur_and_disappear
    csv_path = f'{output_shp_path}/points.csv'
    layer_name = f'points_occur_and_disappear'
    write_shp_file(csv_path, platform_geo_location_occur_and_disappear, output_shp_path, layer_name)

    # for j in range(1, len(ori_list) - 1):
    #     # logging.info(platform_coordinates_by_day[j])
    #     platform_ids_by_day = [item[0] for item in platform_coordinates_by_day[j]]
    #     platform_geo_locations = np.concatenate((np.reshape(platform_ids_by_day, (-1, 1)),
    #                                              get_latitude_longitude(geo_transform,
    #                                                                     np.array(platform_coordinates_by_day[j])[...,
    #                                                                     1:3])), axis=1)
    #     # platform_geo_locations = get_latitude_longitude(geo_transform, np.array(platform_coordinates_by_day[j])[..., 1:3])
    #     ship_ids_by_day = [item[0] for item in ship_coordinates_by_day[j]]
    #     if len(ship_coordinates_by_day[j]) != 0:
    #         ship_geo_locations = np.concatenate((np.reshape(ship_ids_by_day, (-1, 1)),
    #                                              get_latitude_longitude(geo_transform,
    #                                                                     np.array(ship_coordinates_by_day[j])[...,
    #                                                                     1:3])), axis=1)
    #     ship_geo_locations = get_latitude_longitude(geo_transform, np.array(ship_coordinates_by_day[j])[..., 1:3])
    #     logging.info(f'platform_geo_locations = {platform_geo_locations}')
    #     logging.info(f'ship_geo_locations = {ship_geo_locations}')
    #     platform_stable = []
    #     platform_occur = []
    #     platform_disappear = []
    #     for item in platform_geo_locations:
    #         if item[0] in classification_list[j][0]:
    #             platform_stable.append(item[0:3])
    #         elif item[0] in classification_list[j][1]:
    #             platform_occur.append(item[0:3])
    #         elif item[0] in classification_list[j][2]:
    #             platform_disappear.append(item[0:3])
    #     output_shp_path = f'{output_shp_path_by_day}/day_{j}_points_stable'
    #     create_folder(output_shp_path)
    #     csv_path = f'{output_shp_path}/day_{j}_points_stable.csv'
    #     layer_name = f'day_{j}_points_stable'
    #     write_shp_file(csv_path, platform_stable, output_shp_path, layer_name)
    #
    #     output_shp_path = f'{output_shp_path_by_day}/day_{j}_points_occur'
    #     create_folder(output_shp_path)
    #     csv_path = f'{output_shp_path}/day_{j}_points_occur.csv'
    #     layer_name = f'day_{j}_points_occur'
    #     write_shp_file(csv_path, platform_occur, output_shp_path, layer_name)
    #
    #     output_shp_path = f'{output_shp_path_by_day}/day_{j + 1}_points_disappear'
    #     create_folder(output_shp_path)
    #     csv_path = f'{output_shp_path}/day_{j + 1}_points_disappear.csv'
    #     layer_name = f'day_{j + 1}_points_disappear'
    #     write_shp_file(csv_path, platform_disappear, output_shp_path, layer_name)
    #     output_shp_path = f'{output_shp_path_by_day}/day_{j}_ship'
    #     create_folder(output_shp_path)
    #     csv_path = f'{output_shp_path}/day_{j}_ship.csv'
    #     layer_name = f'day_{j}_ship'
    #     # ship_geo_locations = np.concatenate((np.zeros((len(ship_geo_locations), 1)), ship_geo_locations), axis=1)
    #     if len(ship_coordinates_by_day[j]) != 0:
    #         write_shp_file(csv_path, ship_geo_locations, output_shp_path, layer_name)

    # years = matplotlib.dates.YearLocator()
    # months = matplotlib.dates.MonthLocator()
    # days = matplotlib.dates.DayLocator()
    # fig, ax = plt.subplots()
    # ax.xaxis.set_major_locator(years)
    # # ax.xaxis.set_minor_locator(months)
    # ax.xaxis.set_minor_locator(months)
    # time_format = matplotlib.dates.DateFormatter('%Y-%m-%d')
    # ax.xaxis.set_major_formatter(time_format)
    # occur_line = None
    # disappear_line = None
    # for i in range(max_platform_id):
    #     left_index = np.min(np.where(platform_lifetime[i, :]))
    #     right_index = np.max(np.where(platform_lifetime[i, :]))
    #     if left_index != 0:
    #         occur_line = ax.vlines(x=acquire_time_list[left_index], ymin=i+1-0.3, ymax=i+1+0.3,
    #                                linestyle='-', label=f'occur', color='red')
    #         #annotation_text = f'platform {i} occurred at {acquire_time_list[left_index]}'
    #         #ax.annotate(annotation_text, xy=(20, i), ha='center', va='bottom')
    #     if right_index != len(ori_list) - 1:
    #         disappear_line = ax.vlines(x=acquire_time_list[right_index], ymin=i+1-0.3, ymax=i+1+0.3,
    #                                    linestyle='-', label=f'disappear', color='green')
    #         #annotation_text = f'platform {i} disappeared at {acquire_time_list[left_index]}'
    #     color = (0, 0, 0)
    #     if i in stable_index:
    #         color = (0,0,1)
    #     elif i in occur_index:
    #         color = (1,0,0)
    #     elif i in disappear_index:
    #         color = (0,1,0)
    #     elif i in occur_and_disappear_index:
    #         color = 'orange'
    #     # logging.info(color)
    #     b = ax.barh(y=i+1, width=(acquire_time_list[right_index] - acquire_time_list[left_index]), height=0.15, left=acquire_time_list[left_index], color=(0,0,0))

    time_table: List[list[datetime.date | None]] = [[None, None] for _ in range(max_platform_id)]
    print(f'time_table = {time_table}')
    # for i in range(max_platform_id):
    #     left_index = np.min(np.where(platform_lifetime[i, :]))
    #     right_index = np.max(np.where(platform_lifetime[i, :]))
    #     if left_index != 0:
    #         time_table[i][0] = acquire_time_list[left_index].strftime("%Y-%m-%d")
    #     else:
    #         time_table[i][0] = f'{acquire_time_list[0].strftime("%Y-%m-%d")} or earlier'
    #
    #     if right_index != len(acquire_time_list) - 1:
    #         time_table[i][1] = acquire_time_list[right_index].strftime("%Y-%m-%d")
    #     else:
    #         time_table[i][1] = f'{acquire_time_list[-1].strftime("%Y-%m-%d")} or later'
    for i in range(max_platform_id):
        left_index = np.min(np.where(platform_lifetime[i, :]))
        right_index = np.max(np.where(platform_lifetime[i, :]))
        if left_index != 0:
            time_table[i][0] = acquire_time_list[left_index]
        else:
            time_table[i][0] = acquire_time_list[0]

        if right_index != len(acquire_time_list) - 1:
            time_table[i][1] = acquire_time_list[right_index]
        else:
            time_table[i][1] = acquire_time_list[-1]

    logging.info(f'time_table = {time_table}')
    # logging.info(len(time_table))
    logging.info(
        f'id       image_x       image_y       longitude       latitude        occur_time        disappear_time')
    # full_result = np.concatenate((platform_coordinates, platform_geo_location[..., 1:], time_table), axis=1)
    # logging.info(f'full_result =\n {full_result}')

    # pick_platform_disappear_index = np.concatenate((disappear_index, occur_and_disappear_index))
    # pick_platform_occur_index = np.concatenate((occur_index, occur_and_disappear_index))
    # # logging.info(pick_platform_disappear_index)
    # # logging.info(pick_platform_occur_index)
    # disappear_platform = np.concatenate((platform_coordinates[pick_platform_disappear_index],
    #                                      platform_sizes[pick_platform_disappear_index][..., 1:],
    #                                      time_table[pick_platform_disappear_index][..., 1:]), axis=1)
    # occur_platform = np.concatenate((platform_coordinates[pick_platform_occur_index],
    #                                      platform_sizes[pick_platform_occur_index][..., 1:],
    #                                      time_table[pick_platform_occur_index][..., 0:1]), axis=1)
    # logging.info(disappear_platform)
    # logging.info(occur_platform)
    # detect_move_position(disappear_platform, occur_platform)

    # fig.autofmt_xdate(rotation=25)
    # plt.ylabel('id')
    # plt.yticks(range(0, max_platform_id + 2, 10))
    # plt.title('lifetime of platform')
    # plt.legend((occur_line, disappear_line), [f'occur', f'disappear'])
    # plt.show()

    platform_counts = [np.sum(result_list[i][..., 0] == 2) for i in range(len(ori_list))]

    anomaly_events = acquire_time_list.copy()
    no_anomaly_index = [0]
    anomaly_index = np.zeros(len(platform_counts))
    anomaly_counts = platform_counts.copy()
    for i in range(1, len(platform_counts) - 1):
        if platform_counts[i] == platform_counts[i - 1]:
            no_anomaly_index.append(i)
        else:
            anomaly_index[i] = 1
    no_anomaly_index.append(len(platform_counts) - 1)
    anomaly_events = np.delete(anomaly_events, no_anomaly_index)
    anomaly_counts = np.delete(anomaly_counts, no_anomaly_index)

    output_csv_file = f'{output_stem_path}/platform_number.csv'
    with open(output_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['date', 'number', 'anomaly'])
        writer.writeheader()
        for i in range(len(platform_counts)):
            row = {'date': acquire_time_list[i].strftime("%Y/%m/%d"), 'number': platform_counts[i],
                   'anomaly': anomaly_index[i]}
            writer.writerow(row)

    content = [row for day_item in platform_coordinates_by_day for row in day_item]
    content.sort(key=lambda x: x[1])
    content = np.asarray(content)
    content[..., [0, 1]] = content[..., [1, 0]]
    output_summary_csv_file = f'{output_stem_path}/platform_summary_by_id.csv'
    head = ['id', 'date',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']
    write_csv(content, output_summary_csv_file, head)

    content = [row for day_item in platform_coordinates_by_day for row in day_item]
    output_summary_csv_file = f'{output_stem_path}/platform_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_summary_csv_file, head)

    content = [row for day_item in ship_coordinates_by_day for row in day_item]
    output_summary_csv_file = f'{output_stem_path}/ship_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_summary_csv_file, head)

    output_summary_csv_file = f'{output_stem_path}/occur.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['type', 'date', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        for item in occur_array:
            if platform_sizes[item[3] - 1, 0] * platform_sizes[item[3] - 1, 1] * 10 * 10 >= 50:
                row = {'type': "occur",
                       'date': item[0],
                       'geo_x_center': item[1],
                       'geo_y_center': item[2],
                       'id': item[3]
                       }
                writer.writerow(row)

    output_shapefile = f'{output_stem_path}/occur_events'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N

    # 创建图层
    layer_name = 'occur_events'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('DATE', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    layer.CreateField(fieldDefn)

    # 添加点要素
    for date, lon, lat, platform in occur_array:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)

        date_str = datetime.datetime.strftime(date, '%Y-%m-%d')

        feature.SetField('DATE', date_str)  # 设置属性字段
        feature.SetField('PLATFORM', platform)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/disappear.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['type', 'date', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        for item in disappear_array:
            row = {'type': "disappear",
                   'date': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'id': item[3]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/disappear_events'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N\

    # 创建图层
    layer_name = 'disappear_events'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('DATE', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    layer.CreateField(fieldDefn)

    # 添加点要素
    for date, lon, lat, platform in disappear_array:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)

        date_str = datetime.datetime.strftime(date, '%Y-%m-%d')

        feature.SetField('DATE', date_str)  # 设置属性字段
        feature.SetField('PLATFORM', platform)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/special.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['date_occur', 'date_disappear', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        ############## filter area
        for item in special_array:
            row = {'date_occur': item[0], 'date_disappear': item[1],
                   'geo_x_center': item[2],
                   'geo_y_center': item[3],
                   'id': item[4]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/special_events'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）#renaijiao 50N xijiao 49N\

    # 创建图层
    layer_name = 'special_events'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('DATE_1', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('DATE_2', ogr.OFTString)
    # fieldDefn.SetWidth(10)
    layer.CreateField(fieldDefn)

    fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    layer.CreateField(fieldDefn)

    # 添加点要素
    for date_occur, date_disappear, lon, lat, platform in special_array:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)

        date_occur_str = datetime.datetime.strftime(date_occur, '%Y-%m-%d')
        date_disappear_str = datetime.datetime.strftime(date_disappear, '%Y-%m-%d')

        feature.SetField('DATE_1', date_occur_str)  # 设置属性字段
        feature.SetField('DATE_2', date_disappear_str)  # 设置属性字段
        feature.SetField('PLATFORM', platform)  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': calculate_time_score((time_table[i][1] - time_table[i][0]).days) * calculate_size_score(
                       platform_sizes[i][1] * platform_sizes[i][2] * iou_scores[i])
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', (time_table[i][1] - time_table[i][0]).days)  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         calculate_time_score((time_table[i][1] - time_table[i][0]).days) * calculate_size_score(
                             platform_sizes[i][1] * platform_sizes[i][2]) * iou_scores[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)


    days_list = np.asarray([int((time_table[i][1] - time_table[i][0]).days) for i in range(max_platform_id)])
    time_score_list = [calculate_time_score((time_table[i][1] - time_table[i][0]).days) for i in range(max_platform_id)]
    size_score_list = [calculate_size_score(platform_sizes[i][1] * platform_sizes[i][2]) for i in range(max_platform_id)]
    p_score_list = np.asarray([iou_scores[i] * time_score_list[i] * size_score_list[i] for i in range(max_platform_id)])

    platform_geo_location_high_conf = platform_geo_location[np.where(p_score_list >= 0.3)]
    print(platform_geo_location_high_conf)
    days_list_high_conf = days_list[np.where(p_score_list >= 0.3)]
    p_score_list_high_conf = p_score_list[np.where(p_score_list >= 0.3)]

    platform_geo_location_high_conf_stable = platform_geo_location_high_conf[np.where(days_list_high_conf == np.max(days_list))]
    print(platform_geo_location_high_conf_stable)
    days_list_high_conf_stable = days_list_high_conf[np.where(days_list_high_conf == np.max(days_list))]
    p_score_list_high_conf_stable = p_score_list_high_conf[np.where(days_list_high_conf == np.max(days_list))]

    platform_geo_location_high_conf_move = platform_geo_location_high_conf[np.where(days_list_high_conf < np.max(days_list))]
    print(platform_geo_location_high_conf_move)
    days_list_high_conf_move = days_list_high_conf[np.where(days_list_high_conf < np.max(days_list))]
    p_score_list_high_conf_move = p_score_list_high_conf[np.where(days_list_high_conf < np.max(days_list))]

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_high_conf.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_high_conf):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': p_score_list_high_conf[i]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency_high_conf'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency_high_conf'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location_high_conf):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_high_conf[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         p_score_list_high_conf[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)


    output_summary_csv_file = f'{output_stem_path}/platform_frequency_stable.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_high_conf_stable):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': p_score_list_high_conf_stable[i]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency_stable'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency_stable'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location_high_conf_stable):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_high_conf_stable[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         p_score_list_high_conf_stable[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_stable.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_high_conf_stable):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': (time_table[i][1] - time_table[i][0]).days,
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'score': p_score_list_high_conf_stable[i]
                   }
            writer.writerow(row)

    output_shapefile = f'{output_stem_path}/platform_frequency_move'
    target_epsg = 4326
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    data_source = driver.CreateDataSource(output_shapefile)
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(target_epsg)

    # 创建图层
    layer_name = 'platform_frequency_move'
    layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    layer_defn = layer.GetLayerDefn()
    # logging.info(layer_defn)
    fieldDefn = ogr.FieldDefn('Frequency', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('First_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Last_time', ogr.OFTDate)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Days', ogr.OFTInteger)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id, lon, lat] in enumerate(platform_geo_location_high_conf_move):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_high_conf_move[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('Score',
                         p_score_list_high_conf_move[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    ship_counts = [np.sum(result_list[i][..., 0] == 1) for i in range(len(ori_list))]
    # fig, ax = plt.subplots(2, 1)
    # # fig.autofmt_xdate(rotation=25)
    #
    # ax[0].plot(acquire_time_list, platform_counts, marker='o')
    # ax[0].set_title('number of platform')
    # ax[0].set_ylabel('number')
    # ax[0].set_yticks(np.arange(min(platform_counts) - 1, max(platform_counts) + 2, 1, dtype=np.intp))
    # ax[0].set_ylim(min(platform_counts) - 0.5, max(platform_counts) + 0.5)
    # ax[1].plot(acquire_time_list, ship_counts, marker='o')
    # ax[1].set_title('number of ship')
    # ax[1].set_yticks(np.arange(min(ship_counts) - 1, max(ship_counts) + 2, 2, dtype=np.intp))
    # ax[1].set_ylim(min(ship_counts) - 0.5, max(ship_counts) + 0.5)

    acquire_time_list.pop(0)
    acquire_time_list.pop(-1)
    platform_counts = platform_counts[1:-1]
    fig, ax1 = plt.subplots()
    # fig.autofmt_xdate(rotation=25)

    trend = generate_trend_by_date(platform_counts, acquire_time_list)
    # logging.info(f'trend = {trend}')
    # ax1.xaxis.set_major_locator(years)
    # ax1.xaxis.set_major_locator(months)
    # ax.xaxis.set_minor_locator(months)
    # ax1.xaxis.set_minor_locator(days)
    events_str: List[str | None] = [None for i in range(len(acquire_time_list))]
    for i, item_d in enumerate(acquire_time_list):
        events_str[i] = item_d.strftime('%Y-%m-%d')
    # ax1.set_xticks(range(len(events_str)))
    # time_format = matplotlib.dates.DateFormatter('%Y-%m-%d')
    # ax1.xaxis.set_major_formatter(time_format)
    logging.info(f'event_str = {events_str}')
    ax1.set_yticks(range(np.min(platform_counts), np.max(platform_counts) + 1))
    ax1.plot(acquire_time_list, platform_counts, linewidth=5, color='red', marker=None, label='油气设施总数量')
    ax1.scatter(anomaly_events, anomaly_counts, facecolors='#FAFA33', edgecolor='black', marker='o', s=200,
                linewidths=1.5,
                zorder=2)

    texts = []
    # for idx, (x, y, date) in enumerate(zip(anomaly_events, anomaly_counts, anomaly_events)):
    #     # month_day = "/".join(date.split('/')[1:])  # 去掉年份部分
    #     logging.info(date)
    #     month_day = date.strftime()
    #     # 根据ID判断奇偶数，调整偏移方向
    #     if (idx+1) % 2 == 0:  # 偶数ID，向左偏移
    #         x_offset = -240
    #         y_offset = 0.12
    #     else:  # 奇数ID，向右偏移
    #         x_offset = 30
    #         y_offset = -0.1
    #
    #     text = ax1.text(x + x_offset, y + y_offset, month_day, fontsize=20, color='#8A2BE2', ha='left', va='center',
    #                     rotation=0,fontweight='bold',
    #                     bbox=dict(facecolor='white', edgecolor='#4169E1', boxstyle='round,pad=0.001', alpha=0))
    #     texts.append(text)

    # ax1.set_title('number of platform')
    # ax1.set_ylabel('数量')
    # ax1.set_yticks(np.arange(min(platform_counts) - 1, max(platform_counts) + 2, 1, dtype=np.intp))
    # ax1.set_ylim(min(platform_counts) - 2.5, max(platform_counts) + 0.5)
    # ax1.plot(acquire_time_list, trend, linewidth=2.5, label='总数量变化趋势')

    one_day = datetime.timedelta(days=1)
    events_1 = acquire_time_list.copy()
    for index, i in enumerate(acquire_time_list):
        j = i - one_day
        events_1[index] = j

    events_2 = acquire_time_list.copy()
    for index, i in enumerate(acquire_time_list):
        j = i + one_day
        events_2[index] = j

    events_1_str: List[str | None] = [None for i in range(len(events_1))]
    for i, item in enumerate(events_1):
        events_1_str[i] = item.strftime('%Y-%m-%d')

    # ax1.scatter(events_str[0], platform_counts[0], marker='o', color='white', edgecolor='red', s=200)
    # ax1.scatter(events_str[1], platform_counts[1], marker='o', color='white', edgecolor='red', s=200)
    # ax1.scatter(events_str[2], platform_counts[2], marker='o', color='white', edgecolor='red', s=200)

    # ax1.scatter(events_str[3], platform_counts[3], marker='o', color='white', edgecolor='green', s=200)
    # ax1.scatter(events_str[5], platform_counts[5], marker='o', color='white', edgecolor='green', s=200)

    # plt.xticks(range(acquire_time_list[0], len(events_str), 1))
    # x_major_locator = plt.MultipleLocator(12)
    # ax1.xaxis.set_major_locator(x_major_locator)
    #  ax1.xaxis.set_major_locator(mdates.DayLocator(interval=12))

    # ax2 = ax1.twinx()
    # occur_count = occur_count[1:-1]
    # disappear_count = disappear_count[1:-1]
    # all_count = np.concatenate((occur_count, disappear_count))
    # ax2.set_yticks(np.arange(0, max(all_count) + 1, 1, dtype=np.intp))
    # ax2.set_ylim(0, max(platform_counts) + 0.5)
    # ax2.plot(acquire_time_list, occur_count, linewidth=2.5, color='red', label='出现数量')
    # ax2.scatter(events_str[0], occur_count[0], marker='o', color='white', edgecolor='red', s=200)
    # ax2.scatter(events_str[1], occur_count[1], marker='o', color='white', edgecolor='red', s=200)
    # ax2.scatter(events_str[2], occur_count[2], marker='o', color='white', edgecolor='red', s=200)
    # ax2.set_ylabel('出现/消失数量')

    # ax2.plot(acquire_time_list, disappear_count, linewidth=2.5, color='green', label='消失数量')
    # ax2.scatter(events_str[3], disappear_count[3], marker='o', color='white', edgecolor='green', s=200)
    # ax2.scatter(events_str[5], disappear_count[5], marker='o', color='white', edgecolor='green', s=200)

    # fig.legend(loc="upper left", bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)
    fig.legend(loc="upper left", bbox_to_anchor=(0.005, 1), bbox_transform=ax1.transAxes)
    plt.show()
