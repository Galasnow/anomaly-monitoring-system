import os

import cv2
import numpy as np
from osgeo import gdal

from utils import convert_np_dtype_to_gdal_type


def read_image_as_ndarray(image_path, as_rgb=True, gray2rgb=True, channel_combination=(0,1,2), ndarray_dtype=np.float32) -> np.ndarray:
    _, suffix = os.path.splitext(image_path)
    if suffix in ['.tifff', '.tiff']:
        with gdal.Open(image_path) as tiff_file:
            image = tiff_file.ReadAsArray().astype(ndarray_dtype)
            if image.ndim == 3:
                image = np.transpose(image, (1, 2, 0))
                if as_rgb and image.shape[-1] != 3:
                    if np.max(channel_combination) >= image.shape[-1]:
                        raise RuntimeError('select band exceed image bands count')
                    new_image = np.zeros((image.shape[0], image.shape[1], 3), dtype=ndarray_dtype)
                    new_image[:, :, 0] = image[:, :, channel_combination[0]]
                    new_image[:, :, 1] = image[:, :, channel_combination[1]]
                    new_image[:, :, 2] = image[:, :, channel_combination[2]]
                    image = new_image
            else:
                if gray2rgb:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        image = cv2.imread(image_path).astype(ndarray_dtype)
    if not image.flags['C_CONTIGUOUS']:
        image = np.ascontiguousarray(image)
    return image


def export_image(out_image, output_path: str, file_name_stem: str, window, offset=0, **kwargs):
    out_image_stem = f'{file_name_stem}_{window['x_start']}_{window['x_stop']}_{window['y_start']}_{window['y_stop']}'
    output_format = 'tif'
    jpg_quality = 95
    jp2_compression = 950
    tif_data_type = 'int16'
    crop_size = None
    gap_size = None
    geo_transform = None
    projection = None

    for key, value in kwargs.items():
        if key == 'output_format':
            if value in ['jpg', 'png', 'jp2', 'tif']:
                output_format = value
            else:
                raise RuntimeError('"output_format" keyword argument must be "jpg", "png", "jp2" or "tif"')
        elif key == 'jpg_quality':
            if 0 < value <= 100:
                jpg_quality = value
            else:
                raise RuntimeError('"jpg_quality" keyword argument range from 1 to 100')
        elif key == 'jp2_compression':
            if 0 <= value <= 1000:
                jp2_compression = value
            else:
                raise RuntimeError('"jp2_compression" keyword argument range from 0 to 1000')
        elif key == 'tif_data_type':
            if value is str:
                tif_data_type = value
            else:
                raise RuntimeError('"tif_data_type" keyword argument should be string')
        elif key == 'crop_size':
                crop_size = value
        elif key == 'gap_size':
                gap_size = value
        elif key == 'geo_transform':
                geo_transform = value
        elif key == 'projection':
                projection = value

    match output_format:
        case 'jpg':
            if out_image.ndim == 3 and out_image.shape[0] > 3:
                out_image = out_image[:, :, 0:3]
            cv2.imwrite(f'{output_path}/{out_image_stem}.jpg', out_image,
                        [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])
        case 'png':
            # TODO
            cv2.imwrite(f'{output_path}/{out_image_stem}.png', out_image)
        case 'jp2':
            # TODO
            cv2.imwrite(f'{output_path}/{out_image_stem}.jp2', out_image,
                        [int(cv2.IMWRITE_JPEG2000_COMPRESSION_X1000), jp2_compression])
        case 'tif':
            driver = gdal.GetDriverByName('GTiff')
            if out_image.ndim == 3:
                band_count = out_image.shape[-1]
            else:
                band_count = 1
            # Create a new GeoTIFF file to store the result
            out_gdal_type = convert_np_dtype_to_gdal_type(out_image.dtype)

            with driver.Create(f'{output_path}/{out_image_stem}.tif', crop_size[0], crop_size[1], band_count,
                               out_gdal_type, options=['COMPRESS=LZW']) as out_tiff:
                # Set the geotransform and projection information for the out TIFF based on the input tif
                out_tiff.SetGeoTransform(geo_transform)
                out_tiff.SetProjection(projection)

                # Write the out array to the first band of the new TIFF
                if out_image.ndim == 3:
                    for i in range(out_image.shape[-1]):
                        out_tiff.GetRasterBand(i + 1).WriteArray(out_image[:, :, i])
                else:
                    out_tiff.GetRasterBand(1).WriteArray(out_image)

                # Write the data to disk
                out_tiff.FlushCache()
        case _:
            raise RuntimeError('Unknown file type!')