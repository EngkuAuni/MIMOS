# Triangulation Method for Quran Verification

## Overview

The Quran Verification Engine uses a **triangulation method** combining three independent verification approaches to maximize accuracy and catch different types of errors. This document explains how the triangulation method works and why it's essential for KDN compliance.

## The Three Verification Methods

### 1. 🤖 OCR (Optical Character Recognition)
**Purpose:** Extract text by verse and identify each character and diacritic  
**Technology:** QariOCR (Fine-tuned Vision-Language Model)  
**Location:** `triangulation/ocr_compare.py`

**How it works:**
- Uses fine-tuned QariOCR model to extract text from page images
- Performs verse-level segmentation
- Identifies individual characters and diacritics
- Compares extracted text against database using fuzzy matching

**Strengths:**
- High accuracy for general text extraction
- Understands Arabic and Uthmani script structure
- Can handle complex layouts

**Limitations:**
- May auto-correct errors (trained on mostly correct examples)
- Can miss subtle diacritic differences
- Subject to model memorization bias

**Implementation:**
```python
from triangulation.ocr_compare import compare_ocr

# OCR extraction returns verses
ocr_matches = compare_ocr(verses, db_verses)
# Returns similarity scores for each verse
```

### 2. 🖼️ CV (Computer Vision) - Page Overlay Comparison
**Purpose:** Pixel-perfect visual comparison for diacritic detection  
**Technology:** OpenCV + SSIM (Structural Similarity Index)  
**Location:** `triangulation/cv_compare.py` and `verification/image_comparator.py`

**How it works:**
- Loads reference image from database
- Aligns uploaded page with reference using feature matching (ORB)
- Performs pixel-level comparison using SSIM
- Highlights differences with red bounding boxes
- Detects variations as small as 1-2 pixels

**Strengths:**
- Pixel-level accuracy for diacritic detection
- No AI hallucination or memorization
- Catches subtle visual differences
- Independent of OCR limitations

**Limitations:**
- Requires reference images (604 pages)
- Needs manual page number input
- Slightly slower than OCR-only

**Implementation:**
```python
from verification.image_comparator import ImageComparator

comparator = ImageComparator()
result = comparator.compare_page(uploaded_image, page_number)
# Returns similarity score, difference count, visualizations
```

### 3. 🔐 Hash (Cryptographic Verification)
**Purpose:** Cryptographic integrity checking  
**Technology:** SHA256 hashing  
**Location:** `triangulation/hash_compare.py`

**How it works:**
- Computes SHA256 hash of extracted text
- Compares against pre-computed database hashes
- Supports multiple text variants (original, normalized, no-diacritics)
- Provides cryptographic proof of exact match

**Strengths:**
- Exact mathematical verification
- Fast computation
- Supports different normalization levels
- Tamper-proof

**Limitations:**
- Requires exact character match
- Single character difference = hash mismatch
- No tolerance for OCR errors

**Implementation:**
```python
from triangulation.hash_compare import compare_hash

hash_flags = compare_hash(verses, db_verses)
# Returns hash mismatch flags for each verse
```

## Why Triangulation?

### The Problem with Single-Method Verification

Each verification method has strengths and weaknesses:

- **OCR alone**: Fast but may auto-correct errors
- **CV alone**: Accurate but requires reference images
- **Hash alone**: Exact but no tolerance for minor differences

### The Solution: Triangulation

Triangulation combines all three methods to:
1. **Catch different error types** - OCR catches text errors, CV catches visual differences, Hash catches exact mismatches
2. **Cross-verify results** - Methods confirm or contradict each other
3. **Increase confidence** - Agreement between methods = high confidence
4. **Identify inconsistencies** - Disagreement = need for manual review

### Example: Diacritic Error Detection

**Scenario:** Page has incorrect diacritic (fatha instead of kasra)

| Method | Result | Status |
|--------|--------|--------|
| OCR | May auto-correct to correct diacritic | ❌ Missed |
| CV | Catches pixel-level difference | ✅ Detected |
| Hash | Hash mismatch due to character difference | ✅ Detected |

**Triangulation Result:** 2/3 methods detected error → **Manual review required**

## Triangulation Flow

```
Uploaded Page
     │
     ├──→ OCR: Extract text
     │         ↓
     │    Compare with DB (fuzzy match)
     │         ↓
     │    OCR Match Score
     │
     ├──→ CV: Load reference image
     │         ↓
     │    Align and compare pixels
     │         ↓
     │    Similarity Score + Differences
     │
     └──→ Hash: Compute text hash
              ↓
         Compare with DB hash
              ↓
         Hash Match/Mismatch
              ↓
    ┌─────────┴─────────┐
    │                   │
Triangulation        Decision
    │                   │
    │           ┌───────┴───────┐
    │           │               │
         All agree    Disagreement
    │           │               │
    │      ✅ Verified    ⚠️ Review
    │
Final Report
```

