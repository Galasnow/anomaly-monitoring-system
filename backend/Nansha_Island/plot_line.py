# import matplotlib.pyplot as plt
# import pandas as pd
# from datetime import datetime
# import matplotlib as mpl
# import math
# from adjustText import adjust_text
#
# mpl.style.use('classic')
# mpl.rcParams.update({'font.size': 16,
#                      'font.family': 'Microsoft YaHei',
#                      'mathtext.fontset': 'stix'})
# plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
# mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
#
#
# def cal_DOY_from_start(start_date, target_date):
#     """
#     计算从指定开始日期(start_date)到目标日期(target_date)的累积天数（DOY）。
#     """
#     start_date = datetime.strptime(start_date, '%Y/%m/%d')
#     target_date = datetime.strptime(target_date, '%Y/%m/%d')
#     delta = target_date - start_date
#     return delta.days + 1
#
#
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
#     ax1.set_ylabel('面积 (km$\\mathrm{^2}$)', fontsize=22)
#     ax1.set_xlabel('日期', fontsize=22)
#
#     # 标记异常日期
#     ax1.scatter(anomaly_doys, anomaly_areas, facecolors='#FAFA33', edgecolor='black', marker='o', s=200, linewidths=1.5,
#                 zorder=2)
#
#     # 标注异常日期，根据ID（索引）判断奇偶数，设置不同的偏移量
#     texts = []
#     for idx, (x, y, date) in enumerate(zip(anomaly_doys, anomaly_areas, anomaly_dates)):
#         # month_day = "/".join(date.split('/')[1:])  # 去掉年份部分
#         # 分割日期并补零
#         parts = date.split('/')
#         month_day = f"{parts[1].zfill(2)}/{parts[2].zfill(2)}"  # 保留两位的月份和日期
#
#         # 根据ID判断奇偶数，调整偏移方向
#         if (idx+1) % 2 == 0:  # 偶数ID，向左偏移
#             x_offset = -180
#             y_offset = 0.02
#         else:  # 奇数ID，向右偏移
#             x_offset = 40
#             y_offset = 0
#
#         text = ax1.text(x + x_offset, y + y_offset, month_day, fontsize=12, color='#8A2BE2', ha='left', va='center',
#                         rotation=0, fontweight='bold',
#                         bbox=dict(facecolor='white', edgecolor='#4169E1', boxstyle='round,pad=0.001', alpha=0))
#         texts.append(text)
#
#     # 使用adjustText库自动调整文本位置
#     adjust_text(texts)
#
#     ax1.axes.xaxis.set_ticklabels(
#         ["2016/1", "2017/1", "2018/1", "2019/1", "2020/1", "2021/1", "2022/1", "2023/1", "2024/1", "2025/1"])
#
#     y_max = max(area) * 1.1
#     y_min = math.floor(min(area))
#     ax1.set_ylim([y_min, y_max])
#     ax1.set_xlim([0, 3288])
#
#     plt.yticks(fontsize=18)
#     plt.xticks(fontsize=18)
#
#     # 保存或显示图像
#     if area_line:
#         plt.savefig(area_line, bbox_inches='tight')
#     else:
#         plt.show()
#
# main_dir = r"E:\personal file\00Zhongyan\00Nansha\Nansha_Island\01_Baijiao/"
# area_result = main_dir + r"Baijiao_Area.csv"
# line_result = main_dir + r"Baijiao_Area3.png"
# accuracy_csv = main_dir + r"Baijiao_Accuracy.csv"
# plot_area_data(
#     area_csv=area_result,
#     start_date='2016/01/01',
#     tolerance=0.005,
#     area_line=line_result,
#     accuracy_csv=accuracy_csv
#     )
# print('图表绘制完成！')


import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import matplotlib as mpl
import math
from adjustText import adjust_text

mpl.style.use('classic')
mpl.rcParams.update({'font.size': 16,
                     'font.family': 'Microsoft YaHei',
                     'mathtext.fontset': 'stix'})
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


def cal_DOY_from_start(start_date, target_date):
    """
    计算从指定开始日期(start_date)到目标日期(target_date)的累积天数（DOY）。
    """
    start_date = datetime.strptime(start_date, '%Y/%m/%d')
    target_date = datetime.strptime(target_date, '%Y/%m/%d')
    delta = target_date - start_date
    return delta.days + 1


