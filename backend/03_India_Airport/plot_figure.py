import os
import matplotlib.pyplot as plt
from matplotlib import patches as mpatches
import geopandas as gpd
import rasterio as rio
from rasterio.plot import plotting_extent


# 函数：生成水体掩模图像
def generate_test_image_plots(wm_file_path, output_path, id_index):
    # 切换工作目录
    os.chdir(wm_file_path)

    file_list = os.listdir(wm_file_path)
    file_list.sort()  # 对文件列表进行排序

    # 筛选出后缀为.tif的文件，并按照文件名排序
    tif_list = [file for file in file_list if file.endswith('.tif')]

    # 取最新的20个.tif文件
    latest_tif_list = tif_list[id_index:id_index + 20]

    # 读取图像尺寸来计算figsize
    with rio.open(latest_tif_list[0]) as src:
        height, width = src.height, src.width

    # 创建子图
    fig, axes = plt.subplots(nrows=4, ncols=5, figsize=(25, 20), sharex=True, sharey=True)

    sub_plot_num = 0
    i, j = 0, 0

    for tif in latest_tif_list:
        if sub_plot_num < len(tif_list):
            with rio.open(tif) as water_Mask:
                water_Mask_data = water_Mask.read(masked=True)
                water_Mask_meta = water_Mask.profile
                water_Mask_extent = plotting_extent(water_Mask)

            axes[i][j].axis('off')
            axes[i][j].imshow(water_Mask_data.transpose(1, 2, 0), extent=water_Mask_extent)
            title = tif.split('_')[0][:8]  # 从文件路径中提取文件名部分，并根据文件名格式取得日期部分

            axes[i][j].set_title(title, fontsize=20, fontweight='bold', pad=6)  # 标题 默认居中，pad=6是指标题距离图的位置

            sub_plot_num += 1
            j += 1
            if j > 4:
                i += 1
                j = 0

    # 添加指北针
    ax = axes[0][0]
    add_north(ax)

    # 在最后一个子图（右下角）添加比例尺
    last_ax = axes[3][4]
    minx, maxx = last_ax.get_xlim()
    miny, maxy = last_ax.get_ylim()
    # 计算比例尺的起始位置在 x 轴上的坐标
    lon0 = minx + (maxx - minx) * 0.5
    # 计算比例尺的起始位置在y轴上的坐标
    lat0 = miny + (maxy - miny) * 0.05
    # 添加比例尺
    add_scalebar(last_ax, lon0, lat0, length=100)  # 假设比例尺长度为2000米

    # 调整子图之间的水平间距（即列之间的间距）和垂直间距（即行之间的间距）
    plt.subplots_adjust(wspace=0.1, hspace=0.1)

    # 保存图像
    fig.savefig(output_path, bbox_inches='tight', dpi=600, format='png')


# -----------函数：添加指北针--------------
def add_north(ax, labelsize=15, loc_x=0.1, loc_y=0.85, width=0.1, height=0.16, pad=0.1):
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    ylen = maxy - miny
    xlen = maxx - minx
    left = [minx + xlen * (loc_x - width * .5), miny + ylen * (loc_y - pad)]
    right = [minx + xlen * (loc_x + width * .5), miny + ylen * (loc_y - pad)]
    top = [minx + xlen * loc_x, miny + ylen * (loc_y - pad + height)]
    center = [minx + xlen * loc_x, left[1] + (top[1] - left[1]) * .4]
    triangle = mpatches.Polygon([left, top, right, center], color='w')
    ax.text(s='N', x=minx + xlen * loc_x, y=miny + ylen * (loc_y - pad + height), fontsize=labelsize, color='w', horizontalalignment='center', verticalalignment='bottom')
    ax.add_patch(triangle)


# -----------函数：添加比例尺--------------
def add_scalebar(ax, lon0, lat0, length, size=3, fontsize=10):
    # 用来绘制水平线
    ax.hlines(y=lat0, xmin=lon0, xmax=lon0 + length, colors="white", ls="-", lw=2, label='%dm' % (length))
    # 用来绘制垂直线
    ax.vlines(x=lon0, ymin=lat0 , ymax=lat0 + size + 10, colors="white", ls="-", lw=2)
    ax.vlines(x=lon0 + length / 2, ymin=lat0, ymax=lat0 + size + 10, colors="white", ls="-", lw=2)
    ax.vlines(x=lon0 + length, ymin=lat0 , ymax=lat0 + size + 10, colors="white", ls="-", lw=2)
    # 增加文本标注
    ax.text(lon0 + length, lat0 + size + 15, '%d' % (length), horizontalalignment='center', fontweight='bold',fontsize=fontsize, color='white')
    ax.text(lon0 + length / 2, lat0 + size + 15, '%d' % (length / 2), horizontalalignment='center', fontweight='bold',fontsize=fontsize, color='white')
    ax.text(lon0, lat0 + size + 15, '0', horizontalalignment='center', fontweight='bold',fontsize=fontsize, color='white')
    ax.text(lon0 + length / 2 * 2.7, lat0 + size + 15, 'm', horizontalalignment='center', fontweight='bold',fontsize=fontsize, color='white')