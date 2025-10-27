# OCR Functionality

import os
import cv2
import torch
import numpy as np
from PIL import Image
import kraken.binarization
from kraken.lib import models
import kraken.pageseg as pageseg

class OCREngine:
    """Handle OCR for Arabic/Uthmani script."""
    
    def __init__(self, model_path=None):
        """
        Initialize OCR with appropriate models.
        
        Args:
            model_path (str, optional): Path to custom model file
        """
        # Set device for PyTorch (but not used directly in predict)
        self.device = torch.device("cpu")
        torch.set_default_device(self.device)
        
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
            
            # Enhanced binarization for Arabic text
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
                
            # Convert to numpy array for preprocessing
            img_array = np.array(image)
            
            # 1. Apply Gaussian blur to reduce noise while preserving edges
            img_array = cv2.GaussianBlur(img_array, (3,3), 0)
            
            # 2. Apply adaptive thresholding
            img_array = cv2.adaptiveThreshold(
                img_array,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,  # Block size
                2    # C constant
            )
            
            # 3. Remove small noise using morphological operations
            kernel = np.ones((2,2), np.uint8)
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel)
            
            # 4. Convert back to PIL
            image = Image.fromarray(img_array)
            
            # Now apply Kraken's binarization with parameters tuned for Arabic text
            bw_img = kraken.binarization.nlbin(
                image,
                threshold=0.6,    # Higher threshold for clearer text
                zoom=1.0,         # No zoom to preserve details
                escale=2.0,       # Increased edge scale for Arabic script
                border=0.1,
                perc=85,          # Higher percentage for better text extraction
                range=20,
                low=10,           # Adjusted for better contrast
                high=95
            )
            
            # Your image is already at a good resolution (1056 × 1500)
            print("Starting text line detection...")
            
            # Convert to numpy array for preprocessing
            img_array = np.array(bw_img)
            
            # Enhance text lines
            # 1. Light denoising
            img_array = cv2.fastNlMeansDenoising(img_array, None, h=10)
            
            # 2. Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img_array = clahe.apply(img_array)
            
            # 3. Light morphological operations to connect text components
            kernel = np.ones((2,2), np.uint8)
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL
            bw_img = Image.fromarray(img_array)
            
            print("Running page segmentation with Arabic-specific parameters...")
            segmentation_result = pageseg.segment(
                bw_img,
                text_direction='horizontal-rl',  # Right-to-left for Arabic
                scale=1.5,  # Slightly increased scale for better line detection
                maxcolseps=0,  # Disable column separation for Quran pages
                black_colseps=False,
                no_hlines=True,
                pad=3  # Minimal padding to avoid merging lines
            )
            
            # Get line boxes from segmentation result
            line_boxes = []
            try:
                # Try getting lines property first
                if hasattr(segmentation_result, 'lines'):
                    line_boxes = segmentation_result.lines
                # Fallback to segments if lines is not available
                elif hasattr(segmentation_result, 'segments'):
                    line_boxes = segmentation_result.segments
            except Exception as e:
                print(f"Error accessing segmentation results: {e}")
            
            print(f"Found {len(line_boxes)} text lines")
            
            if len(line_boxes) == 0:
                print("First attempt found no lines, trying alternative parameters...")
                # Try alternative segmentation
                img_array = np.array(bw_img)
                # Apply stronger morphological operation
                kernel = np.ones((3,3), np.uint8)
                img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
                bw_img = Image.fromarray(img_array)
                
                segmentation_result = pageseg.segment(
                    bw_img,
                    text_direction='horizontal-rl',
                    scale=2.0,  # Increased scale
                    maxcolseps=1,
                    black_colseps=False,
                    no_hlines=False
                )
                
                # Get line boxes from second attempt
                try:
                    if hasattr(segmentation_result, 'lines'):
                        line_boxes = segmentation_result.lines
                    elif hasattr(segmentation_result, 'segments'):
                        line_boxes = segmentation_result.segments
                except Exception as e:
                    print(f"Error accessing segmentation results in second attempt: {e}")
                
                print(f"Second attempt found {len(line_boxes)} text lines")
            
            # Convert image to tensor with proper dimensions (B, C, H, W)
            img_np = np.array(bw_img)
            if len(img_np.shape) == 2:
                img_np = img_np[np.newaxis, np.newaxis, :, :]  # Add batch and channel dimensions
            elif len(img_np.shape) == 3:
                img_np = img_np[np.newaxis, :, :, :]  # Add batch dimension
            img_tensor = torch.from_numpy(img_np).float()
            
            # Process each text line separately
            lines = []
            for box in line_boxes:
                # Convert box coordinates to integers
                try:
                    if hasattr(box, 'coords'):
                        coords = box.coords
                    else:
                        coords = box
                    x1, y1, x2, y2 = map(int, coords)
                    
                    line_img = bw_img.crop((x1, y1, x2, y2))
                    # Ensure minimum dimensions and normalize
                    line_img = line_img.resize((line_img.width, 48))  # Standard height for OCR
                    line_np = np.array(line_img)
                    if len(line_np.shape) == 2:
                        line_np = line_np[np.newaxis, np.newaxis, :, :]  # (B, C, H, W)
                    elif len(line_np.shape) == 3:
                        line_np = line_np.transpose(2, 0, 1)[np.newaxis, :, :, :]  # Move channels to correct position
                    line_tensor = torch.from_numpy(line_np).float()
                    line_tensor = line_tensor / 255.0  # Normalize to [0,1]
                    lines.append(line_tensor)
                except Exception as e:
                    print(f"Error processing line box: {e}")
                    continue
            
            # Stack all lines into a single batch
            if lines:
                batched_lines = torch.cat(lines, dim=0)
                # Recognize text with proper bounds parameter
                result = self.model.predict(batched_lines)
            else:
                return "[No text lines detected]"
            
            # Join all text lines
            text = '\n'.join([line.prediction for line in result])
            
            return text
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            return f"[OCR ERROR] {str(e)}\n{trace}"