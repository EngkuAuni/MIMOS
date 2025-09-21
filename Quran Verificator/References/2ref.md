

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
	       - Optional: Qari-OCR VLM (multimodal OCR).
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
           - If no match → fuzzy search:
            •	Diacritic‑aware Levenshtein distance.
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
	-	VLM models: models/qari_ocr/…
	-	LLMs: models/llm/ (Phi-3, Mistral, etc.)

2. Core Processing Modules
	-	OpenCV Pipeline (Pre-processing): deskew → binarize → crop → warp
	-	ORB Feature Extraction: extract keypoints/descriptors.
	-	Page Matching: BFMatcher (threshold-based scoring).
	-	OCR Engine: pluggable (Kraken / Qari-OCR).
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