def plot_area_data(area_csv, start_date='2022/05/01', tolerance=0.005, area_line=None,
                   accuracy_csv=None):
    """
    绘制面积随时间变化的图，并保存异常日期。

    参数：
    csv_file: str, 包含日期和面积数据的 CSV 文件路径
    start_date: str, 起始日期，格式为 'YYYY/MM/DD'
    tolerance: float, 面积增长的误差范围百分比
    output_file: str, 可选，若提供则保存图像为此路径
    txt_file: str, 可选，若提供则保存异常日期为此路径
    output_csv: str, 可选，若提供则保存提取的 CSV 文件
    """
    # 读取数据
    table = pd.read_csv(area_csv)
    doy = table['date'].astype(str).map(lambda date: cal_DOY_from_start(start_date, date))
    doy = table['date'].astype(str).map(lambda date: cal_DOY_from_start(start_date, date))
    area = table['area'].values

    # 新增 'abnormal' 列，默认值为 0（正常）
    table['abnormal'] = 0

    # 检查连续三天面积增长的情况并记录第二天的日期
    anomaly_dates = []
    anomaly_doys = []
    anomaly_areas = []
    pre_column = [0] * len(area)  # 用于标记是否发生异常，初始化为0
    true_column = [""] * len(area)  # 初始化 'TRUE' 列为空字符串

    for i in range(1, len(area) - 1):
        if (area[i] > area[i - 1] * (1 + tolerance)) and (area[i + 1] > area[i] * (1 + tolerance)):
            anomaly_dates.append(table['date'].iloc[i])
            anomaly_doys.append(doy.iloc[i])
            anomaly_areas.append(area[i])
            table.at[i, 'abnormal'] = 1  # 标记该日期为异常

    # 获取第一个异常日期的索引
    first_anomaly_index = next((i for i, val in enumerate(table['abnormal']) if val == 1), None)

    # 保存修改后的 CSV 文件
    table.to_csv(area_csv, index=False, encoding='utf-8-sig')  # 直接保存到原始的 csv_file

    # 提取数据并保存为新的 CSV 文件
    extracted_data = None  # 定义一个默认的 None 值，避免未定义错误

    if accuracy_csv and first_anomaly_index is not None:
        # 将 'TRUE' 列添加到原表格
        table['manual_label'] = true_column  # 新增 'TRUE' 列，内容为空
        table.drop(columns=['area'], inplace=True)  # 删除 'area' 列
        table.drop(columns=['abnormal'], inplace=True)  # 删除 'area' 列

        # 根据第一个异常日期的索引提取数据
        if first_anomaly_index < 10:
            extracted_data = table.iloc[:20, :]
        else:
            # 提取第一行和异常日期前9行以及后10行
            start_idx = max(first_anomaly_index - 10, 0)
            end_idx = min(first_anomaly_index + 10, len(table))
            extracted_data = table.iloc[start_idx:end_idx, :]

        # 保存提取的数据
        if extracted_data is not None:
            extracted_data.to_csv(accuracy_csv, index=False, encoding='utf-8-sig')

    # 绘图
    fig, ax1 = plt.subplots(figsize=(14, 8.5))
    ax1.plot(doy.values, area, color='red', lw=5, marker=None)  # red

    ax1.set_xticks([0, 123, 245, 365, 488, 610, 731])
    ax1.set_ylabel('面积 (km$\\mathrm{^2}$)', fontsize=22)
    ax1.set_xlabel('日期', fontsize=22)

    # 标记异常日期
    ax1.scatter(anomaly_doys, anomaly_areas, facecolors='#FAFA33', edgecolor='black', marker='o', s=200, linewidths=1.5,
                zorder=2)

    # 标注异常日期，根据ID（索引）判断奇偶数，设置不同的偏移量
    texts = []
    for idx, (x, y, date) in enumerate(zip(anomaly_doys, anomaly_areas, anomaly_dates)):
        # month_day = "/".join(date.split('/')[1:])  # 去掉年份部分
        # 分割日期并补零
        parts = date.split('/')
        month_day = f"{parts[1].zfill(2)}/{parts[2].zfill(2)}"  # 保留两位的月份和日期

        # 根据ID判断奇偶数，调整偏移方向
        if (idx+1) % 2 == 0:  # 偶数ID，向左偏移
            x_offset = -180
            y_offset = 0.02
        else:  # 奇数ID，向右偏移
            x_offset = 40
            y_offset = 0

        text = ax1.text(x + x_offset, y + y_offset, month_day, fontsize=12, color='#8A2BE2', ha='left', va='center',
                        rotation=0, fontweight='bold',
                        bbox=dict(facecolor='white', edgecolor='#4169E1', boxstyle='round,pad=0.001', alpha=0))
        texts.append(text)

    # 使用adjustText库自动调整文本位置
    adjust_text(texts)

    ax1.axes.xaxis.set_ticklabels(
        ["2022/5/1", "2022/9/1", "2023/1/1", "2023/5/1", "2023/9/1", "2024/1/1", "2024/5/1"])

    y_max = max(area) * 1.1
    y_min = math.floor(min(area))
    ax1.set_ylim([y_min, y_max])
    ax1.set_xlim([0, 731])

    plt.yticks(fontsize=18)
    plt.xticks(fontsize=18)

    # 保存或显示图像
    if area_line:
        plt.savefig(area_line, bbox_inches='tight')
    else:
        plt.show()

        
if __name__ == "__main__":
    main_dir = r"E:\personal file\00Zhongyan\00Nansha\Nansha_Island\01_Baijiao/"
    area_result = main_dir + r"Baijiao_Area.csv"
    line_result = main_dir + r"Baijiao_Area3.png"
    accuracy_csv = main_dir + r"Baijiao_Accuracy.csv"
    plot_area_data(
        area_csv=area_result,
        start_date='2016/01/01',
        tolerance=0.005,
        area_line=line_result,
        accuracy_csv=accuracy_csv
        )
    print('图表绘制完成！')