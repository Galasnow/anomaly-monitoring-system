import os
import cv2
import numpy as np
from tqdm import tqdm

def overlay_grayscale_on_image_batch(original_folder, grayscale_folder, output_folder, dilation_iter=1):
    # List all files in the original and grayscale folders
    original_files = os.listdir(original_folder)
    grayscale_files = os.listdir(grayscale_folder)

    # Iterate through each file in the original folder
    for original_filename in tqdm(original_files):
        # Construct paths for original and grayscale images
        original_image_path = os.path.join(original_folder, original_filename)
        # Assuming grayscale images have "_label" before the extension
        grayscale_filename = original_filename.replace('.tif', '.tif')
        # grayscale_filename = original_filename.replace('.tif', '.tif')
        grayscale_image_path = os.path.join(grayscale_folder, grayscale_filename)

        # Skip if grayscale image doesn't exist
        if not os.path.exists(grayscale_image_path):
            print(f"Grayscale image not found for {original_filename}. Skipping.")
            continue

        # Load the original image
        original_image = cv2.imread(original_image_path)
        if original_image is None:
            print(f"Failed to load the original image from {original_image_path}")
            continue

        # Load the grayscale prediction image
        grayscale_image = cv2.imread(grayscale_image_path, cv2.IMREAD_GRAYSCALE)
        if grayscale_image is None:
            print(f"Failed to load the grayscale image from {grayscale_image_path}")
            continue

        # Check if dimensions match
        if original_image.shape[:2] != grayscale_image.shape:
            print(f"The dimensions of {original_filename} and {grayscale_filename} do not match.")
            continue

        # Perform Canny edge detection to get the edges in the grayscale image
        edges = cv2.Canny(grayscale_image, 100, 200)

        # Dilate the edges to make them thicker
        kernel = np.ones((2, 2), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=dilation_iter)

        # Create a mask where the edges are
        mask = cv2.inRange(dilated_edges, 255, 255)

        # Create a red image with the same dimensions as the original image
        red_image = np.zeros_like(original_image)
        red_image[mask > 0] = [0, 0, 255]  # BGR format for red

        # Blend the red image with the original image
        # Here, to ensure the edges are pure red, we will use addWeighted with alpha=1.0 and beta=0.0
        overlayed_image = cv2.addWeighted(original_image, 1.0, red_image, 1.0, 0)

        # Prepare output path
        output_filename = os.path.splitext(original_filename)[0] + '.tif'
        output_image_path = os.path.join(output_folder, output_filename)

        # Save the result
        cv2.imwrite(output_image_path, overlayed_image)
        # print(f"Overlayed image saved to {output_image_path}")
