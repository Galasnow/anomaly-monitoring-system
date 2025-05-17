import datetime
import logging

import numpy as np
from matplotlib import pyplot as plt

if __name__ == "__main__":
    new_u = np.array(
        [[datetime.date(2024, 9, 3), 29.2883358001709, 30.129358291625977, -0.841022789478302],
         [datetime.date(2024, 11, 14), 27.616924285888672, 33.43302536010742, -5.816102981567383],
         [datetime.date(2024, 12, 8), 27.592998504638672, 26.50196647644043, 1.0910320281982422]])

    logging.info(f'sorted result = {new_u}')

    plt.plot(new_u[..., 0], new_u[..., 1], linewidth=2, color='red', marker='o', label='center')
    plt.plot(new_u[..., 0], new_u[..., 2], linewidth=2, color='blue', marker='o', label='periphery')
    # plt.axhline(y=2, color='yellow', label='reference threshold line')
    plt.ylabel('Top 10% to 50% temperature / °C')
    plt.xlabel('date')
    plt.legend()
    fig = plt.gcf()
    fig.set_size_inches(16, 9)
    # plt.figure(figsize=(16, 9))

    # gcf: Get Current Figure
    # fig = plt.gcf()

    plt.savefig(
        f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_verify_result/1_test_top_10_to_50_temperature.png', dpi=200, pad_inches=0.01)
    plt.close()

    # plt.plot(time_datetime_list_valid, delta_list_valid, linewidth=2.5, marker='o', label='temperature')
    plt.plot(new_u[..., 0], new_u[..., 3], linewidth=2, color='green', marker='o',
             label='center - periphery')
    # plt.axhline(y=2, color='yellow', label='reference threshold line')
    plt.ylabel('Delta top 10% to 50% temperature  / °C')
    plt.xlabel('date')

    plt.legend()
    fig = plt.gcf()
    fig.set_size_inches(16, 9)

    plt.savefig(
        f'H:/zhongyan/ship_drilling_platform/predict_platform/datasets/test_set/malaysia_wenlai/platform_verify_result/1_test_delta_top_10_to_50_temperature.png', dpi=200, pad_inches=0.01)
