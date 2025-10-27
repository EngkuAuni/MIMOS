"""
Pixel-Perfect Image Comparison Module
====================================

This module provides computer vision-based image comparison for Quran verification.
It uses OpenCV for image alignment and scikit-image for difference detection,
providing pixel-level accuracy for diacritic detection without OCR limitations.

Key Features:
- Feature-based image alignment (ORB)
- Structural Similarity Index (SSIM) comparison
- Visual difference highlighting
- Diacritic-level precision
- No AI hallucination or memorization
"""

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage import measure
import os
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ImageComparator:
    """
    Pixel-perfect image comparison for Quran verification.
    
    This class provides methods to:
    1. Align uploaded images with reference images
    2. Detect pixel-level differences
    3. Generate visual difference maps
    4. Calculate similarity scores
    """
    
    def __init__(self, reference_dir: str = "database/reference_imgs"):
        """
        Initialize the image comparator.
        
        Args:
            reference_dir: Path to directory containing reference images
        """
        self.reference_dir = reference_dir
        self.reference_cache = {}
        
        # ORB feature detector parameters
        self.orb = cv2.ORB_create(
            nfeatures=5000,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            firstLevel=0,
            WTA_K=2,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=31
        )
        
        # Feature matcher
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        logger.info(f"ImageComparator initialized with reference directory: {reference_dir}")
    
    def load_reference_image(self, page_number: int) -> Optional[np.ndarray]:
        """
        Load reference image for a specific page number.
        
        Args:
            page_number: Page number (1-604)
            
        Returns:
            Reference image as numpy array, or None if not found
        """
        if page_number in self.reference_cache:
            return self.reference_cache[page_number]
        
        # Try different naming patterns
        possible_names = [
            f"page_{page_number:03d}.jpg",
            f"page_{page_number:03d}.png",
            f"page_{page_number}.jpg",
            f"page_{page_number}.png",
            f"{page_number:03d}.jpg",
            f"{page_number:03d}.png",
            f"{page_number}.jpg",
            f"{page_number}.png"
        ]
        
        for filename in possible_names:
            filepath = os.path.join(self.reference_dir, filename)
            if os.path.exists(filepath):
                try:
                    image = cv2.imread(filepath)
                    if image is not None:
                        self.reference_cache[page_number] = image
                        logger.info(f"Loaded reference image: {filename}")
                        return image
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")
                    continue
        
        logger.warning(f"Reference image for page {page_number} not found")
        return None
    
    def align_images(self, uploaded: np.ndarray, reference: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Align uploaded image with reference image using feature matching.
        
        Args:
            uploaded: Uploaded image as numpy array
            reference: Reference image as numpy array
            
        Returns:
            Tuple of (aligned_image, alignment_confidence)
        """
        try:
            # Convert to grayscale
            gray_uploaded = cv2.cvtColor(uploaded, cv2.COLOR_BGR2GRAY)
            gray_reference = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
            
            # Detect keypoints and descriptors
            kp1, des1 = self.orb.detectAndCompute(gray_uploaded, None)
            kp2, des2 = self.orb.detectAndCompute(gray_reference, None)
            
            if des1 is None or des2 is None:
                logger.warning("No features detected in one or both images")
                return uploaded, 0.0
            
            # Match features
            matches = self.matcher.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Filter good matches
            good_matches = [m for m in matches if m.distance < 50]
            
            if len(good_matches) < 10:
                logger.warning(f"Too few good matches: {len(good_matches)}")
                return uploaded, 0.0
            
            # Calculate alignment confidence
            alignment_confidence = min(len(good_matches) / 100.0, 1.0)
            
            # Get matched points
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches[:50]]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches[:50]]).reshape(-1, 1, 2)
            
            # Find homography matrix
            matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if matrix is None:
                logger.warning("Failed to find homography matrix")
                return uploaded, 0.0
            
            # Apply transformation
            h, w = reference.shape[:2]
            aligned = cv2.warpPerspective(uploaded, matrix, (w, h))
            
            logger.info(f"Image alignment successful. Confidence: {alignment_confidence:.2f}")
            return aligned, alignment_confidence
            
        except Exception as e:
            logger.error(f"Image alignment failed: {e}")
            return uploaded, 0.0
    
    def detect_differences(self, aligned: np.ndarray, reference: np.ndarray) -> Dict:
        """
        Detect pixel-level differences between aligned and reference images.
        
        Args:
            aligned: Aligned uploaded image
            reference: Reference image
            
        Returns:
            Dictionary containing difference analysis results
        """
        try:
            # Convert to grayscale
            gray_aligned = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
            gray_reference = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
            
            # Calculate SSIM
            ssim_score, diff_img = ssim(gray_reference, gray_aligned, full=True)
            
            # Convert SSIM difference to 0-255 range
            diff_img = (diff_img * 255).astype("uint8")
            
            # Create binary difference mask
            _, thresh = cv2.threshold(diff_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
            
            # Find contours of differences
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter small contours (noise)
            min_area = 10  # Minimum area for significant differences
            significant_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            # Calculate difference regions
            diff_regions = []
            for contour in significant_contours:
                x, y, w, h = cv2.boundingRect(contour)
                diff_regions.append({
                    'bbox': (x, y, w, h),
                    'area': cv2.contourArea(contour),
                    'center': (x + w//2, y + h//2)
                })
            
            # Sort by area (largest first)
            diff_regions.sort(key=lambda x: x['area'], reverse=True)
            
            result = {
                'similarity_score': ssim_score * 100,  # Convert to percentage
                'difference_count': len(significant_contours),
                'difference_regions': diff_regions,
                'difference_mask': thresh,
                'ssim_diff_image': diff_img,
                'is_perfect_match': ssim_score > 0.99 and len(significant_contours) == 0
            }
            
            logger.info(f"Difference detection complete. Similarity: {ssim_score:.3f}, "
                       f"Differences: {len(significant_contours)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Difference detection failed: {e}")
            return {
                'similarity_score': 0.0,
                'difference_count': 0,
                'difference_regions': [],
                'difference_mask': None,
                'ssim_diff_image': None,
                'is_perfect_match': False
            }
    
    def create_visualization(self, uploaded: np.ndarray, reference: np.ndarray, 
                           diff_result: Dict) -> np.ndarray:
        """
        Create visual difference overlay on the uploaded image.
        
        Args:
            uploaded: Original uploaded image
            reference: Reference image
            diff_result: Results from detect_differences()
            
        Returns:
            Image with difference regions highlighted
        """
        try:
            # Create overlay
            overlay = uploaded.copy()
            
            # Draw difference regions
            for i, region in enumerate(diff_result['difference_regions']):
                x, y, w, h = region['bbox']
                
                # Draw bounding box
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
                
                # Add semi-transparent red fill
                roi = overlay[y:y+h, x:x+w]
                red_overlay = np.zeros_like(roi)
                red_overlay[:,:,2] = 255  # Red channel
                cv2.addWeighted(roi, 0.7, red_overlay, 0.3, 0, roi)
                
                # Add region number
                cv2.putText(overlay, str(i+1), (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            return overlay
            
        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
            return uploaded
    
    def compare_page(self, uploaded: np.ndarray, page_number: int) -> Dict:
        """
        Complete page comparison workflow.
        
        Args:
            uploaded: Uploaded image as numpy array
            page_number: Page number to compare against
            
        Returns:
            Complete comparison results
        """
        try:
            # Load reference image
            reference = self.load_reference_image(page_number)
            if reference is None:
                return {
                    'success': False,
                    'error': f'Reference image for page {page_number} not found',
                    'similarity_score': 0.0,
                    'difference_count': 0,
                    'difference_regions': [],
                    'alignment_confidence': 0.0
                }
            
            # Align images
            aligned, alignment_confidence = self.align_images(uploaded, reference)
            
            # Detect differences
            diff_result = self.detect_differences(aligned, reference)
            
            # Create visualization
            visualization = self.create_visualization(uploaded, reference, diff_result)
            
            # Compile results
            result = {
                'success': True,
                'page_number': page_number,
                'similarity_score': diff_result['similarity_score'],
                'difference_count': diff_result['difference_count'],
                'difference_regions': diff_result['difference_regions'],
                'alignment_confidence': alignment_confidence,
                'is_perfect_match': diff_result['is_perfect_match'],
                'visualization': visualization,
                'reference_image': reference,
                'aligned_image': aligned,
                'difference_mask': diff_result['difference_mask']
            }
            
            logger.info(f"Page comparison complete for page {page_number}. "
                       f"Similarity: {diff_result['similarity_score']:.2f}%, "
                       f"Differences: {diff_result['difference_count']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Page comparison failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'similarity_score': 0.0,
                'difference_count': 0,
                'difference_regions': [],
                'alignment_confidence': 0.0
            }
    
    def batch_compare(self, uploaded_images: List[np.ndarray], 
                     page_numbers: List[int]) -> List[Dict]:
        """
        Compare multiple uploaded images against their corresponding reference pages.
        
        Args:
            uploaded_images: List of uploaded images
            page_numbers: List of corresponding page numbers
            
        Returns:
            List of comparison results
        """
        results = []
        
        for uploaded, page_num in zip(uploaded_images, page_numbers):
            result = self.compare_page(uploaded, page_num)
            results.append(result)
        
        return results




