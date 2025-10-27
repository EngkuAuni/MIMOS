# Verse segmentation with ayah mapping
# Detects verse boundaries, surah titles, and page numbers from OCR text

import re
from typing import Dict, List, Optional, Tuple
from database.uthmani_db import UthmaniDB

class VerseSegmenter:
    """
    Intelligent verse segmentation for Quranic text.
    Detects verse boundaries, surah names, and attempts page identification.
    """
    
    def __init__(self, db_path="database/quran_verses.db"):
        self.db = UthmaniDB(db_path)
        
        # Common surah title patterns
        self.surah_patterns = {
            'title_pattern': re.compile(r'سورة\s+(\S+)|سُورَةُ\s+(\S+)', re.UNICODE),
            'bismillah': re.compile(r'بِسْمِ\s+اللَّهِ\s+الرَّحْمَـٰنِ\s+الرَّحِيمِ', re.UNICODE),
            'page_number': re.compile(r'صفحة\s*(\d+)|\b(\d{1,3})\s*$', re.UNICODE),
        }
        
        # Verse number markers (not always present in Uthmani text)
        self.verse_markers = [
            '۝',  # End of ayah mark
            '۩',  # Sajdah mark
            '۞',  # Rub el Hizb
        ]
        
        # Surah name mapping (first 10 for quick lookup)
        self.surah_names = {
            'الفاتحة': 1, 'الفَاتِحَة': 1,
            'البقرة': 2, 'البَقَرَة': 2,
            'آل عمران': 3, 'عِمْرَان': 3,
            'النساء': 4, 'النِّسَاء': 4,
            'المائدة': 5, 'المَائِدَة': 5,
            'الأنعام': 6, 'الأَنْعَام': 6,
            'الأعراف': 7, 'الأَعْرَاف': 7,
            'الأنفال': 8, 'الأَنفَال': 8,
            'التوبة': 9, 'التَّوْبَة': 9,
            'يونس': 10, 'يُونُس': 10,
        }
    
    def detect_surah_from_title(self, text: str) -> Optional[int]:
        """
        Detect surah number from title in text.
        
        Args:
            text: Full OCR text
            
        Returns:
            Surah number (1-114) or None
        """
        # Look for surah title pattern
        match = self.surah_patterns['title_pattern'].search(text)
        if match:
            surah_name = match.group(1) or match.group(2)
            if surah_name in self.surah_names:
                return self.surah_names[surah_name]
        
        return None
    
    def detect_page_number(self, text: str) -> Optional[int]:
        """
        Detect page number from text.
        
        Args:
            text: Full OCR text
            
        Returns:
            Page number (1-604) or None
        """
        # Look for explicit page number
        match = self.surah_patterns['page_number'].search(text)
        if match:
            page_num = int(match.group(1) or match.group(2))
            if 1 <= page_num <= 604:
                return page_num
        
        return None
    
    def detect_page_from_content(self, text: str, first_verse: str) -> Optional[int]:
        """
        Detect page number by matching text content against database.
        
        Args:
            text: Full OCR text
            first_verse: First verse text for matching
            
        Returns:
            Page number or None
        """
        # Try to find page using first verse
        if first_verse and len(first_verse) > 20:
            page_num = self.db.find_page_by_content(first_verse)
            if page_num:
                return page_num
        
        # Try with full text sample
        text_sample = text[:200]  # First 200 chars
        return self.db.find_page_by_content(text_sample)
    
    def split_verses_by_newlines(self, text: str) -> List[str]:
        """
        Split text into verse candidates by newlines.
        This is the most reliable method for well-formatted Quran text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            List of verse strings
        """
        # Split by newlines and filter empty lines
        lines = text.split('\n')
        verses = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip surah titles
            if self.surah_patterns['title_pattern'].search(line):
                continue
            
            # Skip page numbers
            if re.match(r'^\d{1,3}$', line):
                continue
            
            # Skip decorative markers
            if line in self.verse_markers:
                continue
            
            verses.append(line)
        
        return verses
    
    def match_verses_to_page(self, verses: List[str], page_num: int) -> Tuple[int, List[int]]:
        """
        Match detected verses to actual ayahs on a known page.
        
        Args:
            verses: List of verse texts
            page_num: Known page number
            
        Returns:
            (surah_number, list of ayah numbers)
        """
        # Get expected verses for this page
        page_verses = self.db.get_verses_for_page(page_num)
        
        if not page_verses:
            return (1, list(range(1, len(verses) + 1)))
        
        # For simplicity, assume verses are in order
        # TODO: Could enhance with fuzzy matching
        surah = page_verses[0]['sura']
        ayah_nums = [v['ayah'] for v in page_verses[:len(verses)]]
        
        # Pad if we have more detected verses than expected
        while len(ayah_nums) < len(verses):
            ayah_nums.append(ayah_nums[-1] + 1 if ayah_nums else 1)
        
        return (surah, ayah_nums[:len(verses)])
    
    def segment(self, ocr_data: Dict) -> Dict:
        """
        Main segmentation method. Analyzes OCR output and segments verses.
        
        Args:
            ocr_data: Dictionary with OCR results containing 'text' key
            
        Returns:
            Dictionary with segmented verses and metadata
        """
        text = ocr_data.get("text", "")
        
        if not text or not text.strip():
            return {
                "surah": None,
                "surah_title": None,
                "ayah_nums": [],
                "verses": [],
                "page_num": None,
                "juz_num": None,
                "status": "empty",
                "verse_count": 0,
                "confidence": 0.0
            }
        
        # Step 1: Split verses by newlines (most reliable for Quran text)
        verses = self.split_verses_by_newlines(text)
        
        if not verses:
            return {
                "surah": None,
                "surah_title": None,
                "ayah_nums": [],
                "verses": [],
                "page_num": None,
                "juz_num": None,
                "status": "no_verses_detected",
                "verse_count": 0,
                "confidence": 0.0
            }
        
        # Step 2: Try to detect page number
        page_num = None
        
        # Method 1: Explicit page number in text
        page_num = self.detect_page_number(text)
        
        # Method 2: Content-based detection
        if not page_num:
            page_num = self.detect_page_from_content(text, verses[0] if verses else "")
        
        # Step 3: Try to detect surah
        surah = self.detect_surah_from_title(text)
        
        # Step 4: If we have page number, match verses to it
        if page_num:
            surah, ayah_nums = self.match_verses_to_page(verses, page_num)
            page_info = self.db.get_page_info(page_num)
            surah_title = f"Surah {surah}"
            confidence = 0.8
        else:
            # Fallback: sequential numbering
            surah = surah or 1
            ayah_nums = list(range(1, len(verses) + 1))
            page_info = None
            surah_title = f"Surah {surah} (estimated)"
            confidence = 0.3
        
        return {
            "surah": surah,
            "surah_title": surah_title,
            "ayah_nums": ayah_nums,
            "verses": verses,
            "page_num": page_num,
            "juz_num": page_info.get('juz_num') if page_info else None,
            "status": "segmented",
            "verse_count": len(verses),
            "confidence": confidence,
            "method": "content_match" if page_num else "fallback"
        }


def segment_verses(ocr_data: Dict) -> Dict:
    """
    Legacy function for backward compatibility.
    Creates a segmenter and processes the OCR data.
    
    Args:
        ocr_data: Dictionary with 'text' key containing OCR output
        
    Returns:
        Segmented verses with metadata
    """
    segmenter = VerseSegmenter()
    return segmenter.segment(ocr_data)