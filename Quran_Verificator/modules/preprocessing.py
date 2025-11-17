# Image preprocessing functionality

import cv2
import numpy as np
from PIL import Image

class ImagePreprocessor:
    """Preprocess images for OCR and feature extraction."""
    
    def __init__(self):
        """Initialize the image preprocessor."""
        pass
    
    def process_image(self, image_path):
        """
        Process an image for OCR and feature extraction.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary of processed images
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Deskew
        deskewed = self._deskew(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(deskewed, None, 10, 7, 21)
        
        # Binarize using Otsu's method
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Auto-crop (detect and remove margins)
        cropped = self._auto_crop(binary)
        
        # Convert to PIL image for OCR
        pil_image = Image.fromarray(cropped)
        
        return {
            'original': image,
            'grayscale': gray,
            'deskewed': deskewed,
            'denoised': denoised,
            'binary': binary,
            'cropped': cropped,
            'pil_image': pil_image
        }
    
    def _deskew(self, image):
        """
        Deskew an image by detecting the orientation.
        
        Args:
            image (numpy.ndarray): Grayscale image
            
        Returns:
            numpy.ndarray: Deskewed image
        """
        # Find non-zero points
        coords = np.column_stack(np.where(image > 0))
        if len(coords) <= 10:  # Not enough points
            return image
            
        # Calculate skew angle
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = 90 + angle
        
        # Rotate image to deskew
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
    def _auto_crop(self, image):
        """
        Auto-crop an image by detecting and removing margins.
        
        Args:
            image (numpy.ndarray): Binary image
            
        Returns:
            numpy.ndarray: Cropped image
        """
        # Find all non-zero points
        coords = cv2.findNonZero(image)
        if coords is None:  # Empty image
            return image
            
        # Get bounding box
        x, y, w, h = cv2.boundingRect(coords)
        
        # Crop the image
        cropped = image[y:y+h, x:x+w]
        
        return cropped