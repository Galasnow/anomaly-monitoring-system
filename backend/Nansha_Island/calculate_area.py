import os
import cv2
import numpy as np
import csv
from datetime import datetime

def calculate_white_area(image_path, pixel_area):
    """
    Calculate the area of white pixels in a grayscale image.

    Parameters:
    - image_path: str, path to the grayscale image
    - pixel_area: float, area represented by one pixel in real-world units

    Returns:
    - total_area: float, calculated total area of white pixels in real-world units
    """
    # Load the grayscale image
    grayscale_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if grayscale_image is None:
        raise ValueError(f"Failed to load the image from {image_path}")

    # Threshold the image to get a binary mask of white pixels
    _, white_pixels_mask = cv2.threshold(grayscale_image, 254, 255, cv2.THRESH_BINARY)

    # Calculate the number of white pixels
    white_pixel_count = cv2.countNonZero(white_pixels_mask)

    # Calculate the total area
    total_area = white_pixel_count * pixel_area

    return total_area


def batch_calculate_white_area(folder_path, pixel_area, output_csv_file):
    """
    Batch calculate the area of white pixels for all _label.tif images in a folder and save to a single CSV file.

    Parameters:
    - folder_path: str, path to the folder containing the images
    - pixel_area: float, area represented by one pixel in real-world units
    - output_csv_file: str, path to the output CSV file where results will be saved
    """
    results = []

    # List all files in the folder
    all_files = os.listdir(folder_path)

    # Filter out files ending with _label.tif
    label_files = [f for f in all_files if f.endswith('.tif')]
    # label_files = [f for f in all_files if f.endswith('.tif')]


    # Iterate through each label file and calculate white pixel area
    for label_file in label_files:
        image_path = os.path.join(folder_path, label_file)
        try:
            total_area = calculate_white_area(image_path, pixel_area)
            # Extract file name parts
            date_str = label_file[:8]  # Get the first 8 characters as date
            # Convert date string to date format
            date = datetime.strptime(date_str, "%Y%m%d").date()
            # Store the result
            results.append({'date': date.strftime('%Y/%m/%d'), 'area': total_area})
            # print(f"Total white pixel area for {label_file}: {total_area} square units")
        except ValueError as e:
            print(e)

    # Save results to a single CSV file
    with open(output_csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['date', 'area'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"All results saved to {output_csv_file}")


