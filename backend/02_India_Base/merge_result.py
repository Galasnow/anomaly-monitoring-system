import os
from osgeo import gdal
import numpy as np

def calculate_bounds(tile_files):
    min_x, min_y, max_x, max_y = None, None, None, None
    for tile in tile_files:
        ds = gdal.Open(tile)
        geo_transform = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize

        top_left_x = geo_transform[0]
        top_left_y = geo_transform[3]
        bottom_right_x = top_left_x + width * geo_transform[1] + height * geo_transform[2]
        bottom_right_y = top_left_y + width * geo_transform[4] + height * geo_transform[5]

        if min_x is None:
            min_x, min_y, max_x, max_y = top_left_x, bottom_right_y, bottom_right_x, top_left_y
        else:
            min_x = min(min_x, top_left_x)
            min_y = min(min_y, bottom_right_y)
            max_x = max(max_x, bottom_right_x)
            max_y = max(max_y, top_left_y)

    return (min_x, min_y, max_x, max_y)

def merge_tiles_with_min_value(tile_files, output_path, geo_transform, projection, output_bounds):
    # Calculate the size of the output image
    min_x, min_y, max_x, max_y = output_bounds
    x_res = int((max_x - min_x) / geo_transform[1])
    y_res = int((max_y - min_y) / -geo_transform[5])

    # Create the output image
    driver = gdal.GetDriverByName('GTiff')
    output_ds = driver.Create(output_path, x_res, y_res, 1, gdal.GDT_Byte)
    output_ds.SetGeoTransform((min_x, geo_transform[1], 0, max_y, 0, geo_transform[5]))
    output_ds.SetProjection(projection)

    # Initialize the output array with large values (since we want to take the min)
    output_array = np.full((y_res, x_res), 255, dtype=np.uint8)

    # Merge the tiles with min value in overlap regions
    for tile in tile_files:
        ds = gdal.Open(tile)
        tile_array = ds.ReadAsArray()

        tile_geo_transform = ds.GetGeoTransform()
        offset_x = int((tile_geo_transform[0] - min_x) / geo_transform[1])
        offset_y = int((max_y - tile_geo_transform[3]) / -geo_transform[5])

        # Update the output array with the min value in overlap regions
        for y in range(tile_array.shape[0]):
            for x in range(tile_array.shape[1]):
                output_y = offset_y + y
                output_x = offset_x + x
                output_array[output_y, output_x] = min(output_array[output_y, output_x], tile_array[y, x])

    # Write the output array to the output dataset
    output_ds.GetRasterBand(1).WriteArray(output_array)
    output_ds.FlushCache()

def stitch_tiles(image_tile_files, label_tile_files, stitched_image_path, stitched_label_path, original_image_path):
    if not image_tile_files or not label_tile_files:
        print("No tile files found.")
        return

    # Calculate the output bounds for the mosaics
    output_bounds = calculate_bounds(image_tile_files)

    # Open original image to get georeference information
    original_image = gdal.Open(original_image_path)
    geo_transform = original_image.GetGeoTransform()
    projection = original_image.GetProjection()

    # Create mosaic for image tiles
    gdal.Warp(stitched_image_path, image_tile_files, format='GTiff', outputBounds=output_bounds,
              xRes=geo_transform[1], yRes=-geo_transform[5], srcSRS=projection, dstSRS=projection)

    # Create mosaic for label tiles with min value in overlap regions
    merge_tiles_with_min_value(label_tile_files, stitched_label_path, geo_transform, projection, output_bounds)

    # print(f'Mosaic stitching completed for {stitched_image_path}.')

def batch_stitch(image_tile_dir, label_tile_dir, stitched_image_base_dir, original_image_base_dir):
    # Get the list of original images
    original_images = [f for f in os.listdir(original_image_base_dir) if f.endswith('.tif')]

    for original_image in original_images:
        region_date = os.path.splitext(original_image)[0]

        # Extract region and date
        region = region_date.split('_')[0]
        date = region_date.split('_')[1]

        # Find corresponding tiles
        image_tile_files = [os.path.join(image_tile_dir, f) for f in os.listdir(image_tile_dir)
                            if f.startswith(f'{region}_{date}_') and f.endswith('.tif')]
        label_tile_files = [os.path.join(label_tile_dir, f) for f in os.listdir(label_tile_dir)
                            if f.startswith(f'{region}_{date}_') and f.endswith('.tif')]

        stitched_image_path = os.path.join(stitched_image_base_dir, f'{region_date}.tif')
        stitched_label_path = os.path.join(stitched_image_base_dir, f'{region_date}.tif')

        original_image_path = os.path.join(original_image_base_dir, original_image)

        if image_tile_files and label_tile_files:
            stitch_tiles(image_tile_files, label_tile_files, stitched_image_path, stitched_label_path, original_image_path)
        else:
            print(f"No tile files found for {region_date}.")