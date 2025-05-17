import datetime
import logging

import numpy as np
from matplotlib import pyplot as plt

from verify_platform_by_surface_temperature import read_csv
import matplotlib as mpl
mpl.rcParams.update({'font.size': 20,
                     'font.family': 'Microsoft YaHei',
                     'mathtext.fontset': 'stix'})
if __name__ == "__main__":
    out_record_temperature_csv_file = r'/datasets/test_set/malaysia_wenlai/temperature_verify.csv'
    all_u = np.asarray(read_csv(out_record_temperature_csv_file))
    ids = all_u[..., 0]
    ids = np.unique(ids)
    for j in ids:
        new_u = all_u[all_u[..., 0] == j, 1:5]
        # logging.info(new_u)
        date_list = [datetime.datetime.strptime(new_u[i, 0], '%Y-%m-%d %H:%M:%S') for i in range(len(new_u[..., 0]))]
        logging.info(date_list)

        center_list_valid = np.asarray(new_u[..., 1], dtype=np.float32)
        periphery_list_valid = np.asarray(new_u[..., 2], dtype=np.float32)
        delta_list_valid = np.asarray(new_u[..., 3], dtype=np.float32)
        logging.info(center_list_valid)
        logging.info(periphery_list_valid)
        mark_list = np.where(center_list_valid > periphery_list_valid)[0]
        logging.info(mark_list)
        if len(mark_list) == 0:
            mark_list = None
        logging.info(mark_list)
        plt.plot(date_list, center_list_valid, linewidth=2, color='red', marker='o', label='center', markevery=mark_list)
        plt.plot(date_list, periphery_list_valid, linewidth=2, color='blue', marker=None, label='periphery')

        plt.ylabel('Top 10% to 50% temperature / °C')
        plt.xlabel('date')
        plt.legend()
        fig = plt.gcf()
        fig.set_size_inches(16, 9)
        # plt.figure(figsize=(16, 9))

        # gcf: Get Current Figure
        # fig = plt.gcf()

        plt.savefig(
            f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_verify_result/{j}_test_top_10_to_50_temperature.png',
            dpi=200, bbox_inches='tight')
        plt.close()

        # plt.plot(time_datetime_list_valid, delta_list_valid, linewidth=2.5, marker='o', label='temperature')
        plt.plot(date_list, delta_list_valid, linewidth=2, color='green', marker='o',
                 label='center - periphery', markevery=mark_list)
        plt.axhline(y=0, color='orange', linestyle='--')

        plt.ylabel('Delta top 10% to 50% temperature  / °C')
        plt.xlabel('date')

        plt.legend()
        fig = plt.gcf()
        fig.set_size_inches(16, 9)

        plt.savefig(
            f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_verify_result/{j}_test_delta_top_10_to_50_temperature.png',
            dpi=200, bbox_inches='tight')
        plt.close()