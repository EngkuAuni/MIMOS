# Models — Mi‑MUALLIM (QariOCR Fine‑Tuned)

## Overview

Mi‑MUALLIM is the fine‑tuned QariOCR used by this engine for Arabic OCR and LLM‑style analysis.

- Active model metadata: `models/current_model.json`
- Default adapter path: `models/FT1_QariOCR`
- Version registry and samples: `QariOCR_Finetuning/Creating_MI-MUALLIM.md`

## Versioning

- Incremental: `v1, v2, v3, ...`
- One small sample report PDF per version kept in `QariOCR_Finetuning/FT*/`

## Loading

- The app loads the adapter via `models/qari_ocr.py` on top of the base `Qwen/Qwen2-VL-2B-Instruct`.
- Device selection: CPU by default; can enable CUDA/MPS with env vars.

## Adding a new version

1. Place adapter under `models/FT{N}_QariOCR` (or consistent naming)
2. Update `models/current_model.json` if making it active
3. Add sample PDF to `QariOCR_Finetuning/FT{N}/FT{N}_sample_report.pdf`
4. Update the registry: `QariOCR_Finetuning/Creating_MI-MUALLIM.md`

## Notes

- See `Docs/FINE_TUNING_ANALYSIS.md` for FT1 analysis and improvement path.
- See `QariOCR_Finetuning/FT2/FT2_IMPLEMENTATION_GUIDE.md` for FT2 plan.
