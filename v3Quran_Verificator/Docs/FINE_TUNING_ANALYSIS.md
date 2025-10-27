# FT1_QariOCR Fine-Tuning Analysis & Recommendations

## Executive Summary

This document analyzes the training data used for FT1_QariOCR fine-tuning, identifies root causes of hallucination issues, and provides actionable recommendations for improving OCR accuracy and error detection.

## Current Training Data Analysis

### Dataset Overview

**Total Samples:** 1,128
- **Training:** 958 samples (85%)
- **Validation:** 170 samples (15%)

### Data Breakdown

#### 1. Perfect Uthmani Text (604 samples, 53.5%)

**Source:** Clean Quran pages from `database/reference_imgs/`  
**Purpose:** Text extraction training  
**Characteristics:**
- Full Uthmani script with correct diacritics
- All examples are correct/perfect
- Represents ideal/standard text

**Problems:**
- Model learns to auto-correct errors
- Bias toward "perfect" standard text
- Memorization of standard Uthmani patterns
- Hallucination risk when seeing actual errors

#### 2. Synthetic Errors (400 samples, 35.5%)

**Source:** Programmatically generated errors  
**Purpose:** Error detection training  
**Error Types:** 39 categories across:
- **Diacritic errors:** Fatha, kasra, damma, shadda, sukun
- **Character errors:** Substitution, addition, deletion, inversion
- **Layout errors:** Spacing, alignment, margins
- **Structural errors:** Verse separation, surah titles

**Severity Levels:** CRITICAL / MAJOR / MINOR

**Problems:**
- May be too artificial for real-world scenarios
- Synthetic errors may not match actual printing errors
- Limited diversity in error patterns

#### 3. KDN Official Examples (124 samples, 11.0%)

**Source:** Real audit examples from official KDN guidelines  
**Purpose:** Visual learning and compliance  
**Characteristics:**
- Actual errors from KDN inspections
- Real-world error patterns
- Compliance-focused examples

**Problems:**
- Too few examples for effective learning
- Insufficient representation of error diversity
- May not cover all error scenarios

## Critical Issue Identified

### Root Cause: Data Imbalance Causing Hallucination

**The Problem:**

Training Data Ratio:
- Correct examples: 604 (perfect) + 0 (in synthetic) = **604 samples**
- Error examples: 400 (synthetic) + 124 (KDN) = **524 samples**

**But MORE IMPORTANTLY:**

The model sees **604 examples** where the "correct" answer is ALWAYS the standard Uthmani text from the database. This creates strong memorization bias.

**Result:**
- Model MEMORIZES standard text instead of reading pixels
- Auto-corrects errors instead of reporting them
- Matches database instead of extracting actual text
- Misses subtle diacritic variations

### Why This Causes Hallucination

```
Training Flow:
1. Model sees image → extracts text
2. Model compares to database → "matches standard text"
3. Model outputs "standard text" → even if image has errors

Result: Hallucination where model "sees" what it expects,
        not what's actually in the image
```

### Evidence from Testing

Your testing revealed:
- **QariOCR gave exact wordings from database** - even when input had different diacritics
- **Tesseract showed actual extraction** - but poorer Arabic recognition
- **Image Comparison caught the differences** - pure pixel analysis

This confirms the model is memorizing, not reading pixels.

## How to Improve: Four Options

### Option 1: Add More Real Error Examples ⭐ RECOMMENDED

**What You Need:**
- Collect 500-1000 REAL Quran pages with actual printing errors
- Include diacritic variations from different publishers
- Pages with missing characters, wrong diacritics, etc.
- From actual KDN audits or real-world printing errors

**Why This Works:**
- Model learns actual error patterns (not synthetic)
- Reduces bias toward "perfect" standard text
- Better error detection without auto-correction
- Real-world accuracy

**Where to Get Data:**
- KDN historical audit records
- Real printing errors from publishers
- Community-reported errors
- Your existing KDN verification examples

**Implementation:**
1. Collect real error pages from KDN archives
2. Manually annotate error locations and types
3. Add to training dataset
4. Retrain model with balanced dataset (50% correct, 50% errors)

### Option 2: Improve Prompting ⭐ EASIEST

**Current Prompt:** "Extract text from image"  
**Better Prompt:** "Extract EXACTLY what you see, including errors"

