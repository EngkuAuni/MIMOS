# Fine-Tuning Guide: Mi‑MUALLIM (QariOCR)

Complete guide for fine-tuning new versions of Mi‑MUALLIM. For version registry and model info, see `Creating_MI-MUALLIM.md`.

## Overview

This guide covers the end-to-end workflow:
1. **Data Preparation** — Generate/augment training data
2. **Training** — Run fine-tuning (Kaggle recommended)
3. **Integration** — Add trained model to app
4. **Testing** — Validate new version

## Prerequisites

- **Kaggle account** (recommended for GPU) or local GPU setup
- Python 3.9+ with ML dependencies
- Training data sources (see below)
- LoRA/PEFT fine-tuning

## 1. Data Preparation

### 1.1 Data Sources

You need:
- **Perfect pages**: Reference images from `database/reference_imgs/`
- **Error examples**: Real errors or synthetic (see below)
- **Ground truth**: Verse text from `database/quran_verses.db`

### 1.2 Generate Synthetic Errors (FT2+)

**Script**: `QariOCR_Finetuning/FT2/scripts/generate_synthetic_errors_v2.py`

```bash
cd QariOCR_Finetuning/FT2/scripts
python generate_synthetic_errors_v2.py \
    --target-samples 800 \
    --reference-dir ../../database/reference_imgs \
    --output-dir ../training_data/synthetic_errors_v2 \
    --db-path ../../database/quran_verses.db
```

**What it does:**
- Generates 800 diverse error samples (diacritic, character, word-level)
- Creates JSON metadata with ground truth text
- Outputs to `training_data/synthetic_errors_v2/`

### 1.3 Augment Perfect Pages (FT2+)

**Script**: `QariOCR_Finetuning/FT2/scripts/augment_perfect_pages.py`

```bash
python augment_perfect_pages.py --augmentations 2
```

**What it does:**
- Applies rotations, brightness, contrast variations
- Creates augmented perfect examples
- Outputs to `training_data/augmented_perfect/`

### 1.4 Rebalance Dataset (FT2+)

**Script**: `QariOCR_Finetuning/FT2/scripts/rebalance_dataset.py`

```bash
# Create extraction model dataset (40% perfect, 60% errors)
python rebalance_dataset.py --model-type extraction

# Create verification model dataset (different prompts)
python rebalance_dataset.py --model-type verification
```

**What it does:**
- Combines perfect + error samples
- Balances to target ratio (40/60 for FT2)
- Applies model-specific prompts
- Splits train/val (85/15)
- Outputs to `training_data/ft2/ft2_extraction/` or `ft2_verification/`

### 1.5 Training Data Format

Each sample in `train.json`/`val.json`:
```json
{
  "image": "path/to/image.jpg",
  "text": "extracted text or ground truth",
  "conversations": [
    {
      "from": "human",
      "value": "<image>\nExtract the Quranic text..."
    },
    {
      "from": "gpt",
      "value": "actual verse text here"
    }
  ]
}
```

## 2. Training Setup

### 2.1 Kaggle (Recommended)

**Notebooks:**
- FT1: `QariOCR_Finetuning/FT1/scripts/QariOCR_Kaggle_FT1.ipynb`
- FT2: `QariOCR_Finetuning/FT2/scripts/QariOCR_Kaggle_FT2.ipynb`

**Setup steps:**
1. Upload notebook to Kaggle
2. Add training data as dataset:
   - `train.json`, `val.json`, `metadata.json`
   - Reference images (or link to dataset)
3. Update paths in notebook:
   ```python
   train_data_path = "/kaggle/input/your-dataset/train.json"
   val_data_path = "/kaggle/input/your-dataset/val.json"
   output_dir = "/kaggle/working/models/FT{N}_QariOCR"
   ```
4. Enable GPU (P100/T4 recommended)
5. Run all cells

**Training config example** (`training_config.json`):
```json
{
  "base_model": "unsloth/qwen2-vl-2b-instruct-bnb-4bit",
  "max_seq_length": 2048,
  "lora_r": 16,
  "lora_alpha": 16,
  "lora_dropout": 0.1,
  "per_device_train_batch_size": 2,
  "gradient_accumulation_steps": 4,
  "num_train_epochs": 3,
  "learning_rate": 2e-4,
  "optim": "adamw_8bit"
}
```

### 2.2 Local Training (if GPU available)

```bash
# Install unsloth for faster training
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install "xformers<0.0.27" --no-deps

# Run training script (create from notebook)
python train_qariocr.py --config training_config.json
```

## 3. Training Execution

### 3.1 Key Parameters

- **LoRA rank**: 16 (increase to 24 for FT2 if needed)
- **Learning rate**: 2e-4
- **Epochs**: 3 (monitor for overfitting)
- **Batch size**: 2 with gradient accumulation 4 (effective batch = 8)
- **Prompt**: Critical — see FT2 guide for error detection prompts

