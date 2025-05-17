import numpy as np
import matplotlib
from matplotlib import pyplot as plt

from summarize_platform import calculate_size_score, calculate_time_score

matplotlib.rcParams.update({'font.size': 18,
                     'font.family': 'Microsoft YaHei',
                     'mathtext.fontset': 'stix'})
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

if __name__ == "__main__":
    x = np.arange(0, 350, 1)
    y = np.zeros_like(x, dtype=np.float32)
    for i, item in enumerate(x):
        y[i] = calculate_size_score(item)
    plt.plot(x, y)
    plt.xlabel('size ($\\times$100m$^{2}$)')
    plt.ylabel('size_score')
    plt.xlim([0, 350])
    plt.xticks([0, 300])
    plt.ylim([0, 1.1])
    plt.yticks([0, 1])

    horizontal_mark_line_x = np.arange(0, 300, 1)
    horizontal_mark_line_y = np.full_like(horizontal_mark_line_x, 1)
    plt.plot(horizontal_mark_line_x, horizontal_mark_line_y, linestyle='--', color='green')

    vertical_mark_line_y = np.linspace(0, 1, 100)
    vertical_mark_line_x = np.full_like(vertical_mark_line_y, 300)
    plt.plot(vertical_mark_line_x, vertical_mark_line_y, linestyle='--', color='green')

    fig = plt.gcf()
    fig.set_size_inches(8, 5)

    plt.savefig(
        f'D:/组会/score_function.png',
        dpi=300, bbox_inches='tight')
    plt.show()

    plt.close()

    x = np.arange(0, 60, 1)
    y = np.zeros_like(x, dtype=np.float32)
    for i, item in enumerate(x):
        y[i] = calculate_time_score(item)
    plt.plot(x, y)
    plt.xlabel('stay days')
    plt.ylabel('time_score')
    plt.xlim([0, 60])
    plt.xticks([0, 50])
    plt.ylim([0, 1.1])
    plt.yticks([0, 1])

    horizontal_mark_line_x = np.arange(0, 50, 1)
    horizontal_mark_line_y = np.full_like(horizontal_mark_line_x, 1)
    plt.plot(horizontal_mark_line_x, horizontal_mark_line_y, linestyle='--', color='green')

    vertical_mark_line_y = np.linspace(0, 1, 100)
    vertical_mark_line_x = np.full_like(vertical_mark_line_y, 50)
    plt.plot(vertical_mark_line_x, vertical_mark_line_y, linestyle='--', color='green')

    fig = plt.gcf()
    fig.set_size_inches(8, 5)

    plt.savefig(
        f'D:/组会/time_function.png',
        dpi=300, bbox_inches='tight')
    plt.show()
    plt.close(