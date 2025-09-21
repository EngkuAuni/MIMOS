# Resources
Tanzil ([](https://tanzil.net/download/))
- Quran text ([Uthmani](../Data/Tanzil_quran-uthmani.sql))
- Quran text jpg/png by verse ([](https://www.versebyversequran.com))

Qari-OCR ([](https://huggingface.co/NAMAA-Space/Qari-OCR-0.1-VL-2B-Instruct))
- multimodal VLM model 
- could be used alongisde traditional OCR/on its own as fallback
- ([Other options](https://huggingface.co/spaces/kitab-bench/KITAB-Bench-Leaderboard))
- open source, not local

Quran.com ([Repos](https://github.com/quran))
- 

----------------------------------------------------------------------------------------------------------------------

# Overview
**User Flow**
1. Upload
    - The user begins by providing an input file, which can be either a photo (e.g., JPEG, PNG) or a PDF document of a Quran page.
    - As soon as the file lands, the backend stores it in a temporary folder and runs pre‑processing (deskew → denoise → auto‑crop → perspective correction) to obtain a clean image ready for analysis.

2. Process & Match
    * The engine first tries to identify the exact page (edition‑locked fingerprint). Two parallel paths exist:
        A. Page‑Match (preferred) –
           - Extract ORB (or SIFT) key‑points & binary descriptors from the cleaned image.
           - Compare them against the pre‑computed ORB database of every reference page (one file per page).
           - If the similarity score is above the page‑match threshold we know the edition + page number with provable confidence.
        
        B. OCR‑Match (fallback) –
           - If page‑matching fails or the user explicitly selects a region, the system runs Arabic OCR on the region.
                - Default: Kraken / Calamari fine‑tuned on Uthmānī script.
                - Optional: Qari‑OCR VLM (vision‑language model) – can be swapped in here and also used later for explanations.
           - The raw Unicode string is sent to the next stage.

3. Verify
   - Edition‑locked verification – because the page is identified, the exact set of ayahs on that page is known from the reference DB.
       - The normalized OCR (or even the raw image) is compared byte‑for‑byte (after the same strict normalization) with the stored canonical text.
       - If the SHA‑256 hashes are identical → “Verified (Edition X)” (provable 100 % correctness).
   - Open‑edition verification – when the edition is unknown or page‑matching failed:
       - The OCR text is strictly normalized (tatweel removal, hamza unification, NFC, optional diacritic‑insensitive mode).
       - Compute the SHA‑256 of the normalized string and look it up in the ayah_hashes table.
       - If a hash hit = exact match → “Textually identical to canonical Uthmānī”.
       - If no hit → compute a diacritic‑aware Levenshtein distance against all verses, pick the best candidates, and produce a confidence score.

4. Display Results
    - Exact Match – a green “Verified (Edition X)” badge, Surah/Ayah, page number, and the two SHA‑256 checksums.
    - Near‑Match – a side‑by‑side HTML diff (red deletions, green insertions) plus a confidence %.
    - Explanation – an LLM‑generated paragraph that tells the user why the two texts differ (missing shadda, different waqf sign, printing error, OCR glitch, edition‑specific glyph, …).
    - No Match – a friendly prompt to retake the photo, choose a different edition, or send the image for human review.

5. Review & Retry
    * Users can:
       - Accept the diff and export a PDF report (original scan, diff, badge, LLM explanation).
       - Click “Try again” – the temporary workspace is cleared and the flow restarts.
       - Mark the result as “Correct / Incorrect” – those clicks feed back into a tiny audit log for future QA.

**Engine Structure**
1. Data Assets
    * This is the foundation of the entire system, pre-built and bundled for offline use. It includes:
        - An offline SQLite database (quran_ref.db)
            - quran_text (sura, ayah, text) – canonical Uthmānī verse.
            - ayah_hash (sura, ayah, hash) – SHA‑256( normalize(text) ).
            - page_map (page_number, edition, sura, ayah_start, ayah_end) – which verses belong to which printed page.
        - Reference page images – high‑resolution PNGs for every page of every supported edition (e.g., Madani, Indo‑Pak).
        - Pre‑computed ORB descriptors – assets/orb/001.npz, 002.npz, … each storing key‑points + binary descriptors for the matching stage.
        - Optional VLM weights – models/qari_ocr/… for the vision‑language fallback and for LLM‑assisted explanations.

2. Core Processing Modules
    * These are the central components that perform the heavy lifting:
       - Pre‑processing – OpenCV pipeline: deskew → bilateral denoise → Otsu binarization → border detection → perspective warp.
       - Feature Extraction – ORB (or SIFT) on the pre‑processed image; identical settings are used when generating the reference descriptors.
       - Page‑Match Core – BFMatcher (Hamming) + cross‑check; keep top‑30 % matches, score = number of good matches. If score ≥ PAGE_MATCH_THRESHOLD → page identified.
       - OCR Module – pluggable:
           - Kraken / Calamari (custom Uthmānī model).
           - Qari‑OCR VLM (vision‑language) – can be used as a direct fallback and also supplies visual embeddings for downstream LLM prompts.
       - Hash‑Lookup Engine – receives the normalized OCR string, computes SHA‑256, and performs a fast index look‑up in ayah_hash.

3. Verification & Logic Layer
    - Text Normalization – remove tatweel, unify hamza forms, NFC, optional diacritic stripping (configurable per edition).
    - Verification Logic –
       - Edition‑locked → page → exact‑hash comparison → provable ✅.
       - Open‑edition → hash miss → diacritic‑aware Levenshtein → top‑k candidates + confidence.
    - Diff Generator – difflib.HtmlDiff (RTL‑aware CSS) to highlight insertions/deletions.
    - Explain‑LLM Engine – thin wrapper around a local open‑source LLM (e.g., Phi‑3‑mini, Mistral‑7B, or a fine‑tuned Noor model).
       - Input: canonical verse, OCR verse, diff highlights, edition/page metadata, optional visual embeddings from Qari‑OCR.
       - Output: short natural‑language explanation of the discrepancy (missing shadda, different waqf sign, printing error, OCR noise, edition‑specific glyph).

4. Output/UI engine
    - Result Presenter – Streamlit (or FastAPI + React) component that renders the badge, diff table, confidence bar, and LLM explanation.
    - Report Builder – assembles an HTML document (original image, diff, badge, explanation) → PDF via WeasyPrint (fallback to ReportLab).
    - Retry / Human‑Review Manager – clears temp files, logs the decision (verified / needs review) and, if the user opts‑in, stores the image for later manual audit.


**User Flow Chart**
┌───────────────────────────────────────────────────────────────────┐
│                USER INTERFACE (Streamlit / FastAPI)               │
│  • Drag‑&‑drop upload                                             │
│  • Optional region selector (fallback)                            │
│  • Results view (badge, diff, explanation)                        │
└───────────────▲───────────────────────────────▲───────────────────┘
                │                                   │
                │                                   │
                │                                   │
   ┌────────────▼─────────────┐        ┌────────────▼────────────┐
   │  Core Processing Layer   │        │  Verification Layer     │
   │  (Pre‑processing,        │        │  (Hash lookup,          │
   │   Feature extraction)    │        │   Normalisation)        │
   │  • OpenCV (deskew,       │        │  • SHA‑256 compare      │
   │    denoise, crop)        │        │  • Surah/Ayat mapping   │
   │  • ORB descriptor gen    │        │                         │
   └──────▲───────▲───────────┘        └──────▲───────▲──────────┘
          │       │                         │       │
          │       │                         │       │
   ┌──────▼─────┐ ┌───────▼───────┐   ┌─────▼─────┐ ┌─────▼─────────┐
   │ Page‑Match │ │ OCR‑Fallback  │   │ Text      │ │ Explain‑LLM   │
   │ Engine     │ │ Engine        │   │ Normalizer│ │  LangChain,   │
   │ (ORB ↔ DB) │ │ (EasyOCR /    │   │ (diacritic│ │ OpenAI /      │
   │            │ │  Qari‑OCR)    │   │  stripping│ │ Claude…)      │
   └──────▲─────┘ └───────▲───────┘   └─────▲─────┘ └─────▲─────────┘
          │               │               │           │
          │               │               │           │
          │               │               │           │
   ┌──────▼───────┐ ┌─────▼───────┐   ┌───▼─────┐ ┌───▼─────────┐
   │   Diff       │ │ Hash Lookup │   │  Badges │ │  Report     │
   │   Generator  │ │ (SQLite)    │   │ (✓/✗)   │ │ Builder     │
   └──────▲───────┘ └─────▲───────┘   └─────▲───┘ └─────▲───────┘
          │               │               │           │
          │               │               │           │
          └───────►───────►──────────────────────►─────►
                         USER (HTML / PDF)


System Pipeline
├─ USER FLOW
│   ├─ Upload
│   │   └─ Save file → Temp folder
│   │   └─ Pre‑process (deskew, denoise, crop, warp)
│   ├─ Process & Match
│   │   ├─ Page‑Match (preferred)
│   │   │   ├─ Extract ORB features from clean image
│   │   │   ├─ Load pre‑computed ORB descriptors (all editions)
│   │   │   ├─ BFMatcher (Hamming, cross‑check)
│   │   │   └─ If similarity ≥ threshold → (edition, page) identified
│   │   └─ OCR‑Match (fallback)
│   │       ├─ User may select region (or whole page)
│   │       ├─ Run OCR
│   │       │   ├─ Default: Kraken/Calamari (Uthmānī‑trained)
│   │       │   └─ Optional: Qari‑OCR VLM (vision‑language)
│   │       └─ Return raw Unicode text
│   ├─ Verify
│   │   ├─ Edition‑Locked verification (page identified)
│   │   │   ├─ Fetch ayahs for that page from DB
│   │   │   ├─ Normalise OCR/scan text
│   │   │   ├─ Compute SHA‑256 of each ayah
│   │   │   └─ All hashes equal → “Verified (Edition X)”
│   │   └─ Open‑Edition verification  (no page id)
│   │       ├─ Normalise OCR text
│   │       ├─ Compute SHA‑256 → hash lookup
│   │       ├─ Exact hash hit → “Textually identical”
│   │       └─ No hit → Diacritic‑aware Levenshtein
│   │           └─ Produce confidence % & top‑k candidate ayahs
│   ├─ Display Results
│   │   ├─ Exact match → Green badge + Surah/Ayah + page
│   │   ├─ Near‑match → Amber badge + confidence %
│   │   │   ├─ HTML diff (red/green)
│   │   │   └─ LLM‑generated explanation
│   │   └─ No match → Suggest better photo / human review
│   └─ Review & Retry
│       ├─ Download PDF report (scan + diff + badge + explanation)
│       ├─ Try again (clear temp, back to Upload)
│       └─ Mark as correct / incorrect → audit log
│
└─ ENGINE STRUCTURE
    ├─ Data Assets (offline bundle)
    │   ├─ SQLite DB: quran_ref.db
    │   │   ├─ quran_text (sura, ayah, text)          ← canonical Uthmānī
    │   │   ├─ ayah_hash (sura, ayah, sha256_norm)    ← pre‑computed checksums
    │   │   └─ page_map (page, edition, sura, ayah_start, ayah_end)
    │   ├─ Reference page images
    │   │   └─ assets/
    │   ├─ Pre‑computed ORB descriptors
    │   │   └─ assets/
    │   ├─ Optional VLM weights
    │   │   └─ models/qari_ocr/ … (ONNX / ggml)
    │   └─ LLM model & tokenizer
    │       └─ models/llm/ … (Phi‑3‑mini, Mistral‑7B, or fine‑tuned Noor)
    │
    ├─ Core Processing Modules
    │   ├─ Pre‑processing (OpenCV)
    │   │   └─ deskew → denoise → Otsu binarise → crop → warp
    │   ├─ ORB Feature Extraction
    │   │   └─ extract_orb(pil_img) → (kp, desc)
    │   ├─ Page‑Match Core
    │   │   └─ match_page(user_desc) → (edition, page, score)
    │   ├─ OCR Engine (pluggable)
    │   │   ├─ run_ocr(pil_img, region) → raw_text
    │   │   ├─ Default: Kraken/Calamari (Uthmānī‑trained)
    │   │   └─ Optional: Qari‑OCR VLM (vision‑language)
    │   └─ Hash‑Lookup Engine
    │       └─ lookup_hash(normalised_str) → (sura, ayah, exact?)
    │
    ├─ Verification & Logic Layer
    │   ├─ Text Normalisation
    │   │   └─ normalize_arabic(txt, drop_diacritics=False)
    │   ├─ Edition‑Locked Verification
    │   │   └─ Compare per‑ayah hashes → provable 100 % badge
    │   ├─ Open‑Edition Verification
    │   │   ├─ Exact hash check → “identical”
    │   │   └─ Fuzzy Levenshtein + confidence % → candidates
    │   ├─ LLM‑Driven Explanation
    │   │   └─ explain_mismatch(ref, ocr, diff, metadata) → short paragraph
    │   └─ Decision Engine
    │       └─ Picks one of: Exact‑edition badge, Exact‑open badge,
    │           Near‑match (confidence + explanation), No‑match (retry)
    │
    └─ Output / UI Engine
        ├─ Result Presenter
        │   ├─ Badge rendering (green / amber / red)
        │   ├─ HTML diff (RTL‑aware)
        │   ├─ LLM explanation block
        │   └─ Action buttons (PDF, Retry, Human‑review)
        ├─ Report Builder
        │   └─ Assemble HTML → PDF via WeasyPrint (fallback ReportLab)
        └─ Retry / Human‑Review Manager
            ├─ Clear temporary workspace
            ├─ Store image + metadata in review queue (if requested)
            └─ Log audit entry (correct / incorrect)