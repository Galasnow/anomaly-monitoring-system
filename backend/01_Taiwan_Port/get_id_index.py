import pandas as pd

def find_matching_id(accuracy_csv_path, area_csv_path):
    """
    从给定的 CSV 文件中，比较 Gaoxiong_Port_Accuracy.csv 和 Gaoxiong_Port_Area.csv 中的日期列，
    返回 Gaoxiong_Port_Area.csv 中与 Gaoxiong_Port_Accuracy.csv 中第一行日期相匹配的行号（ID）。

    :param accuracy_csv_path: Gaoxiong_Port_Accuracy.csv 文件路径
    :param area_csv_path: Gaoxiong_Port_Area.csv 文件路径
    :return: 匹配的行号，如果没有找到匹配则返回 None
    """
    # 读取 CSV 文件
    accuracy_df = pd.read_csv(accuracy_csv_path)
    area_df = pd.read_csv(area_csv_path)

    # 获取 Gaoxiong_Port_Accuracy.csv 的第一行日期，并转换为 datetime 类型
    accuracy_date = pd.to_datetime(accuracy_df.iloc[0, 0], format='%Y/%m/%d')

    # 获取 Gaoxiong_Port_Area.csv 的日期列，并转换为 datetime 类型
    area_dates = pd.to_datetime(area_df.iloc[:, 0], format='%Y/%m/%d')

    # 查找匹配的日期并返回 ID（行号）
    matching_row = area_dates[area_dates == accuracy_date].index.tolist()

    if matching_row:
        return matching_row[0]  # 返回第一个匹配的行号
    else:
        return None  # 如果没有找到匹配的日期，返回 None