### 3.2 Monitoring

Watch for:
- Training loss decreasing smoothly
- Validation loss (should decrease, not increase)
- Overfitting (val loss plateaus while train decreases)
- Checkpoints saved to `output_dir`

### 3.3 After Training

Download from Kaggle:
1. Go to Output tab
2. Download `adapter_model.safetensors`
3. Download `adapter_config.json`
4. Copy tokenizer files if changed

Or from local:
```bash
# Save adapter + config
cp -r /kaggle/working/models/FT{N}_QariOCR/* models/FT{N}_QariOCR/
```

## 4. Integration into App

### 4.1 Place Adapter Files

```bash
# Create model directory
mkdir -p models/FT{N}_QariOCR

# Copy adapter files
cp adapter_model.safetensors models/FT{N}_QariOCR/
cp adapter_config.json models/FT{N}_QariOCR/
# Copy tokenizer files if needed
cp tokenizer*.json models/FT{N}_QariOCR/
```

### 4.2 Update Model Metadata

Edit `models/current_model.json`:
```json
{
  "name": "FT{N}_QariOCR",
  "version": "{N}.0",
  "type": "finetuned",
  "path": "models/FT{N}_QariOCR",
  "status": "available",
  "accuracy": {
    "wer": 0.0XX,  # Update after evaluation
    "cer": 0.0XX
  }
}
```

### 4.3 Update App (if needed)

If adding new model type (e.g., FT2 verification), update `app_enhanced.py`:
```python
# Add model selection in sidebar
model_version = st.sidebar.selectbox(
    "🤖 Model Version",
    options=["FT1", "FT{N}_Extraction", "FT{N}_Verification"]
)

# Load appropriate model
if "FT{N}" in model_version:
    ocr_model = QariOCR(f"models/FT{N}_QariOCR", model_type=model_type)
```

### 4.4 Add Sample Report

```bash
# Generate test report with new model
# Then copy to version folder
cp report/sample_report.pdf QariOCR_Finetuning/FT{N}/FT{N}_sample_report.pdf
```

### 4.5 Update Version Registry

Edit `QariOCR_Finetuning/Creating_MI-MUALLIM.md`:
- Add new version entry
- Document training data summary
- Note improvements/issues
- Add to changelog

## 5. Testing & Validation

### 5.1 Quick Test

```python
from models.qari_ocr import QariOCR
from PIL import Image

# Load new model
ocr = QariOCR("models/FT{N}_QariOCR")

# Test on sample image
img = Image.open("database/reference_imgs/001.jpg")
text = ocr.extract(img)
print(text)
```

### 5.2 Evaluation Metrics

Calculate WER/CER:
- Word Error Rate (WER): Should be < 0.05 for good model
- Character Error Rate (CER): Should be < 0.02

Compare against:
- FT1 baseline (WER: 0.045, CER: 0.012)
- Perfect pages (should maintain accuracy)
- Error pages (should detect, not auto-correct)

### 5.3 Integration Testing

1. Run app: `streamlit run app_enhanced.py`
2. Upload test page (perfect and with errors)
3. Verify:
   - OCR extraction quality
   - Error detection (no auto-correction)
   - Missing line detection accuracy
   - Report generation works

## 6. Common Issues & Solutions

### Issue: Model auto-corrects errors
**Solution**: 
- Improve prompt (explicit "extract exactly what you see")
- Rebalance data (more error examples, ~40/60 ratio)
- Increase LoRA rank (16 → 24)

### Issue: Training loss not decreasing
**Solution**:
- Check learning rate (try 1e-4 or 5e-5)
- Verify data format matches expected structure
- Check batch size (reduce if OOM)

### Issue: Overfitting
**Solution**:
- Reduce epochs (2 instead of 3)
- Increase dropout (0.1 → 0.15)
- Add more diverse training data

### Issue: Model won't load in app
**Solution**:
- Verify `adapter_config.json` exists
- Check base model matches (Qwen2-VL-2B-Instruct)
- Ensure tokenizer files are present

## 7. Next Steps

After successful training:
1. ✅ Document in `Creating_MI-MUALLIM.md`
2. ✅ Update `Docs/MODELS.md` if architecture changed
3. ✅ Add sample report PDF
4. ✅ Test thoroughly before deploying
5. ✅ Consider FT{N+1} improvements (collect more real errors, etc.)

## Resources

- **FT1 Analysis**: `Docs/FINE_TUNING_ANALYSIS.md`
- **FT2 Plan**: `QariOCR_Finetuning/FT2/FT2_IMPLEMENTATION_GUIDE.md`
- **Version Registry**: `QariOCR_Finetuning/Creating_MI-MUALLIM.md`
- **Unsloth Docs**: https://github.com/unslothai/unsloth
- **Qwen2-VL Docs**: https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct

