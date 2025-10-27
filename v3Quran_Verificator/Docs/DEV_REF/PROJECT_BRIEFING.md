# PROJECT BRIEFING - v3quran_verificator

## Executive Summary

This is a production-ready Quran verification system for KDN (Kementerian Dalam Negeri) compliance, combining multiple verification methods:
1. **QariOCR** - Fine-tuned vision-language model for Arabic text extraction
2. **CV Page-Layout Comparison** - Computer vision for pixel-perfect visual comparison
3. **Hash Comparison** - Cryptographic verification
4. **Missing Line Detection** - RAG + LLM powered analysis with semantic understanding

The system uses **triangulation** to cross-verify results across multiple independent methods, ensuring accuracy for diacritic-level error detection in Uthmani script.

---
## Core Features & Architecture

### Primary Technologies
- **Streamlit** (UI - app_enhanced.py)
- **PyTorch** (QariOCR model)
- **Sentence Transformers** (RAG embeddings)
- **FAISS** (Vector database)
- **OpenCV** (Computer vision)
- **RapidFuzz** (Fuzzy matching)
- **Docker** (Deployment on Mac Studio)

### Key Components

1. **OCR Extraction** (`models/qari_ocr.py`)
   - Fine-tuned Qwen2-VL-2B-Instruct model
   - Max tokens: 2048 (full page extraction)
   - Simplified prompt to prevent repetition
   - Location: `models/FT1_QariOCR`

2. **CV Page-Layout Comparison** (`triangulation/cv_compare.py`)
   - ORB features + SSIM
   - Layout analysis
   - Reference images in `database/reference_imgs/`
   - Shows side-by-side uploaded vs reference

3. **Missing Line Detector** (`verification/missing_line_detector.py`)
   - **RAG-powered** with Sentence Transformers
   - **6,236 verse database** for semantic similarity
   - **LLM-enhanced** suggestions with context
   - Fuzzy matching with 60% threshold
   - Provides intelligent suggestions based on similar verses

4. **Hash Verification** (`triangulation/hash_compare.py`)
   - SHA256 hashing
   - Multiple variants (original, normalized, no diacritics)

5. **Database** (`database/uthmani_db.py`)
   - SQLite with Tanzil database
   - 6,236 verses (114 surahs)
   - Columns: sura_number, aya_number, text_original, text_normalized, etc.

---
## Current State (January 2025)

### What's Working
✅ **QariOCR extraction** - Fine-tuned model extracting text
✅ **CV page-layout comparison** - Detects missing lines visually
✅ **Missing line detector** - RAG + LLM system detecting missing content
✅ **Fuzzy matching** - RapidFuzz for Arabic text
✅ **Database queries** - Verse lookup and comparison
✅ **UI display** - Streamlit showing all results
✅ **Docker deployment** - Running on Mac Studio at 100.72.149.103:8501

### Recent Improvements
1. **Removed duplicate detector** - Quran legitimately repeats words
2. **RAG + LLM integration** - Semantic understanding for missing lines
   - Sentence Transformers for embeddings
   - FAISS vector index for fast similarity search
   - Context-aware suggestions
   - Similar verse retrieval
3. **Improved threshold** - 60% for RAG-enhanced detection
4. **Enhanced UI** - Shows RAG/LLM enhancement status
5. **Database schema fix** - Correct column names (sura_number, aya_number)

### Known Issues
⚠️ **QariOCR repetition** - Sometimes repeats extracted lines (prompt issue)
⚠️ **Missing line detection threshold** - May need tuning for real-world accuracy
⚠️ **Hallucination risk** - Model may auto-correct errors (training data imbalance)

---
## The Triangulation Method

See: `Docs/TRIANGULATION_METHOD.md`

Three independent verification methods:

1. **OCR** - Text extraction and comparison
2. **CV** - Pixel-perfect visual comparison  
3. **Hash** - Cryptographic integrity check

**Why Triangulation?**
- Each method has limitations
- Combined approaches catch different error types
- Cross-verification increases confidence
- Independent validation prevents single-point-of-failure

**Database: Tanzil vs KDN**
- Uses Tanzil DB (standard Unicode Uthmani)
- KDN-verified pages may have subtle differences
- Solution: Reference images in `database/reference_imgs/` for exact CV comparison

---
## Fine-Tuning Analysis

See: `Docs/FINE_TUNING_ANALYSIS.md`

**Training Data (1,128 samples):**
- 604 perfect examples (53.5%) - model memorizes these
- 400 synthetic errors (35.5%)
- 124 KDN examples (11.0%)

**Root Cause: Data Imbalance**
- Model memorizes standard text instead of reading pixels
- Bias toward perfect examples
- Results in auto-correction/hallucination

**Recommendations:**
1. Collect 500-1000 real error examples
2. Improve prompting (explicit no auto-correction)
3. Balance training data (50% correct, 50% errors)
4. Use Image Comparison as primary method (no hallucination)

---
## Project Structure

