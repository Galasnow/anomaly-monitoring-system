import os
import re
import numpy as np
import cv2
import datetime
import matplotlib.dates
from matplotlib import pyplot as plt
from natsort import natsorted
import time

if __name__ == "__main__":
    # platform_GEE = np.delete([1, 0, 0, 2, 7, 6, 7, 7, 6, 6, 5, 6, 7, 7, 9, 8, 5, 2, 2], -1)
    # platform_S1 = np.delete([6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 7, 7, 7, 7], -1)
    # platform_truth = np.delete([6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 7, 7, 7, 7], -1)


    platform_truth =            np.array(
        [6, 6, 6, 7, 7, 8, 9, 8, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7])
    # platform_GEE_global_1 =     np.array([6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 7, 7, 5, 5, 7, 7, 7]) - platform_truth
    platform_GEE_global_2 =     np.array(
        [6, 6, 6, 7, 7, 8, 9, 8, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 5, 7, 7, 7]) - platform_truth
    platform_GEE_global_2_lee = np.array(
        [6, 6, 6, 7, 7, 8, 9, 8, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7]) - platform_truth
    platform_GEE_global_2_nlm = np.array(
        [6, 6, 6, 7, 7, 8, 9, 8, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7]) - platform_truth

    #platform_GEE_local_006 =    np.array([6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 7, 5, 5, 7, 7, 7]) - platform_truth
    # platform_GEE_local_008 =    np.array([6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 7, 7, 6, 6, 7, 7, 7]) - platform_truth
    # #platform_GEE_local_01_lee = np.array([6, 2, 2, 2, 0, 3, 6, 4, 4, 2, 1, 5, 6, 3, 4, 1, 1, 6, 4, 4, 5, 5, 3]) - platform_truth
    # platform_GEE_local_01_nlm = np.array([6, 6, 6, 6, 7, 7, 6, 6, 7, 7, 7, 7, 7, 7, 8, 8, 7, 7, 6, 6, 7, 6, 6]) - platform_truth
    # platform_S1 =               np.array([6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 7, 7, 7, 7, 7, 7, 7]) - platform_truth


    # x = range(0, len(platform_truth))
    # plt.plot(x, platform_GEE_global_1)
    # #plt.plot(x, platform_GEE_global_2)
    # #plt.plot(x, platform_GEE_local_006)
    # plt.plot(x, platform_GEE_local_008)
    # #plt.plot(x, platform_GEE_local_01_lee)
    # plt.plot(x, platform_GEE_local_01_nlm)
    # plt.plot(x, platform_S1)
    # #plt.plot(x, platform_truth)
    # # plt.legend(['GEE_global_1%', 'GEE_global_2%', 'GEE_local_0.06%', 'GEE_local_0.08%', 'GEE_local_0.1%_lee', 'GEE_local_0.1%_nlm', 'SLC_preprocess', 'truth'])
    # plt.legend(['GEE_global_1%', 'GEE_local_0.08%', 'GEE_local_0.1%_nlm', 'SLC_preprocess'])
    #
    # plt.title('delta number of platform')
    # plt.xticks(np.arange(0, len(platform_truth), 1))
    # plt.xlim(0, len(platform_truth))
    # plt.show()


    # ship_truth =            np.array([2, 9, 5, 7, 5, 5, 11, 1, 16, 4, 6, 0, 4, 0, 4, 0, 2, 4, 8, 1, 7, 2, 0])
    # ship_GEE_global_1 =     np.array([2, 7, 5, 5, 5, 4, 9, 1, 12, 3, 5, 0, 4, 1, 4, 0, 3, 4, 9, 1, 7, 2, 0]) - ship_truth
    # ship_GEE_global_2 =     np.array([2, 7, 5, 5, 5, 5, 9, 1, 12, 3, 6, 0, 4, 1, 4, 0, 3, 6, 11, 1, 7, 2, 0]) - ship_truth
    # ship_GEE_local_006 =    np.array([2, 7, 5, 5, 5, 3, 9, 1, 12, 3, 5, 0, 4, 1, 4, 0, 3, 4, 9, 1, 7, 2, 0]) - ship_truth
    # ship_GEE_local_008 =    np.array([2, 8, 5, 7, 5, 4, 9, 1, 12, 4, 6, 0, 4, 1, 4, 0, 3, 8, 11, 1, 8, 3, 1]) - ship_truth
    # ship_GEE_local_01_lee = np.array([0, 4, 0, 3, 6, 0, 1, 4, 0, 5, 1, 0, 3, 4, 0, 7, 0, 1, 3, 0, 1, 0, 4]) - ship_truth
    # ship_GEE_local_01_nlm = np.array([8, 14, 6, 16, 5, 5, 9, 1, 15, 8, 7, 1, 12, 1, 4, 1, 3, 12, 17, 3, 10, 8, 13]) - ship_truth
    # ship_S1 =               np.array([2, 7, 5, 6, 5, 4, 9, 1, 12, 2, 5, 0, 3, 1, 4, 0, 3, 5, 6, 1, 7, 2, 1]) - ship_truth
    #
    #
    # x = range(0, len(ship_truth))
    #
    #
    # plt.plot(x, ship_GEE_global_1)
    # #plt.plot(x, ship_GEE_global_2)
    # #plt.plot(x, ship_GEE_local_006)
    # plt.plot(x, ship_GEE_local_008)
    # #plt.plot(x, ship_GEE_local_01_lee)
    # plt.plot(x, ship_GEE_local_01_nlm)
    # plt.plot(x, ship_S1)
    # #plt.plot(x, ship_truth)
    # # plt.legend(['GEE_global_1%', 'GEE_global_2%', 'GEE_local_0.06%', 'GEE_local_0.08%', 'GEE_local_0.1%_lee', 'GEE_local_0.1%_nlm', 'SLC_preprocess', 'truth'])
    # plt.legend(['GEE_global_1%', 'GEE_local_0.08%', 'GEE_local_0.1%_nlm', 'SLC_preprocess'])
    # plt.title('delta number of ship')
    # plt.xticks(np.arange(0, len(ship_truth), 1))
    # plt.xlim(0, len(ship_truth))
    # plt.show()

    modify_type = 'GEE_global_2%'
    original_image_path = f'F:/zhongyan/ship_drilling_platform/weizhou/test_compare/{modify_type}/crop'
    ori_list = []
    original_image_names = natsorted(os.listdir(original_image_path))

    pattern = r'1SDV_(.*)T1(.*)T1'

    for ori_image_name in original_image_names:
        stem, _ = os.path.splitext(ori_image_name)
        acquire_time_select = re.search(pattern, stem)
        if acquire_time_select:
            acquire_time = str(acquire_time_select.group(1))
            # logging.info(acquire_time)
            year = int(acquire_time[:4])
            month = int(acquire_time[4:6])
            day = int(acquire_time[6:8])
            # logging.info(year, month, day)
        else:
            raise RuntimeError
        # ori_image = cv2.imread(f'{original_image_path}/{ori_image_name}')
        # ori_w = ori_image.shape[1]
        # ori_h = ori_image.shape[0]
        ori_list.append({'image_original_stem': stem,
                         'image_original_name': ori_image_name,
                         # 'width': ori_w,
                         # 'height': ori_h,
                         'acquire_time': datetime.date(year, month, day)
                         })
    logging.info(len(ori_list))

    events = [ori_list_item['acquire_time'] for ori_list_item in ori_list]
    logging.info(events)
    logging.info(len(events))
    years = matplotlib.dates.YearLocator()
    months = matplotlib.dates.MonthLocator()
    fig, ax = plt.subplots()
    plt.plot(events[1:-1], platform_truth)
    plt.plot(events[1:-1], platform_GEE_global_2)
    plt.plot(events[1:-1], platform_GEE_global_2_lee)
    plt.plot(events[1:-1], platform_GEE_global_2_nlm)
    #plt.plot(events[:-1], platform_GEE_global_2_nlm)
    #plt.plot(events[:-1], platform_GEE_global_2_S1)

    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_minor_locator(months)
    time_format = matplotlib.dates.DateFormatter('%Y-%m')
    ax.xaxis.set_major_formatter(time_format)
    #date_range = matplotlib.dates.drange(events[0], events[-1], )
    data = np.concatenate((platform_truth, platform_GEE_global_2), axis=0)
    plt.yticks(np.arange(min(data) - 1, max(data) + 1, 1))
    plt.ylim(min(data), max(data))

    plt.legend(['truth', 'GEE_global_2 - truth', 'GEE_global_2_lee - truth', 'GEE_global_2_nlm - truth'])

    plt.title('number of platform')
    plt.show()