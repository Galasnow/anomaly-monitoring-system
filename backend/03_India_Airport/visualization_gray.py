import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


def visualize_results_gray( image_pred, files, save_image):
    """
    image: [height, width, channels] 0-255
    image_true:[height, width] 0-1
    image_pred:[height, width] 0-1

    true positive(green): y_true = 1, y_pred = 1
    false positive(red): y_true = 0, y_pred = 1
    false negative(blue): y_true = 1, y_pred = 0
    true negative(original): y_true = 0, y_pred = 0
    """
    # Initialize a black background
    height, width = image_pred.shape
    result_image = np.zeros((height, width), dtype=np.uint8)

    # Convert prediction to black and white
    result_image[image_pred > 0.5] = 255
    result_image[image_pred <= 0.5] = 0

    # Display the result image
    plt.imshow(result_image, cmap='gray')
    plt.axis('off')
    plt.tight_layout()  # Automatically adjust subplot parameters

    # Save the result image
    pillow_image = Image.fromarray(result_image)

    if not os.path.exists(save_image):
        os.makedirs(save_image)
    pillow_image.save(
        save_image + str(files) + ".tif",
        dpi=(600, 600))
    return
