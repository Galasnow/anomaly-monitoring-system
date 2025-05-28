import pandas as pd

# 读取 Gaoxiong_Port_Accuracy.csv 和 Gaoxiong_Port_Area.csv
accuracy_df = pd.read_csv(r"E:\04_ZhongyanExperiment\02_Building\00_India_Base_Test\01_Durbuk_Base\Durbuk_Base_Accuracy.csv")
area_df = pd.read_csv(r"E:\04_ZhongyanExperiment\02_Building\00_India_Base_Test\01_Durbuk_Base\Durbuk_Base_Area.csv")

accuracy_df['date'] = pd.to_datetime(accuracy_df['date'])
area_df['date'] = pd.to_datetime(area_df['date'])

# 创建一个字典，将 area_df 的日期与 abnormal 值关联
area_dict = dict(zip(area_df['date'], area_df['abnormal']))

# 定义一个函数，用来根据日期从 area_dict 获取 abnormal 值
def get_abnormal(date):
    return area_dict.get(date, None)  # 如果找不到对应的日期，返回 None

# 在 accuracy_df 中新增一列 'abnormal'，使用 get_abnormal 函数填充
accuracy_df['abnormal'] = accuracy_df['date'].apply(get_abnormal)

# 计算准确率（manual_label 和 abnormal 相等的数量）
correct_count = (accuracy_df['manual_label'] == accuracy_df['abnormal']).sum()
total_count = len(accuracy_df)
accuracy = (correct_count / total_count) * 100  # 转换为百分比

# 添加 '监测准确率' 列，默认为 NaN
accuracy_df['监测准确率'] = pd.NA

# 将准确率添加到最后一行（可以选择一个特定位置）
accuracy_df.at[0, '监测准确率'] = f'{accuracy:.2f}%'

# 保存修改后的 CSV 文件
accuracy_df.to_csv(r"E:\04_ZhongyanExperiment\02_Building\00_India_Base_Test\01_Durbuk_Base\Durbuk_Base_Accuracy_Updated.csv", index=False, encoding='utf-8-sig')

# 打印准确率
print(f"判断正确的数量: {correct_count}")
print(f"总的数量: {total_count}")
print(f"Accuracy: {accuracy:.2f}%")
