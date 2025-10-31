# Architecture

## Overview

The system verifies Quran pages via three independent methods and surfaces results in a Streamlit UI.

## Components

- UI: `app_enhanced.py`
- Models: `models/` (Mi‑MUALLIM fine‑tuned adapters)
- Verification: `verification/` (text, structural, semantic, missing-line)
- Triangulation: `triangulation/` (ocr/cv/hash)
- CV/Preprocess/Segmentation: `cv/`, `preprocessing/`, `segmentation/`
- Data: `database/` (SQLite, reference images, scripts)
- Reporting: `report/`

## Data Flow (text-based)

1. Upload page (image/PDF) → `utils/file_handler.py` → optional `preprocessing/preprocess.py`
2. Page segmentation (optional) → `segmentation/verse_segmenter.py`
3. OCR extraction (Mi‑MUALLIM) → `models/qari_ocr.py`
4. Verification:
   - Text/structural checks → `verification/`
   - Missing-line detector (RAG) → `verification/missing_line_detector.py`
   - Hash comparison → `triangulation/hash_compare.py`
   - CV layout comparison → `triangulation/cv_compare.py`
5. Cross-compare (triangulation) → `triangulation/ocr_compare.py` + display via UI
6. Report generation → `report/report_gen.py`

## Key Decisions

- Use triangulation to avoid single point of failure
- SQLite Tanzil DB for reference text + reference images for exact CV matching
- Mi‑MUALLIM (fine‑tuned QariOCR) as OCR/LLM component

## Environments

- Docker (recommended): `Dockerfile`, `docker-compose.yml`, `README_Docker.md`
- Local dev: `SETUP.md`
