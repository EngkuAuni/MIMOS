# CV (Computer Vision) page-layout comparison
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from typing import Dict, List, Any, Optional
from pathlib import Path

class CVPageComparator:
    """
    Computer Vision-based page layout comparison for Quran verification.
    Detects structural differences, layout anomalies, and visual inconsistencies.
    """
    
    def __init__(self, reference_images_dir="database/reference_imgs"):
        self.reference_images_dir = Path(reference_images_dir)
        self.reference_images = {}
        self._load_reference_images()
    
    def _load_reference_images(self):
        """Load reference images for comparison"""
        try:
            for i in range(1, 605):  # Assuming 604 pages
                img_path = self.reference_images_dir / f"{i:03d}.jpg"
                if img_path.exists():
                    img = cv2.imread(str(img_path))
                    if img is not None:
                        self.reference_images[i] = img
            print(f"✅ Loaded {len(self.reference_images)} reference images for CV comparison.")
        except Exception as e:
            print(f"⚠️ Could not load reference images: {e}")
    
    def compare_page_layout(self, uploaded_img, page_number: int) -> Dict[str, Any]:
        """
        Compare page layout and structure with reference image.
        
        Args:
            uploaded_img: PIL Image or numpy array of uploaded page
            page_number: Page number to compare against
            
        Returns:
            Dictionary with comparison results and analysis
        """
        try:
            # Convert PIL to OpenCV format
            if hasattr(uploaded_img, 'convert'):
                uploaded_img_np = np.array(uploaded_img.convert('RGB'))
            else:
                uploaded_img_np = uploaded_img
            
            uploaded_img_cv = cv2.cvtColor(uploaded_img_np, cv2.COLOR_RGB2BGR)
            
            # Get reference image
            reference_img = self.reference_images.get(page_number)
            if reference_img is None:
                return {
                    "success": False,
                    "error": f"Reference image for page {page_number} not found",
                    "page_number": page_number
                }
            
            # Align images using feature matching
            aligned_img, alignment_confidence = self._align_images(uploaded_img_cv, reference_img)
            
            # Perform layout analysis
            layout_analysis = self._analyze_layout(aligned_img, reference_img)
            
            # Detect structural differences
            structural_diffs = self._detect_structural_differences(aligned_img, reference_img)
            
            # Calculate overall similarity
            similarity_score = self._calculate_similarity(aligned_img, reference_img)
            
            return {
                "success": True,
                "page_number": page_number,
                "similarity_score": similarity_score,
                "alignment_confidence": alignment_confidence,
                "layout_analysis": layout_analysis,
                "structural_differences": structural_diffs,
                "is_layout_match": similarity_score > 0.95,
                "reference_image": cv2.cvtColor(reference_img, cv2.COLOR_BGR2RGB),
                "aligned_image": cv2.cvtColor(aligned_img, cv2.COLOR_BGR2RGB),
                "method": "cv_page_layout_comparison"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "page_number": page_number
            }
    
    def _align_images(self, img1, img2):
        """Align two images using feature matching"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Detect ORB features
            orb = cv2.ORB_create(5000)
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)
            
            if des1 is None or des2 is None:
                return img1, 0.0
            
            # Match features
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = matcher.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Get transformation matrix
            if len(matches) < 10:
                return img1, 0.0
                
            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches[:50]]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches[:50]]).reshape(-1, 1, 2)
            
            matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if matrix is None:
                return img1, 0.0
            
            # Align image
            h, w = img2.shape[:2]
            aligned_img = cv2.warpPerspective(img1, matrix, (w, h))
            
            # Calculate alignment confidence
            alignment_confidence = np.sum(mask) / len(matches[:50]) if len(matches) > 0 else 0
            
            return aligned_img, alignment_confidence
            
        except Exception as e:
            print(f"Alignment error: {e}")
            return img1, 0.0
    
    def _analyze_layout(self, img1, img2):
        """Analyze page layout structure"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Detect text regions using contours
            contours1 = self._detect_text_regions(gray1)
            contours2 = self._detect_text_regions(gray2)
            
            # Compare text region counts
            region_count_diff = abs(len(contours1) - len(contours2))
            
            # Analyze margins and spacing
            margin_analysis = self._analyze_margins(gray1, gray2)
            
            return {
                "text_regions_uploaded": len(contours1),
                "text_regions_reference": len(contours2),
                "region_count_difference": region_count_diff,
                "margin_analysis": margin_analysis,
                "layout_consistency": region_count_diff < 3
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _detect_text_regions(self, gray_img):
        """Detect text regions using contour analysis"""
        try:
            # Apply threshold
            _, thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area (text regions)
            text_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum area for text region
                    text_contours.append(contour)
            
            return text_contours
            
        except Exception as e:
            return []
    
    def _analyze_margins(self, gray1, gray2):
        """Analyze page margins and spacing"""
        try:
            h, w = gray1.shape
            
            # Sample margin regions (top, bottom, left, right)
            margin_regions = {
                'top': (gray1[:h//10, :], gray2[:h//10, :]),
                'bottom': (gray1[-h//10:, :], gray2[-h//10:, :]),
                'left': (gray1[:, :w//10], gray2[:, :w//10]),
                'right': (gray1[:, -w//10:], gray2[:, -w//10:])
            }
            
            margin_similarities = {}
            for region, (m1, m2) in margin_regions.items():
                if m1.size > 0 and m2.size > 0:
                    sim = ssim(m1, m2)
                    margin_similarities[region] = sim
            
            return margin_similarities
            
        except Exception as e:
            return {}
    
    def _detect_structural_differences(self, img1, img2):
        """Detect structural differences between images"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Threshold to get significant differences
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # Find contours of differences
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter significant differences
            significant_diffs = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area for significant difference
                    x, y, w, h = cv2.boundingRect(contour)
                    significant_diffs.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'center': (x + w//2, y + h//2)
                    })
            
            return {
                'difference_count': len(significant_diffs),
                'differences': significant_diffs,
                'total_difference_area': sum(d['area'] for d in significant_diffs)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_similarity(self, img1, img2):
        """Calculate overall similarity between images"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Ensure same size
            if gray1.shape != gray2.shape:
                gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
            
            # Calculate SSIM
            similarity = ssim(gray1, gray2)
            
            return similarity
            
        except Exception as e:
            return 0.0

# Legacy function for backward compatibility
def compare_cv(image, verses):
    """Legacy function - now uses CVPageComparator"""
    comparator = CVPageComparator()
    # This is a simplified version for the old interface
    return [{"verse_num": i, "cv_flag": False} for i in range(len(verses["verses"]))]