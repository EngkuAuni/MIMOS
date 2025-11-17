# v3quran_verificator

Production-ready Quran Verification Engine for KDN compliance. It triangulates OCR extraction, computer-vision page layout comparison, and cryptographic hashing to detect diacritic/character-level issues in Uthmani script.

## Quick start

- Docker (recommended): see `README_Docker.md`, or run:

```bash
./run_docker.sh
```

- Local (developers): see `SETUP.md`.

App runs at `http://localhost:8501`.

## Remote testing on Mac Studio (Streamlit)

- Prepare server (once):
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - PDFs: `brew install poppler` (PyMuPDF used as fallback if present)
  - Optional env: `USE_MPS=true` (Apple Silicon), `QARIOCR_CV_PREPROCESS=1` (for scanned images)
- Run and expose to LAN:
  - `streamlit run app_enhanced.py --server.address 0.0.0.0 --server.port 8501`
  - Allow inbound on port 8501 in macOS Firewall
  - Find IP: `ipconfig getifaddr en0` (Wi‑Fi) or `en1` (Ethernet)
  - Testers open: `http://YOUR_MAC_IP:8501`
- Secure option (no firewall change):
  - Tester runs SSH tunnel: `ssh -N -L 8501:localhost:8501 user@YOUR_MAC_IP`
  - Then open `http://localhost:8501`
- Notes:
  - Use Settings tab → switch model adapter (FT1, FT2‑extraction, FT2‑verification)
  - PDFs: choose DPI (150/300/600) in UI; 300 recommended
  - If PDFs don’t render, ensure Poppler is installed

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

- Getting started (local): `SETUP.md`
- Docker: `README_Docker.md`
- Architecture: `Docs/ARCHITECTURE.md`
- Database: `Docs/DATABASE.md`
- Models (Mi‑MUALLIM): `Docs/MODELS.md`
- Developer brief: `Docs/DEV_REF/PROJECT_BRIEFING.md`

## Models (Mi‑MUALLIM)

- Active model metadata: `models/current_model.json`
- Version registry and per-version samples: `QariOCR_Finetuning/Creating_MI-MUALLIM.md`
- One small sample report per version:
  - `QariOCR_Finetuning/FT1/FT1_sample_report.pdf`
  - `QariOCR_Finetuning/FT2/FT2_sample_report.pdf`

## Requirements

See `requirements.txt` for local dev and `requirements-docker.txt` for Docker image.

## Contributing

Open PRs with clear descriptions. For larger changes, start a discussion first. See `Docs/README.md` to navigate all docs.


