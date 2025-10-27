# 🚀 Quick Start: Train QariOCR in 4 Simple Steps

## TL;DR

1. **Upload** dataset to Google Drive (15 min)
2. **Open** this notebook in Colab: `QariOCR_Qwen2VL_Training_Colab.ipynb`
3. **Run all cells** (click Runtime → Run all)
4. **Wait** 4-6 hours, download trained model

---

## Step 1: Upload to Google Drive (15 minutes)

### Files to Upload:

From your MacBook `/Users/Engku/Downloads/v3Quran_Verificator/`:

```bash
training_data/enhanced/train_enhanced.json           → Google Drive
training_data/enhanced/val_enhanced.json             → Google Drive  
../database/reference_imgs/* (604 images)               → Google Drive
../database/extracted_examples/*.jpg (73 JPG files ONLY) → Google Drive
```


### Google Drive Structure:

```
My Drive/
└── QariOCR_Training/
    ├── train_enhanced.json 
    ├── val_enhanced.json 
    └── database/
        ├── reference_imgs/
        │   └── [604 .jpg files]
        └── extracted_examples/
            └── [124 .jpg files ONLY - no .png!]
```

---

## Step 2: Open Colab (2 minutes)

1. Go to [Google Colab](https://colab.research.google.com)
2. **File** → **Upload notebook**
3. Upload: `scripts/QariOCR_FTunsloth.ipynb` ⭐
4. **Runtime** → **Change runtime type** → **GPU (T4)** → **Save**

**Note**: This is the official Unsloth notebook, modified for QariOCR!

---

## Step 3: Run Training (5 minutes setup + 4-6 hours training)

### Option A: Run All (Easiest)
- **Runtime** → **Run all**
- Authorize Google Drive when prompted
- Keep tab open!

### Option B: Run Cell by Cell
- Run each cell from top to bottom
- Wait for ✅ before proceeding to next cell

---

## Step 4: Download Model (5 minutes)

After training completes:

1. Go to **Google Drive** → `My Drive/QariOCR_Trained_Model/`
2. **Right-click** folder → **Download**
3. Extract to: `/Users/Engku/Downloads/v3Quran_Verificator/models/trained/`

---

## 💻 Alternative: Use Unsloth's Official Notebook

If you prefer to use Unsloth's official template:

1. Go to [Unsloth Vision Notebooks](https://docs.unsloth.ai/get-started/unsloth-notebooks)
2. Open: **Qwen2.5-VL (7B)** notebook [[Link]](https://colab.research.google.com/drive/1UG5h7sKZZOlV3HGmQrKBPJ-8Av8Y0nRE?usp=sharing)
3. Modify these sections:
   - **Dataset loading**: Point to your Google Drive paths
   - **Model**: Change to `Qwen/Qwen2-VL-2B-Instruct`
   - **Training args**: Use settings from `GOOGLE_COLAB_TRAINING_GUIDE.md`

---

## ⏱️ Timeline

| Task | Time |
|------|------|
| Upload dataset | 15 min |
| Setup Colab | 2 min |
| Install packages | 3 min |
| Load model | 5 min |
| **Training** | **4-6 hours** ⏰ |
| Save & download | 5 min |
| **Total** | **~5-6 hours** |

*(Active time: ~30 min, rest is automated)*

---

## 📊 What Happens During Training

You'll see progress like this:

```
🎓 STARTING TRAINING
===========================================
⏰ Start time: 2025-10-14 09:00:00
⏱️  Estimated duration: 4-6 hours
💡 Tip: Keep this tab open!
===========================================

{'loss': 2.453, 'learning_rate': 0.00012, 'epoch': 0.33}
{'loss': 1.892, 'learning_rate': 0.00015, 'epoch': 0.67}
{'loss': 1.234, 'learning_rate': 0.00018, 'epoch': 1.00}
{'eval_loss': 0.856, 'epoch': 1.00}

... (continues for 3 epochs) ...

{'loss': 0.234, 'learning_rate': 0.00002, 'epoch': 3.00}
{'eval_loss': 0.198, 'epoch': 3.00}

===========================================
✅ TRAINING COMPLETE!
===========================================
⏰ End time: 2025-10-14 14:30:00
⏱️  Duration: 5.50 hours
📊 Final loss: 0.234
```

---

## ⚠️ Important Tips

1. **Keep tab open** - Closing Colab stops training
2. **Check GPU** - Make sure T4 GPU is enabled
3. **Monitor progress** - Check every hour or two
4. **Don't sleep MacBook** - Keep it awake (or use phone to monitor)
5. **Save checkpoints** - Auto-saved every 100 steps

---

## 🆘 Troubleshooting

### "Files not found"
Check paths in Google Drive:
```python
!ls "/content/drive/MyDrive/QariOCR_Training/"
```

### "CUDA out of memory"
Reduce batch size in training config:
```python
per_device_train_batch_size=1  # Instead of 2
```

### "Colab disconnected"
- Keep tab active
- Use Colab Pro ($10/month) for longer sessions
- Training auto-resumes from last checkpoint

---

## ✅ Success Checklist

- [ ] Dataset uploaded to Google Drive
- [ ] Colab notebook opened
- [ ] GPU enabled (T4)
- [ ] All files verified (✓ checkmarks)
- [ ] Training started
- [ ] Tab kept open for 4-6 hours
- [ ] Model downloaded after completion

---

## 📚 Full Documentation

For detailed explanations, see:

- **Complete Guide**: `GOOGLE_COLAB_TRAINING_GUIDE.md` (70+ pages)
- **Dataset Info**: `ENHANCED_DATASET_SUMMARY.md`
- **KDN Standards**: `docs/OFFICIAL_VERIFICATION_STANDARDS.md`
- **Unsloth Docs**: https://docs.unsloth.ai

---

## 🎯 After Training

1. Test model on sample pages
2. Evaluate with `evaluate_model.py`
3. Integrate with your verification engine
4. Deploy to production!

**Expected accuracy**:
- Text extraction: ~98%
- Error detection: >95%
- Diacritic accuracy: >98%

---

**Ready? Let's train! 🚀**

*For questions, refer to GOOGLE_COLAB_TRAINING_GUIDE.md*

