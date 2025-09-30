# OCR Functionality

import os
import torch
from PIL import Image
import kraken.binarization
from kraken import blla
from kraken.lib import models

class OCREngine:
    """Handle OCR for Arabic/Uthmani script."""
    
    def __init__(self, model_path=None):
        """
        Initialize OCR with appropriate models.
        
        Args:
            model_path (str, optional): Path to custom model file
        """
        # Check for GPU support with MPS (Apple Silicon)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
        
        # Load model
        try:
            if model_path and os.path.exists(model_path):
                self.model = models.load_any(model_path)
            else:
                # Try to load models from the models/ocr directory
                model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'ocr')
                model_path = os.path.join(model_dir, 'arabic_best.mlmodel')
                default_path = os.path.join(model_dir, 'default.mlmodel')
                
                if os.path.exists(model_path):
                    self.model = models.load_any(model_path)
                elif os.path.exists(default_path):
                    self.model = models.load_any(default_path)
                else:
                    print(f"Warning: No OCR model found in {model_dir}. OCR functionality will be limited.")
                    self.model = None
        except Exception as e:
            raise RuntimeError(f"Failed to load OCR model: {str(e)}")
    
    def recognize(self, image):
        """
        Perform OCR on an image.
        
        Args:
            image: PIL Image or numpy array
            
        Returns:
            str: Extracted text
        """
        try:
            if self.model is None:
                return "[OCR Model Not Available]"
                
            # Ensure image is in PIL format
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)
            
            # Binarize the image
            bw_img = kraken.binarization.nlbin(image)
            
            # Get text lines with baseline
            segmentation_result = blla.segment(bw_img)
            
            # Recognize text with proper bounds parameter
            result = self.model.predict(bw_img, 
                                       segmentation_result['boxes'],
                                       device=self.device)
            
            # Join all text lines
            text = '\n'.join([line.prediction for line in result])
            
            return text
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            return f"[OCR ERROR] {str(e)}\n{trace}"