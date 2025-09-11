import datetime
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
    output_shp_path_disappear, output_shp_path_occur_and_disappear, output_shp_path_by_day, output_stem_path, \
    support_file_list
from utils import *
from util.labels import *

mpl.rcParams.update({'font.size': 18,
                     'font.family': 'Microsoft YaHei',
                     'mathtext.fontset': 'stix'})
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


def round_day(dt: datetime.timedelta | None = None):
    if dt.seconds >= 12 * 3600:
        return dt.days + 1
    else:
        return dt.days


def write_csv(content, csv_file_path, head=None):
    with open(csv_file_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if head is not None:
            writer.writerow(head)
        # for row in content:
        #     row_content = list(row.values())[1:]
        #     writer.writerow(row_content)
        writer.writerows(content)


def calculate_size_score(size):
    # 300: 1
    if size >= 0:
        if size <= 60:
            score = size / 60.0
        else:
            score = 1.0
    else:
        raise RuntimeError('size must >= 0')
    return score


def calculate_time_score(days: int):
    # 0: 0.02, 50: 1
    if days >= 0:
        if days <= 9:
            score = days / 9.0
        else:
            score = 1.0
    else:
        raise RuntimeError('stay days must >= 0')
    return score


def calculate_iou_score(iou_list: Sequence | np.ndarray):
    if any(iou_list) < 0:
        raise RuntimeError('IOU must >= 0')
    exponent = 1 / 2.0
    score = np.mean(np.pow(iou_list, exponent))
    return score


if __name__ == "__main__":
    # a = 14
    # matr = [[i, i+1, i+2, i+3, i+4] for i in (range(5, 200, 5))]
    # print(matr)
    # print(matr.index(a))
    initial_logging_formatter()
    original_image_list = build_sorted_sentinel_1_list(original_image_path)
    original_image_name_list = [original_image.filename for original_image in original_image_list]

    # logging.info(f'{len(original_image_list) = }')
    original_image_list.pop(0)
    original_image_list.pop(-1)
    acquire_time_list = [ori_list_item.acquire_time for ori_list_item in original_image_list]

    result_list = []
    max_platform_id = 0
    for i in range(len(original_image_list)):
        result = read_txt_label(f'{modified_label_path}/{original_image_list[i].filename_stem}.txt')
        result[..., 1:5] = yolo2number(original_image_list[i].shape, result[..., 1:5])
        result_list.append(result)
        if len(result) != 0:
            max_platform_id = int(np.max((np.max(result[..., -1]), max_platform_id)))
    print(f'{len(result_list) = }')
    logging.info(f'{max_platform_id = }')
    # logging.info(f'{result_list =}')
    # logging.info(len(result_list))
    platform_coordinates_by_id = get_platform_ship_coordinates_by_id_final(result_list, original_image_list,
                                                                           max_platform_id)

    platform_coordinates_by_day, ship_coordinates_by_day = get_platform_ship_coordinates_by_day_final(result_list,
                                                                                                      original_image_list)

    # logging.info(f'{platform_coordinates_by_id =}')
    platform_geo_location = np.asarray(
        [[platform_coordinates['obj_id'], platform_coordinates['geo_center_x'], platform_coordinates['geo_center_y']]
         for
         platform_coordinates in platform_coordinates_by_id])
    # logging.info(f'{platform_geo_location = }')
    # platform_sizes = get_platform_sizes(result_list, max_platform_id)
    platform_sizes = np.asarray([[platform_coordinates['obj_id'],
                                  platform_coordinates['average_size_x'],
                                  platform_coordinates['average_size_y']] for
                                 platform_coordinates in platform_coordinates_by_id])
    # logging.info(f'{platform_sizes = }')

    platform_annotations = [[np.array([]) for j in range(len(original_image_list))] for i in range(max_platform_id)]
    platform_lifetime = np.zeros((max_platform_id, len(original_image_list)), dtype=np.bool)
    # logging.info(f'{result_list = }')
    for i in range(max_platform_id):
        for j in range(len(original_image_list)):
            select_array = result_list[j]
            if len(select_array) != 0:
                platform_annotations[i][j] = result_list[j][np.where(result_list[j][..., -1] == i + 1)]
                platform_lifetime[i][j] = True if (platform_annotations[i][j].size != 0) else False
    platform_ious = [[np.array([]) for j in range(len(original_image_list))] for i in range(max_platform_id)]
    for i in range(max_platform_id):
        # print(i)
        platform_i_bboxes_array = np.asarray(
            [item[..., 1:5] for item in platform_annotations[i] if len(item) != 0]).squeeze()
        # print(platform_i_bboxes_array)
        if platform_i_bboxes_array.ndim < 2:
            platform_i_bboxes_array = np.concatenate(
                (np.reshape(platform_i_bboxes_array, (1, 4)), np.reshape(platform_i_bboxes_array, (1, 4))), axis=0)
        platform_ious[i] = [calculate_iou(platform_i_bboxes_array[i], platform_i_bboxes_array[i + 1]) for i in
                            range(len(platform_i_bboxes_array) - 1)]
        # calculate_iou()
        # print(platform_ious[i])

    # iou_scores =
    iou_scores = [calculate_iou_score(platform_ious[i]) for i in range(max_platform_id)]
    # print(iou_scores)

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
    # logging.info(platform_geo_location_occur)
    # logging.info(platform_geo_location_occur_and_disappear)

    occur_array = []
    disappear_array = []
    for i in range(len(platform_geo_location_occur[..., 0])):
        id_i = int(platform_geo_location_occur[..., 0][i])
        time_line = platform_lifetime[id_i - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == False and time_line[w + 1] == True:
                occur_array.append(
                    [acquire_time_list[w + 1], platform_geo_location_occur[i][1], platform_geo_location_occur[i][2],
                     id_i])

    for i in range(len(platform_geo_location_disappear[..., 0])):
        id_i = int(platform_geo_location_disappear[..., 0][i])
        time_line = platform_lifetime[id_i - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == True and time_line[w + 1] == False:
                disappear_array.append(
                    [acquire_time_list[w + 1], platform_geo_location_disappear[i][1],
                     platform_geo_location_disappear[i][2], id_i])

    for i in range(len(platform_geo_location_occur_and_disappear[..., 0])):
        id_i = int(platform_geo_location_occur_and_disappear[..., 0][i])
        time_line = platform_lifetime[id_i - 1, ...]
        for w in range(len(time_line) - 1):
            if time_line[w] == False and time_line[w + 1] == True:
                occur_array.append([acquire_time_list[w + 1], platform_geo_location_occur_and_disappear[i][1],
                                    platform_geo_location_occur_and_disappear[i][2], id_i])
            if time_line[w] == True and time_line[w + 1] == False:
                disappear_array.append([acquire_time_list[w + 1], platform_geo_location_occur_and_disappear[i][1],
                                        platform_geo_location_occur_and_disappear[i][2], id_i])

    # logging.info(f'{np.array(occur_array) = }')
    # logging.info(f'{np.array(disappear_array) = }')
    occur_counts = np.zeros_like(acquire_time_list, dtype=np.intp)
    disappear_counts = np.zeros_like(acquire_time_list, dtype=np.intp)

    for item in occur_array:
        acquire_time = item[0]
        index = acquire_time_list.index(acquire_time)
        # print(index)
        # print(f'{occur_counts = }')
        occur_counts[index] += 1
    for item in disappear_array:
        acquire_time = item[0]
        index = acquire_time_list.index(acquire_time)
        disappear_counts[index] += 1
    # logging.info(f'{occur_counts = }')
    # logging.info(f'{disappear_counts = }')
    # logging.info(f'platform_geo_location_occur = {platform_geo_location_occur}')

    # special_array = search_special_events(occur_array, disappear_array, platform_geo_location)

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

    time_table: List[List[datetime.date | None]] = [[None, None] for _ in range(max_platform_id)]
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

    # platform_counts = [np.sum(result_list[i][..., 0] == 2) for i in range(len(original_image_list)) if
    #                    len(result_list[i]) != 0]
    platform_counts = np.zeros((len(original_image_list)), dtype=np.intp)
    for i in range(len(original_image_list)):
        if len(result_list[i]) != 0:
            platform_counts[i] = np.sum(result_list[i][..., 0] == 2)
        else:
            platform_counts[i] = 0
    anomaly_events = acquire_time_list.copy()
    no_anomaly_index = [0]
    anomaly_index = np.zeros(len(platform_counts))
    anomaly_counts = platform_counts.copy()
    # anomaly_count_need = list(range(5, 200, 5))
    def find_first_range_index(arr):
        """
        查找数组中第一个满足 [n, n+4] (n>0) 范围的元素索引

        参数:
            arr (list): 整数数组

        返回:
            int: 第一个满足条件的元素索引，如果没有则返回 -1
        """
        for i, num in enumerate(arr):
            if num > 0:
                n = (num // 5) * 5  # 计算基准n (5的倍数)
                if n > 0 and num <= n + 4:
                    return i
        return -1
    anomaly_count_need_2d = [[i, i+1, i+2, i+3, i+4] for i in (range(5, 130, 5))]
    # anomaly_count_need_1d = np.reshape(anomaly_count_need_2d, -1)
    for i in range(1, len(platform_counts) - 1):
        anomaly_exist = False
        for j in range(len(anomaly_count_need_2d)):
            print(f'{anomaly_count_need_2d[j] = }')
            if platform_counts[i] in anomaly_count_need_2d[j]:
                anomaly_index[i] = 1
                anomaly_count_need_2d.pop(j)
                print(f'{anomaly_count_need_2d = }')
                anomaly_exist = True
                break
        if not anomaly_exist:
            no_anomaly_index.append(i)

    no_anomaly_index.append(len(platform_counts) - 1)
    anomaly_events = np.delete(anomaly_events, no_anomaly_index)
    anomaly_counts = np.delete(anomaly_counts, no_anomaly_index)
    print(f'{no_anomaly_index = }')
    output_csv_file = f'{output_stem_path}/platform_number.csv'
    with open(output_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['date', 'number', 'anomaly'])
        writer.writeheader()
        for i in range(len(platform_counts)):
            row = {'date': acquire_time_list[i].strftime("%Y/%m/%d"), 'number': platform_counts[i],
                   'anomaly': anomaly_index[i]}
            writer.writerow(row)

    content = [list(row.values())[1:] for day_item in platform_coordinates_by_day for row in day_item]
    content.sort(key=lambda x: x[0])
    content = np.asarray(content)
    # content[..., [0, 1]] = content[..., [1, 0]]
    # print(f'{content[0] = }')
    output_details_csv_file = f'{output_stem_path}/platform_summary_by_id.csv'
    head = ['id', 'date',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']
    write_csv(content, output_details_csv_file, head)

    content = [list(row.values())[1:] for day_item in platform_coordinates_by_day for row in day_item]
    content = np.asarray(content)
    content[..., [0, 1]] = content[..., [1, 0]]
    output_details_csv_file = f'{output_stem_path}/platform_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_details_csv_file, head)

    content = [list(row.values())[1:] for day_item in ship_coordinates_by_day for row in day_item]
    content = np.asarray(content)
    content[..., [0, 1]] = content[..., [1, 0]]
    output_details_csv_file = f'{output_stem_path}/ship_summary_by_date.csv'
    head = ['date', 'id',
            'image_x_center', 'image_y_center',
            'image_x_min', 'image_y_min', 'image_x_max', 'image_y_max',
            'geo_x_center', 'geo_y_center',
            'geo_x_min', 'geo_y_min', 'geo_x_max', 'geo_y_max']

    write_csv(content, output_details_csv_file, head)

    output_summary_csv_file = f'{output_stem_path}/occur.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['type', 'date', 'geo_x_center', 'geo_y_center', 'id'])
        writer.writeheader()
        for item in occur_array:
            # if platform_sizes[item[3] - 1, 0] * platform_sizes[item[3] - 1, 1] * 10 * 10 >= 50:
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
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）

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
    spatial_ref.ImportFromEPSG(target_epsg)  # 使用WGS84坐标系（EPSG:4326）

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

    # output_summary_csv_file = f'{output_stem_path}/special.csv'
    # with open(output_summary_csv_file, mode='w', newline='') as csv_file:
    #     writer = csv.DictWriter(csv_file,
    #                             fieldnames=['date_occur', 'date_disappear', 'geo_x_center', 'geo_y_center', 'id'])
    #     writer.writeheader()
    #     ############## filter area
    #     for item in special_array:
    #         row = {'date_occur': item[0], 'date_disappear': item[1],
    #                'geo_x_center': item[2],
    #                'geo_y_center': item[3],
    #                'id': item[4]
    #                }
    #         writer.writerow(row)
    #
    # output_shapefile = f'{output_stem_path}/special_events'
    # target_epsg = 4326
    # driver = ogr.GetDriverByName('ESRI Shapefile')
    # if os.path.exists(output_shapefile):
    #     driver.DeleteDataSource(output_shapefile)
    # data_source = driver.CreateDataSource(output_shapefile)
    # spatial_ref = osr.SpatialReference()
    # spatial_ref.ImportFromEPSG(target_epsg)
    #
    # # 创建图层
    # layer_name = 'special_events'
    # layer = data_source.CreateLayer(layer_name, spatial_ref, ogr.wkbPoint)
    # layer_defn = layer.GetLayerDefn()
    # # logging.info(layer_defn)
    # fieldDefn = ogr.FieldDefn('DATE_1', ogr.OFTString)
    # # fieldDefn.SetWidth(10)
    # layer.CreateField(fieldDefn)
    # fieldDefn = ogr.FieldDefn('DATE_2', ogr.OFTString)
    # # fieldDefn.SetWidth(10)
    # layer.CreateField(fieldDefn)
    #
    # fieldDefn = ogr.FieldDefn('PLATFORM', ogr.OFTString)
    # layer.CreateField(fieldDefn)
    #
    # # 添加点要素
    # for date_occur, date_disappear, lon, lat, platform in special_array:
    #     point = ogr.Geometry(ogr.wkbPoint)
    #     point.AddPoint(lon, lat)
    #     feature = ogr.Feature(layer_defn)
    #
    #     date_occur_str = datetime.datetime.strftime(date_occur, '%Y-%m-%d')
    #     date_disappear_str = datetime.datetime.strftime(date_disappear, '%Y-%m-%d')
    #
    #     feature.SetField('DATE_1', date_occur_str)  # 设置属性字段
    #     feature.SetField('DATE_2', date_disappear_str)  # 设置属性字段
    #     feature.SetField('PLATFORM', platform)  # 设置属性字段
    #     feature.SetGeometry(point)
    #     layer.CreateFeature(feature)

    # days_list = np.asarray([(time_table[i][1] - time_table[i][0]).days for i in range(max_platform_id)])
    days_list = np.asarray([round_day(time_table[i][1] - time_table[i][0]) for i in range(max_platform_id)])
    time_score_list = np.asarray([calculate_time_score(round_day(time_table[i][1] - time_table[i][0])) for i in range(max_platform_id)])
    size_score_list = np.asarray([calculate_size_score(platform_sizes[i][1] * platform_sizes[i][2]) for i in
                       range(max_platform_id)])
    logging.info(f'{size_score_list = }')
    p1_score_list = np.asarray([iou_scores[i] * time_score_list[i] for i in range(max_platform_id)])
    p_score_list = np.asarray([iou_scores[i] * time_score_list[i] * size_score_list[i] for i in range(max_platform_id)])

    # platform_geo_location_high_conf = platform_geo_location[np.where(p_score_list >= 0)]
    # # print(f'{platform_geo_location_high_conf = }')
    # days_list_high_conf = days_list[np.where(p_score_list >= 0)]
    # p_score_list_high_conf = p_score_list[np.where(p_score_list >= 0)]

    time_table_array = np.asarray(time_table)
    platform_geo_location_stable = platform_geo_location[
        np.where(days_list == np.max(days_list))]
    # print(platform_geo_location_stable)
    days_list_stable = days_list[np.where(days_list == np.max(days_list))]

    size_score_list_stable = size_score_list[np.where(days_list == np.max(days_list))]
    p1_score_list_stable = p1_score_list[np.where(days_list == np.max(days_list))]
    p_score_list_stable = p_score_list[np.where(days_list == np.max(days_list))]

    time_table_stable = time_table_array[np.where(days_list == np.max(days_list))]
    platform_lifetime_stable = platform_lifetime[np.where(days_list == np.max(days_list))]
    platform_sizes_stable = platform_sizes[np.where(days_list == np.max(days_list))]

    platform_geo_location_move = platform_geo_location[
        np.where(days_list < np.max(days_list))]
    # print(platform_geo_location_move)
    days_list_move = days_list[np.where(days_list < np.max(days_list))]

    size_score_list_move = size_score_list[np.where(days_list < np.max(days_list))]
    p1_score_list_move = p1_score_list[np.where(days_list < np.max(days_list))]
    p_score_list_move = p_score_list[np.where(days_list < np.max(days_list))]
    time_table_move = time_table_array[np.where(days_list < np.max(days_list))]
    platform_lifetime_move = platform_lifetime[np.where(days_list < np.max(days_list))]
    platform_sizes_move = platform_sizes[np.where(days_list < np.max(days_list))]

    output_summary_csv_file = f'{output_stem_path}/platform_frequency.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'p1_score', 'size_score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime[i]),
                   'days': round_day(time_table[i][1] - time_table[i][0]),
                   'first_time': time_table[i][0],
                   'last_time': time_table[i][1],
                   'size': platform_sizes[i][1] * platform_sizes[i][2],
                   'p1_score': p1_score_list[i],
                   'size_score': size_score_list[i]
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
    fieldDefn = ogr.FieldDefn('P1_Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size_Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id_i, lon, lat] in enumerate(platform_geo_location):
        # print(calculate_time_score(round_day(time_table[i][1] - time_table[i][0])) * calculate_size_score(
        #     platform_sizes[i][1] * platform_sizes[i][2]) * iou_scores[i])
        # print(type(calculate_time_score(round_day(time_table[i][1] - time_table[i][0])) * calculate_size_score(
        #     platform_sizes[i][1] * platform_sizes[i][2]) * iou_scores[i]))
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime[i])))  # 设置属性字段
        feature.SetField('First_time', time_table[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', round_day(time_table[i][1] - time_table[i][0]))  # 设置属性字段
        feature.SetField('Size', platform_sizes[i][1] * platform_sizes[i][2])  # 设置属性字段
        feature.SetField('P1_Score',
                         p1_score_list[i])  # 设置属性字段
        feature.SetField('Size_Score',
                         size_score_list[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_stable.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'p1_score', 'size_score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_stable):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime_stable[i]),
                   'days': round_day(time_table[i][1] - time_table[i][0]),
                   'first_time': time_table_stable[i][0],
                   'last_time': time_table_stable[i][1],
                   'size': platform_sizes_stable[i][1] * platform_sizes_stable[i][2],
                   'p1_score': p1_score_list_stable[i],
                   'size_score': size_score_list_stable[i]
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
    fieldDefn = ogr.FieldDefn('P1_Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size_Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id_i, lon, lat] in enumerate(platform_geo_location_stable):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime_stable[i])))  # 设置属性字段
        feature.SetField('First_time', time_table_stable[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table_stable[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_stable[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes_stable[i][1] * platform_sizes_stable[i][2])  # 设置属性字段
        feature.SetField('P1_Score',
                         p1_score_list_stable[i])  # 设置属性字段
        feature.SetField('Size_Score',
                         size_score_list_stable[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    output_summary_csv_file = f'{output_stem_path}/platform_frequency_move.csv'
    with open(output_summary_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=['id', 'geo_x_center', 'geo_y_center', 'frequency', 'days', 'first_time',
                                            'last_time', 'size', 'p1_score', 'size_score'])
        writer.writeheader()
        ############## filter area
        for i, item in enumerate(platform_geo_location_move):
            row = {'id': item[0],
                   'geo_x_center': item[1],
                   'geo_y_center': item[2],
                   'frequency': np.sum(platform_lifetime_move[i]),
                   'days': round_day(time_table[i][1] - time_table[i][0]),
                   'first_time': time_table_move[i][0],
                   'last_time': time_table_move[i][1],
                   'size': platform_sizes_move[i][1] * platform_sizes_move[i][2],
                   'p1_score': p1_score_list_move[i],
                   'size_score': size_score_list_move[i]
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
    fieldDefn = ogr.FieldDefn('P1_Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    fieldDefn = ogr.FieldDefn('Size_Score', ogr.OFTReal)
    layer.CreateField(fieldDefn)
    # 添加点要素
    for i, [id_i, lon, lat] in enumerate(platform_geo_location_move):
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature = ogr.Feature(layer_defn)
        feature.SetField('Frequency', int(np.sum(platform_lifetime_move[i])))  # 设置属性字段
        feature.SetField('First_time', time_table_move[i][0].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Last_time', time_table_move[i][1].strftime("%Y-%m-%d"))  # 设置属性字段
        feature.SetField('Days', int(days_list_move[i]))  # 设置属性字段
        feature.SetField('Size', platform_sizes_move[i][1] * platform_sizes_move[i][2])  # 设置属性字段
        feature.SetField('P1_Score',
                         p1_score_list_move[i])  # 设置属性字段
        feature.SetField('Size_Score',
                         size_score_list_move[i])  # 设置属性字段
        feature.SetGeometry(point)
        layer.CreateFeature(feature)

    ship_counts = [np.sum(result_list[i][..., 0] == 1) for i in range(len(original_image_list)) if
                   len(result_list[i]) != 0]
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

    # acquire_time_list.pop(0)
    # acquire_time_list.pop(-1)
    occur_counts = list(occur_counts)
    disappear_counts = list(disappear_counts)
    # occur_counts.pop(0)
    # occur_counts.pop(-1)
    # disappear_counts.pop(0)
    # disappear_counts.pop(-1)

    # platform_counts = platform_counts[1:-1]
    fig, ax1 = plt.subplots()
    # fig.autofmt_xdate(rotation=25)

    # trend = generate_trend_by_date(platform_counts, acquire_time_list)
    # logging.info(f'trend = {trend}')

    # ax1.xaxis.set_major_locator(years)
    # ax1.xaxis.set_major_locator(months)
    # ax.xaxis.set_minor_locator(months)
    # ax1.xaxis.set_minor_locator(days)
    print(f'{platform_counts = }')
    print(f'{acquire_time_list = }')
    print(f'{len(platform_counts) = }')
    print(f'{len(acquire_time_list) = }')
    events_str: List[str | None] = [None for i in range(len(acquire_time_list))]
    for i, item_d in enumerate(acquire_time_list):
        events_str[i] = item_d.strftime('%Y-%m-%d')
    # ax1.set_xticks(range(len(events_str)))
    # time_format = matplotlib.dates.DateFormatter('%Y-%m-%d')
    # ax1.xaxis.set_major_formatter(time_format)
    logging.info(f'event_str = {events_str}')

    ax1.set_yticks(range(np.min(platform_counts), np.max(platform_counts) + 1, 10))
    full_counts = occur_counts + disappear_counts
    # ax1.set_yticks(range(np.min(full_counts), np.max(full_counts) + 1))
    # ax1.set_ylim(np.min(full_counts), np.max(full_counts) + 1)
    ax1.set_xlabel('日期')
    ax1.set_ylabel('固定设施总数量')
    # ax1.set_ylabel('异常数量')
    ax1.plot(acquire_time_list, platform_counts, linewidth=2, color='red', marker='o', markersize=2)
    # ax1.plot(acquire_time_list, platform_counts, linewidth=2, color='steelblue', marker=None)
    # ax1.plot(acquire_time_list, occur_counts, linewidth=3, color='red', marker=None, label='异常出现')
    # ax1.plot(acquire_time_list, disappear_counts, linewidth=3, color='blue', marker=None, label='异常消失')
    ax1.scatter(anomaly_events, anomaly_counts, facecolors='#FAFA33', edgecolor='black', marker='o', s=200,
                linewidths=1.5,
                zorder=2)

    for idx, (x, y, date) in enumerate(zip(anomaly_events, anomaly_counts, anomaly_events)):
        # month_day = "/".join(date.split('/')[1:])  # 去掉年份部分
        # logging.info(date)
        year_month_day = date.strftime('%Y-%m-%d').split('-')
        month_day = f'{year_month_day[1]}/{year_month_day[2]}'
        # 根据ID判断奇偶数，调整偏移方向
        if (idx + 1) % 2 == 0:  # 偶数ID，向左偏移
            # x_offset = -datetime.timedelta(days=3)
            x_offset = datetime.timedelta(days=0)
            y_offset = 0.1
        else:  # 奇数ID，向右偏移
            # x_offset = datetime.timedelta(days=2)
            x_offset = datetime.timedelta(days=0)
            y_offset = -0.1

        # text = ax1.text(x + x_offset, y + y_offset, month_day, fontsize=16, color='#8A2BE2', ha='left', va='center',
        #                 rotation=0, fontweight='bold',
        #                 bbox=dict(facecolor='white', edgecolor='#4169E1', boxstyle='round,pad=0.001', alpha=0))

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

    # fig.legend(loc="upper right", bbox_to_anchor=(0.995, 1), bbox_transform=ax1.transAxes)
    # fig.legend()
    fig = plt.gcf()
    fig.set_size_inches(16, 8)
    plt.savefig(
        f'{output_stem_path}/summarize_platform.png', dpi=600, bbox_inches='tight')
    plt.show()
    plt.close()

    from brokenaxes import brokenaxes
    days_range = sorted(np.unique(days_list))
    print(f'{days_range = }')
    print(f'{days_list = }')
    print(f'{np.where(days_list == 6) = }')
    days_count = np.zeros_like(days_range)
    for i, item in enumerate(days_range):
        days_count[i] = len(np.where(days_list == item)[0])
    print(f'{days_count = }')

    # bax = brokenaxes(xlims=((0, 70), (150, 160), (1670, 1690), (3140, 3150), (3700, 3710)),  # 设置x轴裂口范围
    #                  # ylims=((0, 0.28), (0.4, 2)),  # 设置y轴裂口范围
    #                  # hspace=0.25,  # y轴裂口宽度
    #                  wspace=0.1,  # x轴裂口宽度
    #                  despine=True,  # 是否y轴只显示一个裂口
    #                  diag_color='r',  # 裂口斜线颜色
    #                  d=0.01,
    #                  )
    # bax.bar(days_range, days_count, width=4)
    fig = plt.gcf()
    fig.set_size_inches(16, 8)
    days_range_str = [str(item) for item in days_range]
    print(f'{days_range_str = }')
    # plt.xticks(days_range, labels=days_range_str)
    plt.xlabel('停留天数')
    plt.ylabel('数量')
    plt.subplots_adjust(wspace=0)
    plt.bar(days_range_str, days_count, width=0.8, color='darkgray')

    plt.savefig(
        f'{output_stem_path}/summarize_platform_days.png', dpi=600, bbox_inches='tight')

    plt.show()