```
v3quran_verificator/
├── app_enhanced.py              # Main Streamlit UI
├── config.py                    # Configuration
├── models/
│   ├── qari_ocr.py              # QariOCR model wrapper
│   └── FT1_QariOCR/             # Fine-tuned model (6,236 verses)
├── verification/
│   ├── missing_line_detector.py # RAG + LLM system
│   ├── text_verifier.py         # Text verification
│   ├── structural_verifier.py    # Structural analysis
│   └── semantic_verifier_simple.py
├── triangulation/
│   ├── ocr_compare.py           # OCR comparison
│   ├── cv_compare.py             # CV page-layout comparison
│   └── hash_compare.py           # Hash verification
├── database/
│   ├── quran_verses.db           # SQLite database (6,236 verses)
│   ├── reference_imgs/            # Reference page images
│   └── uthmani_db.py             # Database interface
├── Server/
│   └── docker-compose-mac-studio-dev.yml
├── Docs/
│   ├── TRIANGULATION_METHOD.md
│   └── FINE_TUNING_ANALYSIS.md
└── requirements-docker.txt       # All dependencies
```

---
## Deployment

**Mac Studio Setup:**
- Running via Docker
- Access: http://100.72.149.103:8501
- Tailscale IP: 100.72.149.103
- Container: quran-verifier-mac-studio-dev

**File Sharing:**
```bash
# Access Mac Studio from MacBook
smb://100.72.149.103
```

**Container Management:**
```bash
# Restart
cd Server && docker-compose -f docker-compose-mac-studio-dev.yml restart

# View logs
docker logs quran-verifier-mac-studio-dev -f

# Check status
docker ps | grep quran-verifier
```

---
## Detection Methodology

### Missing Line Detection Flow
1. Extract text via QariOCR
2. Get reference verses from database
3. Split into lines and clean
4. **Fuzzy matching** (rapidfuzz, 60% threshold)
5. **RAG semantic search** (find similar verses)
6. **LLM suggestion** (context-aware recommendations)
7. Generate enhanced suggestions
8. Display in UI with status indicators

### UI Display
- Shows missing line count
- RAG + LLM enhancement status
- Missing line details with suggestions
- Confidence scores
- Similar verse references

---
## User Workflow

1. Upload Quran page image
2. Select verification method (Hybrid recommended)
3. System extracts text via QariOCR
4. Detects missing lines via RAG + LLM
5. Compares with reference via CV
6. Shows results with visual indicators
7. Provides intelligent suggestions

---
## Critical Knowledge

### Why RAG + LLM?
- Fuzzy matching alone wasn't detecting missing lines
- Semantic understanding improves accuracy
- Context-aware suggestions help identify what's missing
- Similar verse retrieval provides educational context

### Why 60% Threshold?
- Arabic text has natural variations
- Too high = misses real differences
- Too low = false positives
- 60% balances accuracy vs sensitivity

### Why Remove Duplicate Detector?
- Quran legitimately repeats phrases
- Words like "الله" appear many times
- Flagging as errors is incorrect
- Removed to prevent false positives

### Database Column Mapping
- Schema uses: `sura_number`, `aya_number`, `text_original`
- NOT: `surah`, `ayah`, `text`
- Fixed in RAG initialization

---
## Goals & Direction

**Short-term:**
- Improve missing line detection accuracy
- Tune thresholds for real-world data
- Fix QariOCR repetition issue
- Collect more training data

**Medium-term:**
- Better training data (real errors)
- Retrain QariOCR with balanced dataset
- Enhanced semantic understanding
- More CV reference images

**Long-term:**
- Full RAG + LLM integration
- Real-time learning from errors
- Automated report generation
- Integration with KDN systems

---
## Dependencies

See: `requirements-docker.txt`

Key packages:
- streamlit, plotly
- sentence-transformers, faiss-cpu
- opencv-python, numpy, scikit-image
- transformers, huggingface-hub, peft, accelerate
- rapidfuzz
- qwen-vl-utils
- arabic-reshaper, python-bidi

---
## Testing & Validation

**Test Cases:**
1. Upload page with missing characters
2. Verify QariOCR + CV both detect issue
3. Check missing line detector finds it
4. Validate RAG + LLM suggestions
5. Compare with reference

**Success Criteria:**
- All methods detect issue
- Missing line index matches
- Suggestions are relevant
- UI shows correct status

---
## Context for AI Assistance

When working on this project:
1. Understand triangulation first - three independent methods
2. RAG + LLM is for intelligent missing line detection
3. CV comparison is primary method (no hallucination)
4. Database uses Tanzil standard
5. Training data imbalance causes hallucination
6. Docker deployment on Mac Studio
7. Arabic text needs fuzzy matching (not exact)
8. Remove duplicate detection (Quran repeats legitimately)
9. Missing line detector shows status even when no missing lines
10. Threshold tuning critical (currently 60%)

This is a KDN compliance system - accuracy and reliability are paramount. The triangulation method ensures robust verification through multiple independent approaches.

