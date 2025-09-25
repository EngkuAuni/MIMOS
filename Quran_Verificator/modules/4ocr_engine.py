# OCR functionality

import os
import tempfile
import subprocess
import numpy as np
from PIL import Image
import importlib.util
import kraken.binarization
from kraken import blla
from kraken.lib import models
from PIL import Image
import torch

class OCREngine:
    """Handle OCR for Arabic/Uthmani script."""
    
    def __init__(self):
        """Initialize OCR with appropriate models."""
        # Check for GPU support with MPS (Apple Silicon)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
            
        # Load default model
        try:
            self.model = models.load_any("arabic_best.mlmodel")
        except:
            # Fallback to default model if arabic model not available
            self.model = models.load_any("default")

            
    
    def recognize(self, image):
        """Perform OCR on an image."""
        try:
            # Ensure image is in PIL format
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)
            
            # Binarize the image
            bw_img = kraken.binarization.nlbin(image)
            
            # Get text lines with baseline
            # This creates the 'bounds' that rpred needs
            segmentation_result = blla.segment(bw_img)
            
            # Recognize text with proper bounds parameter
            result = self.model.predict(bw_img, 
                                       segmentation_result['boxes'],  # This provides the bounds
                                       device=self.device)
            
            # Join all text lines
            text = '\n'.join([line.prediction for line in result])
            
            return text
        except Exception as e:
            return f"[OCR ERROR] {str(e)}"