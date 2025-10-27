# Resources
Tanzil ([](https://tanzil.net/download/))
- Quran text ([Uthmani](../Data/Tanzil_quran-uthmani.sql)) - by surah & verse for OCR hashing
- Quran text jpg/png by verse ([](https://www.versebyversequran.com)) - not suitable for whole page ORB+SIFT

Holy Quran Arabic King Fahd Complex ([](https://archive.org/details/holy-quran-arabic-king-fahd-complex-for-printing_20221229/page/n605/mode/2up?utm_source=chatgpt.com))
- Quran Mushaf by page - ref to generate ORB + SIFT feature descriptors

Qari-OCR ([](https://huggingface.co/NAMAA-Space/Qari-OCR-0.1-VL-2B-Instruct))
- multimodal VLM model 
- could be used alongisde traditional OCR/on its own as fallback
- ([Other options](https://huggingface.co/spaces/kitab-bench/KITAB-Bench-Leaderboard))
- open source, not local

Quran.com ([Repos](https://github.com/quran))

----------------------------------------------------------------------------------------------------------------------
# Overview
**User Flow**
1. Upload
	-	User uploads an image or PDF of a Quran page.
	-	Backend saves file → temporary folder.
	-	Pre-processing: deskew → denoise → crop → warp → binarize.

2. Process & Match
	A. Page‑Match (Preferred)
	   - Extract ORB/SIFT features from cleaned image.
	   - Load precomputed ORB descriptors for all known editions.
	   - BFMatcher (Hamming) with cross‑check.
	   - If similarity ≥ threshold → edition + page identified.

	B. OCR‑Match (Fallback)
	   - User selects a region (or whole page auto‑selected).
	   - OCR runs on that region using:
	       - Default: Kraken (fine‑tuned for Uthmānī script).
	   - Output: raw Unicode string (Arabic).

3. Verify
   * Edition‑Locked Verification (if page matched)
       - Fetch ayahs for identified page from DB.
       - Normalize OCR result.
       - Compute SHA‑256 of each ayah.
           - If all hashes match → ✅ Verified (Edition X).
   * Open‑Edition Verification (if page unknown)
       - Normalize entire OCR text:
       - Remove Tatweel, unify Hamza, NFC, optional diacritic removal.
       - Compute SHA‑256 hash → lookup in ayah_hash DB.
           - If exact match → ✅ Identical to Uthmānī.
           - If no match → fuzzy search:   # Current verifier uses database’s get_fuzzy_matches (difflib) --> will upgrade to RapidFuzz
            •	Diacritic‑aware Levenshtein distance (RapidFuzz)
            •	Top‑K ayah candidates + confidence score.

4. Explain & Display Results
	-	Exact Match → Green badge, surah, ayah, page, SHA‑256.
	-	Near Match → HTML diff (insertions → green, deletions → red).
	-	LLM Explanation:
        - Use local LLM (e.g., Phi‑3, Mistral‑7B, Noor).
	        •   Input: canonical vs OCR text + metadata + diff.
            •	Output: natural-language explanation (e.g., missing diacritic, OCR error).
            •	No Match → Suggest better photo, retry, or escalate to human review.

5. Review & Retry
	-	Export PDF report (scan + diff + badge + LLM explanation).
	-	“Try Again” → clears workspace and restarts flow.
	-	Mark as Correct / Incorrect → saved to audit log.


**Engine Structure**
1. Data Assets (offline)
	-	quran_ref.db (SQLite):
	-	quran_text (sura, ayah, text)
	-	ayah_hash (sura, ayah, sha256_norm)
	-	page_map (page, edition, sura, ayah_start, ayah_end)
	-	Reference page images: assets/images/
	-	ORB descriptors: assets/orb/*.npz
	-	LLMs: models/llm/ (Phi-3, Mistral, etc.)

2. Core Processing Modules
	-	OpenCV Pipeline (Pre-processing): deskew → binarize → crop → warp
	-	ORB Feature Extraction: extract keypoints/descriptors.
	-	Page Matching: BFMatcher (threshold-based scoring).
	-	OCR Engine: pluggable (Kraken).
	-	Hash Lookup: SHA‑256 → ayah DB.

3. Verification & Logic
	-	normalize_arabic(text, drop_diacritics=True/False)
	-	Edition Match: byte-for-byte hash check.
	-	Open Match: hash lookup → fuzzy match.
	-	Diff Generator: RTL-aware HTML diff.
		LLM Explainer: generates reasoning behind mismatch.

4. Output / UI Engine
	-	Streamlit or FastAPI frontend.
	-	Render: badge, diff, LLM explanation. 
	-	PDF Report builder: WeasyPrint / ReportLab
	-	Human review module + audit log.

# System Pipeline
├─ USER FLOW
│   ├─ Upload
│   │   ├─ User selects an image or PDF of a Quran page
│   │   ├─ Backend stores the file in a temporary folder
│   │   └─ Pre‑processing (OpenCV)
│   │       ├─ deskew
│   │       ├─ denoise
│   │       ├─ crop
│   │       ├─ warp (perspective correction)
│   │       └─ binarize (Otsu / adaptive)
│   ├─ Process & Match
│   │   ├─ A. Page‑Match (preferred)
│   │   │   ├─ Extract visual features (ORB **or** SIFT) from the cleaned image
│   │   │   ├─ Load pre‑computed ORB descriptors for **all known editions**
│   │   │   ├─ BFMatcher (Hamming, cross‑check) → similarity score
│   │   │   └─ If score ≥ threshold (e.g. 0.70) → identify **(edition, page)**
│   │   └─ B. OCR‑Match (fallback)
│   │       ├─ UI lets the user pick a region (or auto‑select the whole page)
│   │       ├─ Run OCR on the region using the pluggable engine:
│   │       │   ├─ Default: **Kraken** (Uthmānī‑fine‑tuned)
│   │       └─ Output: raw Unicode Arabic string
│   ├─ Verify
│   │   ├─ *Edition‑Locked Verification*  (page was matched)
│   │   │   ├─ Pull the list of ayahs that belong to the identified page from `page_map`
│   │   │   ├─ Normalise the OCR result
│   │   │   ├─ Compute SHA‑256 for **each ayah**
│   │   │   └─ If **all** hashes equal the stored `ayah_hash` → ✅ “Verified (Edition X)”
│   │   └─ *Open‑Edition Verification*  (no page match)
│   │       ├─ Normalise the whole OCR text
│   │       │   • strip Tatweel, unify Hamza, NFC‑compose, optional diacritic removal
│   │       ├─ Compute a single SHA‑256 over the normalised string
│   │       ├─ Lookup that hash in `ayah_hash`
│   │       │   ├─ Exact hit → ✅ “Identical to Uthmānī”
│   │       │   └─ Miss → fuzzy search:
│   │       │       • Diacritic‑aware Levenshtein distance
│   │       │       • Return top‑K ayah candidates + confidence % (e.g. ≥ 80 %)
│   │       └─ Decision recorded for UI rendering
│   ├─ Explain & Display Results
│   │   ├─ Exact Match
│   │   │   ├─ Green badge  ✅
│   │   │   ├─ Shows Surah / Ayah / Page / SHA‑256
│   │   ├─ Near‑Match
│   │   │   ├─ Amber badge  ⚠️
│   │   │   ├─ HTML diff (RTL‑aware):
│   │   │   │   • insertions → green background
│   │   │   │   • deletions → red background
│   │   │   └─ LLM‑generated explanation:
│   │   │       • Input: canonical text, OCR text, diff, metadata
│   │   │       • Model (local Phi‑3 / Mistral‑7B / Noor)
│   │   │       • Output: short natural‑language reason (missing diacritic, OCR glitch, etc.)
│   │   └─ No Match
│   │       ├─ Red badge  ❌
│   │       ├─ Suggest a better photo / retry / escalates to human review
│   └─ Review & Retry
│       ├─ Export a PDF report (scan + diff + badge + LLM explanation)
│       ├─ “Try Again” button → clears temporary workspace & restarts flow
│       └─ Mark as Correct / Incorrect → persisted in the immutable audit log
│
└─ ENGINE STRUCTURE
    ├─ Data Assets (offline bundle)
    │   ├─ SQLite DB: **quran_ref.db**
    │   │   ├─ `quran_text`   (sura, ayah, text)                 ← canonical Uthmānī
    │   │   ├─ `ayah_hash`    (sura, ayah, sha256_norm)          ← pre‑computed checksums
    │   │   └─ `page_map`    (page, edition, sura, ayah_start, ayah_end)
    │   ├─ Reference page images → `assets/images/`
    │   ├─ Pre‑computed ORB descriptors → `assets/orb/*.npz`
    │   └─ LLM models & tokenizer → `models/llm/` (Phi‑3, Mistral‑7B, Noor, …)
    │
    ├─ Core Processing Modules
    │   ├─ **OpenCV Pipeline** (Pre‑processing)
    │   │   └─ deskew → denoise → crop → warp → binarize
    │   ├─ **ORB Feature Extraction**
    │   │   └─ `extract_orb(pil_img)` → (keypoints, descriptors)
    │   ├─ **Page‑Matching Core**
    │   │   └─ `match_page(user_desc)` → (edition, page, similarity_score)
    │   ├─ **OCR Engine** (pluggable)
    │   │   ├─ `run_ocr(pil_img, region)` → raw Unicode text
    │   │   ├─ Default: Kraken (Uthmānī‑trained)
    │   └─ **Hash‑Lookup Engine**
    │       └─ `lookup_hash(normalised_str)` → (sura, ayah, exact_match?)
    │
    ├─ Verification & Logic Layer
    │   ├─ **Text Normalisation**
    │   │   └─ `normalize_arabic(text, drop_diacritics=True/False)`
    │   ├─ **Edition‑Locked Verification**
    │   │   └─ Byte‑for‑byte ayah hash comparison → provable 100 % badge
    │   ├─ **Open‑Edition Verification**
    │   │   ├─ Exact hash lookup → “Identical”
    │   │   └─ Fuzzy Levenshtein + confidence % → top‑K candidates
    │   ├─ **Diff Generator**
    │   │   └─ RTL‑aware HTML diff (insert‑green, delete‑red)
    │   ├─ **LLM‑Driven Explanation**
    │   │   └─ `explain_mismatch(canonical, ocr, diff, metadata)` → short paragraph
    │   └─ **Decision Engine**
    │       └─ Chooses one of:
    │           • Exact‑edition badge (green)
    │           • Exact‑open badge (green)
    │           • Near‑match (amber + confidence + explanation)

# Modular Architecture Overview

┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                      │
│─────────────────────────────────────────────────────────────│
│ • Streamlit / FastAPI UI                                    │
│   - File uploader (PDF/image)                               │
│   - Optional region selector (for OCR fallback)             │
│   - Output: badge, diff, LLM explanation, report download   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      DATA ASSETS (OFFLINE)                  │
│─────────────────────────────────────────────────────────────│
│ • SQLite DB: quran_ref.db                                   │
│   - quran_text (sura, ayah, text)                           │
│   - ayah_hash (sura, ayah, sha256_norm)                     │
│   - page_map (page, edition, ayah range)                    │
│ • Page images (assets/images/*.png)                         │
│ • ORB descriptors (assets/orb/*.npz)                        │
│ • LLM Weights (Phi-3, Mistral, Noor...)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   CORE PROCESSING MODULES                   │
│─────────────────────────────────────────────────────────────│
│ 1. Preprocessing (OpenCV):                                  │
│    - Deskew, denoise, crop, warp, binarize                  │
│                                                             │
│ 2. Page Matching Engine:                                    │
│    - Feature extraction (ORB/SIFT)                          │
│    - BFMatcher (Hamming) against ORB DB                     │
│    - Output: edition + page if similarity ≥ threshold       │
│                                                             │
│ 3. OCR Engine (fallback):                                   │
│    - User can select region or use auto-page                │
│    - Output: raw Arabic Unicode string                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  VERIFICATION & LOGIC LAYER                 │
│─────────────────────────────────────────────────────────────│
│ 1. Text Normalizer:                                         │
│    - normalize_arabic(text, drop_diacritics=True/False)     │
│    - Tatweel removal, Hamza unification, NFC, diacritics    │
│                                                             │
│ 2. Edition-Locked Verification:                             │
│    - Retrieve ayahs from page_map                           │
│    - Hash each ayah and compare to DB                       │
│    - If all match → “Verified (Edition X)” ✅               │
│                                                             │
│ 3. Open-Edition Verification:                               │
│    - Hash entire normalized OCR text                        │
│    - Lookup in ayah_hash                                    │
│    - If no match → fuzzy match (Levenshtein + confidence)   │
│                                                             │
│ 4. Diff Engine:                                             │
│    - HTML diff (insertions = green, deletions = red)        │
│                                                             │
│ 5. Explain-LLM Engine:                                      │
│    - Input: canonical vs OCR text, metadata, diff           │
│    - Output: short explanation (LLM-generated)              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT / REVIEW MODULE                   │
│─────────────────────────────────────────────────────────────│
│ • Render badges (✅ Verified / ⚠️ Near-Match / ❌ No Match)  │
│ • LLM-generated explanation block                           │
│ • PDF Report Builder (WeasyPrint / ReportLab)               │
│ • Human Review Tools + Audit Logging                        │
└─────────────────────────────────────────────────────────────┘


## Based on KDN Requirements
# Data
- Canonical Quran text (From KDN/JAKIM)	
    - Use Tanzil/Uthmani DB for now (temporary placeholder)
- Reference images/PDFs	(From certified Quran publications)	
- Approved corpus hashes (Will be provided later for enforcement)	
    - Build the hash engine and test it on own normalized version
- Rules (rasm, tajwid, etc.) (From Lajnah Tashih)	
    - Don’t need full rules now; just basic normalisation + diacritic modes
- Sample submission (developers will submit them later)
    - Use test APK placeholders, dummy binaries, or PDFs

# Tech-stack from “Technical Architecture” section:
- Frontend: React (for Developer Portal, Reviewer Console)
- Engines: Python for Text Diff, OCR, Malware, Crawlers     # current
- APIs: REST / GraphQL (microservices + event bus)
- Database: PostgreSQL (transactions)       # SQLite for now
- File Storage: S3-compatible (object store for binaries/docs)      # Local filesystem for now
- Search/Logs: Elasticsearch / OpenSearch
- Cache/Queues:	Redis	
- Security:	PKI, HSM, IAM, audit logs
- CI/CD: Gated pipelines, SAST/DAST
- Hosting: MyGovCloud / Cloud Selamat
