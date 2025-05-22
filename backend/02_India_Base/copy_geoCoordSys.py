import os
from osgeo import gdal

def add_geoCoordSys_to_original_files(set_dir, label_dir):
    """
    从set_dir中的影像提取坐标，并赋值给label_dir中的对应影像，直接覆盖label_dir。
    :param set_dir: 带有坐标的图像文件夹
    :param label_dir: 没有坐标的图像文件夹
    """

    def update_geoCoordSys(read_path, img_transf, img_proj):
        array_dataset = gdal.Open(read_path, gdal.GA_Update)  # 以更新模式打开影像
        img_array = array_dataset.ReadAsArray(0, 0, array_dataset.RasterXSize, array_dataset.RasterYSize)

        if len(img_array.shape) == 2:  # 如果影像是单波段，添加维度
            img_array = img_array[None, ...]

        # 确保影像数据正确写入后更新坐标
        for i in range(img_array.shape[0]):
            array_dataset.GetRasterBand(i + 1).WriteArray(img_array[i])

        array_dataset.SetGeoTransform(img_transf)  # 更新仿射变换参数
        array_dataset.SetProjection(img_proj)  # 更新投影信息

        array_dataset.FlushCache()  # 确保数据写入磁盘
        array_dataset = None  # 关闭文件

        # print(f"Updated coordinates for: {read_path}")

    all_files = [f for f in os.listdir(set_dir) if f.endswith(".tif")]
    print('Total files to process:', len(all_files))

    for temp_file in all_files:
        img_pos_path = os.path.join(set_dir, temp_file)
        img_none_path = os.path.join(label_dir, temp_file)

        if not os.path.exists(img_none_path):
            print(f"Skipping {temp_file}, corresponding file not found in label directory.")
            continue

        dataset = gdal.Open(img_pos_path)
        img_pos_transf = dataset.GetGeoTransform()
        img_pos_proj = dataset.GetProjection()

        update_geoCoordSys(img_none_path, img_pos_transf, img_pos_proj)

