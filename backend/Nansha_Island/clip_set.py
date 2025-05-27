import os
import numpy as np
from tqdm import tqdm
from osgeo import gdal
gdal.UseExceptions()

def clip_set(set_dir, savefile_dir, size):
    all_file = []
    for root, dirs, files in os.walk(set_dir):
        for file in files:
            if file.endswith(".tif"):
                all_file.append(file)
    print('all file len ', len(all_file))

    pbar = tqdm(range(len(all_file)))
    pbar.set_description(f'Clip original images')
    for num in pbar:
        temp_file = all_file[num]
        in_ds = gdal.Open(os.path.join(set_dir, temp_file))  # 读取要切的原图

        width = in_ds.RasterXSize  # 获取数据宽度
        height = in_ds.RasterYSize  # 获取数据高度
        outbandsize = in_ds.RasterCount  # 获取数据波段数
        im_geotrans = in_ds.GetGeoTransform()  # 获取仿射矩阵信息
        im_proj = in_ds.GetProjection()  # 获取投影信息
        datatype = in_ds.GetRasterBand(1).DataType

        # 读取原图中的每个波段
        in_band1 = in_ds.GetRasterBand(1)
        in_band2 = in_ds.GetRasterBand(2)
        in_band3 = in_ds.GetRasterBand(3)
        # in_band4 = in_ds.GetRasterBand(4)

        size = size  # 切割的块的大小
        # step = size // 2  # 50%重叠
        step = size


        num_tiles_x = (width + step - 1) // step
        num_tiles_y = (height + step - 1) // step

        for i in range(num_tiles_y):
            up = i * step
            down = size
            if up + size > height:
                up = height - size  # 向前补充，使最后一块是 1024 高

            for j in range(num_tiles_x):
                left = j * step
                right = size
                if left + size > width:
                    left = width - size  # 向前补充，使最后一块是 1024 宽

                # 读取各个波段的数据
                out_band1 = in_band1.ReadAsArray(left, up, right, down)
                out_band2 = in_band2.ReadAsArray(left, up, right, down)
                out_band3 = in_band3.ReadAsArray(left, up, right, down)
                # out_band4 = in_band4.ReadAsArray(left, up, right, down)

                # 获取Tif的驱动，为创建切出来的图文件做准备
                gtif_driver = gdal.GetDriverByName("GTiff")
                file = os.path.join(savefile_dir, f"{os.path.splitext(temp_file)[0]}_{i}_{j}.tif")

                # 创建切出来的要存的文件
                out_ds = gtif_driver.Create(file, right, down, outbandsize, datatype)

                # 获取原图的原点坐标信息
                ori_transform = im_geotrans

                # 读取原图仿射变换参数值
                top_left_x = ori_transform[0]  # 左上角x坐标
                w_e_pixel_resolution = ori_transform[1]  # 东西方向像素分辨率
                top_left_y = ori_transform[3]  # 左上角y坐标
                n_s_pixel_resolution = ori_transform[5]  # 南北方向像素分辨率
                top_left_x = top_left_x + left * w_e_pixel_resolution
                top_left_y = top_left_y + up * n_s_pixel_resolution

                # 将计算后的值组装为一个元组，以方便设置
                dst_transform = (top_left_x, ori_transform[1], ori_transform[2], top_left_y, ori_transform[4], ori_transform[5])

                # 设置裁剪出来图的原点坐标
                out_ds.SetGeoTransform(dst_transform)

                # 设置SRS属性（投影信息）
                out_ds.SetProjection(im_proj)

                # 写入目标文件
                out_ds.GetRasterBand(1).WriteArray(out_band1)
                out_ds.GetRasterBand(2).WriteArray(out_band2)
                out_ds.GetRasterBand(3).WriteArray(out_band3)
                # out_ds.GetRasterBand(4).WriteArray(out_band4)

                # 将缓存写入磁盘
                out_ds.FlushCache()

                # 释放内存
                # del out_ds, out_band1, out_band2, out_band3, out_band4
                del out_ds, out_band1, out_band2, out_band3