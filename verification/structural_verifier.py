"""
Structural Verification Module
Handles verse segmentation, surah identification, and layout verification
"""

import re
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from PIL import Image

class StructuralVerifier:
    """Advanced structural verification for Uthmani Quran pages"""
    
    def __init__(self):
        self.ayah_patterns = self._load_ayah_patterns()
        self.surah_patterns = self._load_surah_patterns()
        self.layout_templates = self._load_layout_templates()
    
    def _load_ayah_patterns(self) -> Dict[str, str]:
        """Load Uthmani ayah number patterns"""
        return {
            'uthmani_ayah': r'(\d+)\s*',  # Uthmani ayah numbers
            'bismillah': r'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
            'verse_separator': r'[۞۩]',  # Uthmani verse separators
            'sajdah': r'سَجَدَ',  # Prostration markers
        }
    
    def _load_surah_patterns(self) -> Dict[str, str]:
        """Load surah identification patterns"""
        return {
            'surah_title': r'سُورَةُ\s+(\S+)',
            'bismillah_start': r'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
            'page_number': r'صفحة\s+(\d+)',
        }
    
    def _load_layout_templates(self) -> Dict:
        """Load Uthmani layout templates"""
        return {
            'margin_ratio': 0.1,  # Expected margin ratio
            'line_spacing': 0.05,  # Expected line spacing
            'text_region': (0.1, 0.1, 0.8, 0.8),  # (x, y, width, height)
        }
    
    def verify_structure(self, image: np.ndarray, extracted_text: str, page_number: int) -> Dict:
        """
        Comprehensive structural verification
        
        Args:
            image: Input page image
            extracted_text: OCR extracted text
            page_number: Page number for verification
            
        Returns:
            Dict with structural verification results
        """
        results = {
            'verse_segmentation': {},
            'surah_identification': {},
            'layout_verification': {},
            'page_verification': {},
            'anomalies': []
        }
        
        # Verse segmentation
        verse_results = self._verify_verse_segmentation(extracted_text)
        results['verse_segmentation'] = verse_results
        
        # Surah identification
        surah_results = self._verify_surah_identification(extracted_text, page_number)
        results['surah_identification'] = surah_results
        
        # Layout verification
        layout_results = self._verify_layout(image)
        results['layout_verification'] = layout_results
        
        # Page verification
        page_results = self._verify_page_number(image, page_number)
        results['page_verification'] = page_results
        
        return results
    
    def _verify_verse_segmentation(self, text: str) -> Dict:
        """Verify verse segmentation accuracy"""
        # Extract ayah numbers
        ayah_numbers = re.findall(self.ayah_patterns['uthmani_ayah'], text)
        
        # Check for bismillah
        has_bismillah = bool(re.search(self.surah_patterns['bismillah_start'], text))
        
        # Validate ayah sequence
        ayah_sequence_valid = self._validate_ayah_sequence(ayah_numbers)
        
        return {
            'ayah_count': len(ayah_numbers),
            'has_bismillah': has_bismillah,
            'sequence_valid': ayah_sequence_valid,
            'ayah_numbers': ayah_numbers
        }
    
    def _verify_surah_identification(self, text: str, page_number: int) -> Dict:
        """Verify surah identification"""
        # Extract surah title
        surah_match = re.search(self.surah_patterns['surah_title'], text)
        surah_name = surah_match.group(1) if surah_match else None
        
        # Map page to expected surah
        expected_surah = self._get_expected_surah(page_number)
        
        # Check bismillah presence
        has_bismillah = bool(re.search(self.surah_patterns['bismillah_start'], text))
        
        return {
            'detected_surah': surah_name,
            'expected_surah': expected_surah,
            'surah_match': surah_name == expected_surah if expected_surah else None,
            'has_bismillah': has_bismillah
        }
    
    def _verify_layout(self, image: np.ndarray) -> Dict:
        """Verify Uthmani layout compliance"""
        height, width = image.shape[:2]
        
        # Check margins
        margin_ratio = self._calculate_margin_ratio(image)
        margin_valid = abs(margin_ratio - self.layout_templates['margin_ratio']) < 0.05
        
        # Check text region
        text_region = self._detect_text_region(image)
        text_region_valid = self._validate_text_region(text_region, (width, height))
        
        # Check line spacing
        line_spacing = self._calculate_line_spacing(image)
        spacing_valid = abs(line_spacing - self.layout_templates['line_spacing']) < 0.02
        
        return {
            'margin_ratio': margin_ratio,
            'margin_valid': margin_valid,
            'text_region': text_region,
            'text_region_valid': text_region_valid,
            'line_spacing': line_spacing,
            'spacing_valid': spacing_valid
        }
    
    def _verify_page_number(self, image: np.ndarray, page_number: int) -> Dict:
        """Verify page number accuracy"""
        # Extract page number from image
        detected_page = self._extract_page_number(image)
        
        return {
            'detected_page': detected_page,
            'expected_page': page_number,
            'page_match': detected_page == page_number
        }
    
    def _validate_ayah_sequence(self, ayah_numbers: List[str]) -> bool:
        """Validate ayah number sequence"""
        if not ayah_numbers:
            return False
        
        try:
            numbers = [int(num) for num in ayah_numbers]
            # Check if sequence is consecutive
            return numbers == list(range(min(numbers), max(numbers) + 1))
        except ValueError:
            return False
    
    def _get_expected_surah(self, page_number: int) -> Optional[str]:
        """Get expected surah for page number"""
        # This would be loaded from a page-to-surah mapping database
        # For now, return a placeholder
        surah_mapping = {
            1: "Al-Fatiha",
            2: "Al-Baqarah",
            # ... complete mapping
        }
        return surah_mapping.get(page_number)
    
    def _calculate_margin_ratio(self, image: np.ndarray) -> float:
        """Calculate margin ratio from image"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect text regions
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 0.0
        
        # Calculate bounding box
        x, y, w, h = cv2.boundingRect(np.concatenate(contours))
        
        # Calculate margin ratio
        total_area = image.shape[0] * image.shape[1]
        text_area = w * h
        margin_area = total_area - text_area
        
        return margin_area / total_area
    
    def _detect_text_region(self, image: np.ndarray) -> Tuple[int, int, int, int]:
        """Detect main text region in image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Use morphological operations to detect text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(gray, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return (0, 0, image.shape[1], image.shape[0])
        
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        return (x, y, w, h)
    
    def _validate_text_region(self, text_region: Tuple[int, int, int, int], image_size: Tuple[int, int]) -> bool:
        """Validate text region against expected layout"""
        x, y, w, h = text_region
        img_w, img_h = image_size
        
        # Check if text region is within expected bounds
        expected_x = int(img_w * self.layout_templates['text_region'][0])
        expected_y = int(img_h * self.layout_templates['text_region'][1])
        expected_w = int(img_w * self.layout_templates['text_region'][2])
        expected_h = int(img_h * self.layout_templates['text_region'][3])
        
        # Allow some tolerance
        tolerance = 0.1
        return (abs(x - expected_x) < img_w * tolerance and
                abs(y - expected_y) < img_h * tolerance and
                abs(w - expected_w) < img_w * tolerance and
                abs(h - expected_h) < img_h * tolerance)
    
    def _calculate_line_spacing(self, image: np.ndarray) -> float:
        """Calculate average line spacing"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Find line positions
        line_positions = []
        for i in range(horizontal_lines.shape[0]):
            if np.any(horizontal_lines[i, :] > 0):
                line_positions.append(i)
        
        if len(line_positions) < 2:
            return 0.0
        
        # Calculate average spacing
        spacings = [line_positions[i+1] - line_positions[i] for i in range(len(line_positions)-1)]
        avg_spacing = np.mean(spacings)
        
        # Normalize by image height
        return avg_spacing / image.shape[0]
    
    def _extract_page_number(self, image: np.ndarray) -> Optional[int]:
        """Extract page number from image using OCR"""
        # This would use OCR to extract page number
        # For now, return None as placeholder
        return None