**Why This Works:**
- Explicitly instructs model NOT to auto-correct
- Forces model to report raw extraction
- Can be implemented immediately without retraining

**Implementation:**

Update `models/qari_ocr.py` (lines 118-132):

```python
# Current (problematic):
prompt = "Extract the Quranic text from this image..."

# Better:
prompt = """
Extract the Quranic text from this image EXACTLY as it appears.
DO NOT auto-correct errors.
DO NOT match to database text.
DO NOT fill in missing characters.
Report exactly what you see, including:
- Missing characters
- Wrong diacritics
- Extra characters
- Any variations from standard text

If you cannot read a character, use underscore (_).
Extract character by character, maintaining exact spacing.
"""
```

**Advantages:**
- Immediate implementation
- No retraining required
- Forces model to report actual pixels
- Can combine with current fine-tuned model

### Option 3: Balance Training Data ⭐ GOOD COMPLEMENT

**What to Add:**
- 500-1000 more synthetic error examples
- Include subtle diacritic differences (fatha vs kasra)
- Add pages with missing/wrong dots (نقطة)
- Simulate real-world printing variations

**Why This Works:**
- More error examples = better error detection
- Model sees more diverse error patterns
- Balances training data distribution
- Complements real error examples

**Implementation:**
1. Enhance synthetic error generator
2. Add more subtle error patterns
3. Increase diversity of error types
4. Retrain with balanced dataset

### Option 4: Adjust Training Strategy ⭐ ADVANCED

**What to Change:**
- Use different loss function for error detection
- Add contrastive learning for error vs correct
- Fine-tune vision layers more aggressively
- Use curriculum learning (easy → hard errors)

**Why This Works:**
- Different training approach = different learning
- Model learns error patterns more explicitly
- Better separation between correct and error cases
- More robust error detection

**Technical Details:**

**Contrastive Learning:**
```python
# Train model to distinguish between:
- Correct pages (positive examples)
- Error pages (negative examples)
# Goal: Learn difference patterns explicitly
```

**Curriculum Learning:**
```python
# Phase 1: Easy errors (obvious mistakes)
# Phase 2: Medium errors (subtle differences)
# Phase 3: Hard errors (very similar to correct)
```

## Best Approach: Hybrid Strategy

### Immediate Actions (No Training Needed)

1. ✅ **Improve Prompting** in `qari_ocr.py`
   - Add explicit instructions not to auto-correct
   - Force exact pixel reporting
   - Use underscore for unreadable characters

2. ✅ **Use Image Comparison** as primary verification method
   - Most reliable for diacritic detection
   - No OCR hallucination issue
   - Pure pixel analysis

3. ✅ **Keep Tesseract** for cross-verification
   - Raw extraction without AI processing
   - No memorization
   - Shows actual OCR output

### Short-Term Actions (Collect Data, Then Fine-Tune)

1. **Collect Real Error Examples** (500-1000 samples)
   - KDN historical audits
   - Real printing errors
   - Community reports

2. **Add More Synthetic Errors** (500-1000 samples)
   - Subtle diacritic variations
   - Missing/wrong dots
   - Real-world printing artifacts

3. **Balance Training Data** (50% correct, 50% errors)
   - Remove bias toward perfect examples
   - Equal representation of error types
   - Diverse error patterns

4. **Retrain Model** with updated dataset
   - Use improved prompt in training
   - Better loss function for error detection
   - More training epochs

### Long-Term Actions (Production-Ready)

1. **Build Large Dataset** (5000+ real-world errors)
   - Comprehensive error coverage
   - Various publishers and printing methods
   - Historical error patterns

2. **Fine-Tune Vision Encoder** specifically for Arabic
   - Better Arabic character recognition
   - Diacritic-aware features
   - Uthmani script specialization

3. **Multi-Task Learning** (extraction + detection)
   - Joint training of text extraction and error detection
   - Better feature representation
   - Shared knowledge between tasks

4. **Iterative Improvement Loop**
   - Collect errors from verification system
   - Add to training dataset
   - Retrain periodically
   - Continuous improvement

## Data Needed for Better OCR

### High Priority

1. **Real Printing Errors** (500-1000 examples)
   - Different publishers and printing methods
   - Actual diacritic mistakes
   - Missing characters in real pages
   - Wrong letter forms