## Database: Tanzil vs KDN

### Tanzil Database

**What is Tanzil?**
- Tanzil is an open-source Quran text project
- Provides Unicode text of Quran in Uthmani script
- Standard reference for Quranic text representation

**Is it "raw Unicode"?**
Yes and no:
- **Yes**: It uses Unicode encoding (UTF-8) to represent Arabic text
- **Not exactly "raw"**: It follows Unicode Arabic Standard (U+0600–U+06FF range)
- **Uthmani Script**: Uses specific Unicode characters for Uthmani text features

**Tanzil Uthmani Text Characteristics:**
- Full diacritics (harakat, tanween, etc.)
- Uthmani-specific features (like special Alif forms)
- Standardized spacing and line breaks
- Warsh or Hafs reading variants

**Limitations:**
- May have minor differences from actual printed Mushaf
- Not publisher-specific
- No visual/image data (text only)
- May not match KDN-verified pages exactly

### KDN Database (Not Available)

**Why differences occur:**
- KDN has official verification standards
- Different publishers may have slight variations
- KDN compliance requires exact match with approved version
- Visual differences may exist even with same Unicode

**The Challenge:**
- You don't have access to KDN's official database
- Tanzil is closest available standard
- Must rely on visual comparison (CV method) for exact verification

**Solution:**
Use reference images (`database/reference_imgs/`) from KDN-verified Quran pages for CV comparison!

## Implementation in Engine

### Current Workflow

The engine currently uses triangulation in `app_enhanced.py`:

```python
# Triangulation verification
ocr_matches = compare_ocr(verses, db_verses)      # Method 1: OCR
cv_flags = compare_cv(preprocessed_img, verses)   # Method 2: CV
hash_flags = compare_hash(verses, db_verses)      # Method 3: Hash

# Image Comparison (Enhanced CV)
image_comparison_result = image_comparator.compare_page(preprocessed_img, page_number)
```

### Integration Points

1. **OCR Extraction** (`models/qari_ocr.py`)
   - Extracts text from image
   - Returns verses with confidence scores

2. **Verse Segmentation** (`segmentation/verse_segmenter.py`)
   - Splits text into individual verses
   - Prepares for database comparison

3. **Database Lookup** (`database/uthmani_db.py`)
   - Retrieves reference verses from Tanzil
   - Returns text variants and hashes

4. **Triangulation Comparison** (`triangulation/`)
   - Compares across all three methods
   - Generates flags and scores

5. **Image Comparison** (`verification/image_comparator.py`)
   - Performs pixel-perfect visual comparison
   - Highlights differences

## Future Enhancement: LLM + RAG for Anomaly Suggestions

### Planned Addition

**Purpose:** Provide intelligent suggestions on detected anomalies  
**Technology:** Large Language Model + Retrieval-Augmented Generation

**How it will work:**
1. Extract anomalies from triangulation results
2. Retrieve relevant KDN guidelines using RAG
3. Generate context-aware suggestions using LLM
4. Provide explanations and remediation steps

**Expected Capabilities:**
- Explain why an error was flagged
- Reference specific KDN guidelines
- Suggest correction approaches
- Provide educational context

**Status:** Not yet implemented - planned for future version

## Recommendations

### For Best Results

1. **Use Image Comparison as Primary Method**
   - Most reliable for diacritic detection
   - No OCR hallucination issues
   - Catches KDN-verified differences

2. **Use OCR for Text Extraction Only**
   - Extract text for reference
   - Don't rely solely on OCR for verification
   - Use OCR results for downstream processing

3. **Use Hash for Exact Matching**
   - Quick integrity check
   - Cryptographic verification
   - Catches character-level errors

4. **Cross-Verify with All Methods**
   - Run all three methods
   - Compare results
   - Flag disagreements for review

### Data Collection Priorities

To improve triangulation accuracy:

1. **KDN Reference Images** (Critical)
   - Collect all 604 verified KDN pages
   - Use as ground truth for CV comparison
   - Ensure high-resolution scans

2. **Real Error Examples** (High Priority)
   - Collect actual printing errors
   - Document KDN-non-compliant pages
   - Use for training better OCR

3. **Synthetic Error Generation** (Medium Priority)
   - Generate more diverse error patterns
   - Focus on subtle diacritic variations
   - Improve error detection coverage

## Conclusion

The triangulation method provides robust verification by combining multiple independent approaches. While each method has limitations, together they provide comprehensive error detection suitable for KDN compliance standards.

**Key Takeaways:**
- Use all three methods for best results
- Image Comparison catches what OCR misses
- Tanzil DB is reference, not ground truth
- Need KDN-verified images for exact compliance
- Future: Add LLM+RAG for intelligent suggestions


