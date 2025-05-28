# -*- coding: utf-8 -*-
# 核心文件，包含了定义数据集路径，定义train还是test
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import torch
import torch.utils as utils
from torch.autograd import Variable
import torchvision.transforms as transforms
import numpy as np
from tqdm import tqdm
# my libs
from dataio import BuildingDataset
from dataio import RandomCrop
from clip_set import clip_set
from model_v3plus import DeepLabv3_plus as Unet
from trainer import Trainer
from visualization_gray import visualize_results_gray
from copy_geoCoordSys import add_geoCoordSys_to_original_files
from merge_result import batch_stitch
from calculate_area import batch_calculate_white_area
from plot_line import plot_area_data
from merge import overlay_grayscale_on_image_batch
from plot_figure import generate_test_image_plots
from get_id_index import find_matching_id
#
def get_file_names_in_folder(folder_path):
    file_names = []
    # 遍历文件夹中的所有文件和子文件夹
    for _, _, filenames in os.walk(folder_path):
        for filename in filenames:
            # 获取文件名（不包含扩展名）
            file_name = os.path.splitext(filename)[0]
            # 将文件名添加到列表中
            file_names.append(file_name)
    return file_names

if __name__ == "__main__":
    DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    current_file_path = os.path.abspath(__file__)
    current_path = os.path.dirname(current_file_path)

    main_dir = r"../public/Nansha_Island/02_Bishengjiao/"

    # # -----------------step 1:将原始影像裁剪为256*256-----------------
    size = 128
    set_dir = main_dir + r"01_Input/"
    cut_set_dir = main_dir + r"test/image/"
    if not os.path.exists(cut_set_dir):
        os.makedirs(cut_set_dir)
    clip_set(set_dir, cut_set_dir, size)
    print('裁剪完成！')

    # -----------------step 2:使用训练好的模型对影像进行预测-----------------
    # train_dir = r"E:\04_ZhongyanExperiment\03_TaiWan_Port\train/"
    test_dir = main_dir + r"test/"

    model_file_path = os.path.join(current_path, f"./model/model3.pth")
    #file_path = r'E:\personal file\00Zhongyan\00Nansha\Nansha_Island\code\model3.pth'

    # 读取每个文件的名字并存为file，方便后面命名预测结果
    # test_folder_path = r'E:\04_ZhongyanExperiment\03_TaiWan_Port\test\image/'  # 修改为你的文件夹路径
    test_folder_path = cut_set_dir
    files = get_file_names_in_folder(test_folder_path)

    # 定义data的路径和预处理方式（随机裁剪）
    # 这里进行了对于NoData像元的操作：检查影像中所有波段都为0的像素，将所有波段都为0的像素标记为NoData值（-1），记录所有波段都为0的像素的位置，这将用于在损失函数中忽略这些像素
    # train_data = BuildingDataset(root_dir = train_dir, mode='train')   # transform = composed 这个是选择是否使用随机裁剪
    test_data = BuildingDataset(root_dir = test_dir, mode='test')      # 如果预测时没有标签，就使用mode='test'

    # train test的批处理方式（每批次读1个，并打乱数据集）
    # train_loader = utils.data.DataLoader(train_data, batch_size=4, shuffle=True,num_workers = 0)
    test_loader = utils.data.DataLoader(test_data, batch_size=4, num_workers = 0)

    # building the net 输入通道为3，输出通道为1
    unet = Unet(n_channels=3, n_classes=1)
    unet = unet.to(DEVICE)
    # unet = unet.cuda()
    # print("begin training!")

    trainer = Trainer(net = unet, file_path = model_file_path)
    #
    # trainer.train_model(train_loader=train_loader, test_loader=test_loader, epoch=100)
    # print("训练完成")
    # show result:
    if True:
        for i in tqdm(range(len(test_data))):
            sample = test_data[i]
            image_tensor = Variable(torch.FloatTensor(sample["image"])).to(DEVICE).unsqueeze(0)

            image_pred = trainer.predict(image_tensor)
            image_pred = image_pred.squeeze().cpu().data.numpy()  # 预测结果

            # 恢复原图像值
            image = (sample["image"].transpose(1, 2, 0) + 1) * (255 * 0.5)

            # 处理 NoData 区域
            no_data_mask = np.all(image == 0, axis=-1)
            image_pred[no_data_mask] = 0  # 将 NoData 区域的预测结果设置为 0

            save_image = main_dir + r"test\result128/"
            visualize_results_gray(image_pred, files[i],save_image)

    print('预测完成！')

    # -----------------step 3:对预测结果进行拼接-----------------
    result_dir = main_dir + r"test\result128/"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    add_geoCoordSys_to_original_files(cut_set_dir, result_dir)   # 带坐标的影像、未带坐标的结果

    result_merge_dir = main_dir + r"02_Output/result"
    if not os.path.exists(result_merge_dir):
        os.makedirs(result_merge_dir)

    batch_stitch(cut_set_dir, result_dir, result_merge_dir,set_dir)   # 切割后的影像、切割后的结果、合并后的结果、原始影像
    add_geoCoordSys_to_original_files(set_dir, result_merge_dir)
    print('结果拼接完成！')

    # -----------------step 4:记录面积变化-----------------
    pixel_area = 100 / 1000000  # 每个像素大小是10-4平方千米
    # pixel_area = 100   # 每个像素大小是100平方米
    area_result = main_dir + r"02_Output/Bishengjiao_Area.csv"
    batch_calculate_white_area(result_merge_dir, pixel_area, area_result)
    #
    # # -----------------step 5:根据面积变化获取异常日期并绘制图表-----------------
    line_result = main_dir + r"02_Output/Bishengjiao_Area.png"
    accuracy_csv = main_dir + r"02_Output/Bishengjiao_Accuracy.csv"
    plot_area_data(
        area_csv=area_result,
        start_date='2016/01/01',
        tolerance=0.005,
        area_line=line_result,
        accuracy_csv=accuracy_csv
    )
    print('图表绘制完成！')
    #
    # # -----------------step 6:绘制异常扩建时期影像/影像及提取结果-----------------
    image_merge_result_dir = main_dir + r"test\merge/"
    if not os.path.exists(image_merge_result_dir):
        os.makedirs(image_merge_result_dir)
    overlay_grayscale_on_image_batch(set_dir, result_merge_dir, image_merge_result_dir, 4)
    add_geoCoordSys_to_original_files(set_dir, image_merge_result_dir)

    id_index = find_matching_id(accuracy_csv, area_result)
    print("测试的第一景影像id为" + str(id_index))

    # image_merge_result_plt = main_dir + r"Baijiao_Image.png"
    # generate_test_image_plots(set_dir, image_merge_result_plt, id_index)
    # print('预测结果绘制完成！')

    finish_txt = main_dir + r"02_Output//finish.txt"
    with open(finish_txt, "w") as file:
        pass  # 不写入任何内容，文件会保持为空