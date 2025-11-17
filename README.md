# v3quran_verificator

This Quran Verification Engine triangulates OCR extraction, computer-vision page layout comparison, and cryptographic hashing to detect diacritic/character-level issues in Uthmani script.

## Quick Start

**Docker (recommended):**
```bash
./run_docker.sh
```
See `docker/README.md` for detailed Docker setup and management.

**Local development:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_enhanced.py
```
App runs at `http://localhost:8501`.

## Features

- Multi-layer verification: OCR, CV layout, SHA-256 hash
- Missing line detector with RAG-enhanced suggestions
- Streamlit UI + PDF report generation
- SQLite Tanzil database + reference page images

## Architecture (high-level)

- UI: `app_enhanced.py` (Streamlit)
- Models: `models/` (Mi‑MUALLIM fine-tuned QariOCR adapters)
- Verification: `verification/` (text, structural, semantic, missing-line)
- Triangulation: `triangulation/` (ocr/cv/hash comparison)
- Data: `database/` (SQLite, reference images, scripts)

See `Docs/ARCHITECTURE.md` for details.

## Documentation

- **Docker setup**: `docker/README.md`
- **Architecture**: `Docs/ARCHITECTURE.md`
- **Database**: `Docs/DATABASE.md`
- **Models (Mi‑MUALLIM)**: `Docs/MODELS.md`
- **Fine-tuning guide**: `QariOCR_Finetuning/FINE_TUNING_GUIDE.md` ⭐ **Start here for model development**
- **Developer reference**: `Docs/DEV_REF/PROJECT_BRIEFING.md`
- **Triangulation method**: `Docs/TRIANGULATION_METHOD.md`
- **Fine-tuning analysis**: `Docs/FINE_TUNING_ANALYSIS.md`

## Models (Mi‑MUALLIM)

- Active model metadata: `models/current_model.json`
- Version registry and per-version samples: `QariOCR_Finetuning/Creating_MI-MUALLIM.md`
- One small sample report per version:
  - `QariOCR_Finetuning/FT1/FT1_sample_report.pdf`
  - `QariOCR_Finetuning/FT2/FT2_sample_report.pdf`

## Requirements

See `requirements.txt` for local dev and `requirements-docker.txt` for Docker image.