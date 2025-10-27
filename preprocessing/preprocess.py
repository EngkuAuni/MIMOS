# OpenCVimage preprocessing (needs improvement)

import cv2
import numpy as np
from PIL import Image

def preprocess_image(image):
    # Converts PIL image to OpenCV format
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binarized = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
    resized = cv2.resize(binarized, (int(binarized.shape[1]*1.2), int(binarized.shape[0]*1.2)))
    return Image.fromarray(resized)