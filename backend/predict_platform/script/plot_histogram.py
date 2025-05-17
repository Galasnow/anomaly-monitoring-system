import os
import re
import numpy as np
import cv2
import datetime
import matplotlib.dates
from matplotlib import pyplot as plt
from natsort import natsorted
import time
from osgeo import gdal
gdal.UseExceptions()


if __name__ == "__main__":
    image_name_1 = r"F:\zhongyan\gee_download_wenlai\S1A_IW_GRDH_1SDV_20241122T221439_20241122T221508_056673_06F40E_0F4A.tif"
    image_name_2 = r"F:\zhongyan\gee_download_wenlai\decimal\S1A_IW_GRDH_1SDV_20241122T221439_20241122T221508_056673_06F40E_0F4A-0000000000-0000000000.tif"

    with gdal.Open(image_name_1) as tiff_file:
        geo_transform_1 = tiff_file.GetGeoTransform()
        projection_1 = tiff_file.GetProjection()
        image_1 = tiff_file.ReadAsArray()

    with gdal.Open(image_name_2) as tiff_file:
        geo_transform_2 = tiff_file.GetGeoTransform()
        projection_2 = tiff_file.GetProjection()
        image_2 = tiff_file.ReadAsArray()

    center = [6000, 6000]
    crop_size = [4000, 4000]
    center_2 = [6000, 6000]
    geo_calibration = True

    if geo_calibration:
        exact_coordinates = [-1, -1]
        # exact_coordinates = [267146.46617872437, 2301003.086221326]
        if exact_coordinates == [-1, -1]:
            exact_coordinates[0] = geo_transform_1[0] + geo_transform_1[1] * center[0]
            exact_coordinates[1] = geo_transform_1[3] + geo_transform_1[5] * center[1]
            # logging.info(exact_coordinates)
            center_2[0] = int((exact_coordinates[0] - geo_transform_2[0]) / geo_transform_2[1])
            center_2[1] = int((exact_coordinates[1] - geo_transform_2[3]) / geo_transform_2[5])
            logging.info(f'new_center = {center_2}')
    logging.info(image_1.shape)
    image_1_crop = image_1[center[1] - crop_size[0]: center[1] + crop_size[0], center[0] - crop_size[1]: center[0] + crop_size[1]]
    image_1_1d = np.reshape(image_1_crop, -1)
    image_1_1d = np.nan_to_num(image_1_1d, nan=-1)
    range_1 = (-0.5, np.max(image_1_1d))
    image_2_crop = image_2[center_2[1] - crop_size[0]: center_2[1] + crop_size[0], center_2[0] - crop_size[1]: center_2[0] + crop_size[1]]
    image_2_1d = np.reshape(image_2_crop, -1)
    image_2_1d = np.nan_to_num(image_2_1d, nan=1)
    range_2 = (np.min(image_2_1d), 0.5)
    logging.info(range_1)
    logging.info(range_2)
    fig, ax = plt.subplots(2, 1)
    ax[0].hist(image_1_1d, bins=500, range=range_1, histtype='step')
    ax[0].set_title('Histogram of S1_GRD_FLOAT')
    ax[0].set_xlabel('value')
    ax[0].set_ylabel('count')
    ax[1].hist(image_2_1d, bins=500, range=range_2, histtype='step')
    ax[1].set_title('Histogram of S1_GRD')
    ax[1].set_xlabel('value')
    ax[1].set_ylabel('count')
    plt.show()
