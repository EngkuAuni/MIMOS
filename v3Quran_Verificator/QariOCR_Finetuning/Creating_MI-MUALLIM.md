# Creating Mi‑MUALLIM (QariOCR Fine‑Tuned)

Purpose: Track Mi‑MUALLIM versions, artifacts, essential configs, and usage. Keep this document concise and updated.

## 1. Versioning and Registry

- Scheme: incremental (`v1`, `v2`, `v3`, ...)
- Storage: in‑repo under `models/` (use Git LFS if needed)
- One sample report PDF per version:
  - `QariOCR_Finetuning/FT1/FT1_sample_report.pdf`
  - `QariOCR_Finetuning/FT2/FT2_sample_report.pdf`

### Current versions

- v1 → `models/FT1_QariOCR` (active by default)
- v2 → planned (FT2 extraction/verification split per guide)

## 2. Latest Release (v1 – FT1)

- Base: `Qwen/Qwen2-VL-2B-Instruct`
- Adapter path: `models/FT1_QariOCR`
- Metrics (approx): WER 0.045, CER 0.012 (see `models/current_model.json`)
- Known behavior: Tendency to auto‑correct on error pages (see FT1 analysis)

## 3. Artifacts

- Adapter: PEFT LoRA weights (`adapter_model.safetensors` + config)
- Tokenizer/processor configs: included with adapter folder
- Metadata: `models/current_model.json` (name, version, accuracy)

## 4. Training Data Summary (v1)

- Perfect pages: ~604
- Synthetic errors: ~400 (39 types)
- KDN examples: ~124
- Note: imbalance → memorization → auto‑correction risk (see `Docs/FINE_TUNING_ANALYSIS.md`)

## 5. Training Configuration (reference)

- Context length: 2048 tokens
- LoRA rank/alpha/dropout: 16/16/0.1
- Epochs: 3; LR: 2e‑4; Accumulation: 4
- Batch: 2/2 (train/eval)
- Optimizer: adamw_8bit
- Example JSON: `QariOCR_Finetuning/FT2/training_config_ft2_extraction.json` (for FT2 direction)

## 6. Evaluation

- Report: keep one small sample PDF per version (≤2MB)
- Include a “perfect page” and an “error detected” case when feasible
- For FT1 issues and targets for FT2, see `Docs/FINE_TUNING_ANALYSIS.md` and `QariOCR_Finetuning/FT2/FT2_IMPLEMENTATION_GUIDE.md`

## 7. Integration and Usage

- Loader: `models/qari_ocr.py` wraps base + adapter (CPU default; CUDA/MPS via env)
- App integration: `app_enhanced.py` initializes model once at startup
- Active model pointer: `models/current_model.json`
- For future split (FT2): optional `model_type` (extraction/verification)

## 8. Changelog (essentials)

- v1 (FT1): initial fine‑tune; good extraction on perfect pages; auto‑correction on errors
- v2 (FT2): goal — reduce auto‑correction, improve error detection; add verification model for analysis

## 9. Roadmap (short)

- Collect more real error pages; balance data (~50/50 correct vs error)
- Improve prompting ("extract exactly what you see; no auto‑correct")
- Publish FT2 extraction + verification adapters