2. **Subtle Diacritic Variations** (300-500 examples)
   - Pages with different diacritic styles
   - Fatha vs Kasra variations
   - Tanween differences (ً vs ٌ vs ٍ)
   - Hamza form variations (ء vs إ vs أ)

3. **Multi-Line Extraction Examples** (200-300 examples)
   - Pages with complex layouts
   - Overlapping text
   - Margin notes
   - Page numbers

### Medium Priority

4. **Error Localization Examples** (200-300 examples)
   - Bounding boxes for errors
   - Pixel-level error annotations
   - Region of interest marking
   - Visual error highlighting

5. **Different Font/Script Variations** (200-300 examples)
   - Various Uthmani script styles
   - Different publishers' fonts
   - Historical script variations
   - Regional printing differences

### Low Priority

6. **Augmented Synthetic Errors** (500-1000 examples)
   - More diverse error patterns
   - Edge cases and rare errors
   - Complex multi-error scenarios
   - Combinations of error types

## Where to Get Data

### Real Error Examples

**Best Sources:**
- **KDN Historical Audits** - Official records of errors
- **Real Printing Errors** - From publishers' records
- **Community Reports** - User-submitted errors
- **Existing Verification Examples** - Your KDN verification cases

**Collection Strategy:**
1. Request access to KDN audit archives
2. Contact publishers for error records
3. Set up community error reporting system
4. Extract errors from existing verification workflow

### Synthetic Errors

**Generation Methods:**
- Programmatically generate variations
- Use existing synthetic generator
- Add noise, blur, rotation variations
- Simulate printing artifacts
- Introduce OCR-like errors

**Enhancement Ideas:**
- Add more subtle variations
- Include region-specific error patterns
- Simulate different printing methods
- Generate rare edge cases

## Why Image Comparison Works Better

### Comparison: OCR vs Image Comparison

| Aspect | OCR (QariOCR) | Image Comparison |
|--------|---------------|------------------|
| **Training** | Requires labeled data | No training needed |
| **Bias** | Memorizes standard text | Pure pixel analysis |
| **Hallucination** | May auto-correct | No hallucination |
| **Diacritic Detection** | May miss subtle differences | Pixel-level accuracy |
| **Speed** | ~30-90 seconds | <1 second |
| **Reference Required** | Text database | Image database |
| **Dependency** | AI model | Computer vision |

### Why Image Comparison is Superior for Diacritic Detection

1. **No Training Bias**
   - Pure mathematical comparison
   - Not influenced by learned patterns
   - No memorization effects

2. **Pixel-Level Accuracy**
   - Detects differences as small as 1-2 pixels
   - Captures visual variations
   - Independent of text interpretation

3. **No Hallucination**
   - Reads actual pixels
   - Doesn't "see" what it expects
   - Shows real differences

4. **Mathematical Approach**
   - SSIM similarity index
   - Feature-based alignment
   - Contour detection
   - Proven computer vision methods

## Recommendation Summary

### Current Setup (Best Approach Until Better Data)

Your current three-method system is actually **OPTIMAL**:

1. ✅ **Image Comparison** - Primary verification (catches diacritics)
2. ✅ **QariOCR** - Text extraction (reference only)
3. ✅ **Tesseract** - Cross-verification (raw extraction)

**Why This Works:**
- Image Comparison handles what OCR can't
- QariOCR provides good text extraction when trained
- Tesseract shows actual raw output
- Triangulation provides comprehensive coverage

### Next Steps

**Priority 1: Immediate**
- Improve prompting in `qari_ocr.py`
- Continue using Image Comparison as primary method
- Collect real error examples

**Priority 2: Short-Term**
- Collect 500-1000 real error examples
- Enhance synthetic error generation
- Balance training dataset

**Priority 3: Long-Term**
- Retrain model with balanced dataset
- Fine-tune vision encoder for Arabic
- Implement multi-task learning
- Build iterative improvement loop

## Conclusion

The root cause of hallucination is **data imbalance** causing the model to memorize standard text instead of reading pixels. The solution is:

1. **Immediate:** Improve prompting, use Image Comparison
2. **Short-term:** Collect real error data, retrain with balance
3. **Long-term:** Build comprehensive dataset, continuous improvement

**Your current setup with Image Comparison + QariOCR + Tesseract is the BEST approach until you have better training data.**

The Image Comparison method solves the diacritic detection problem independently of OCR training data quality.


