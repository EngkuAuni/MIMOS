## Integration Steps (After Training)

### Step 6: Update qari_ocr.py

Add model selection and LLM analysis capability:

```python
class QariOCR:
    def __init__(self, model_path, model_type="extraction"):
        """
        Args:
            model_path: Path to model adapter
            model_type: "extraction" or "verification"
        """
        self.model_path = model_path
        self.model_type = model_type
        # Load appropriate adapter
        
    def analyze_error(self, extracted_text, reference_text, context):
        """
        Use verification model to analyze errors (LLM capability)
        Only available for verification model
        
        Args:
            extracted_text: Text extracted from image
            reference_text: Expected reference text
            context: RAG context (similar verses)
        
        Returns:
            Structured error analysis with type, location, severity
        """
        if self.model_type != "verification":
            raise ValueError("analyze_error only available for verification model")
        
        # Create analysis prompt
        prompt = f"""Analyze this Quranic text discrepancy:

Extracted: {extracted_text}
Reference: {reference_text}

Context: {context}

Provide:
1. Error type (diacritic/character/word/line)
2. Location
3. Severity (CRITICAL/MAJOR/MINOR)
4. Description"""
        
        # Use model to generate analysis
        analysis = self.extract(None, prompt=prompt)
        return analysis
```

### Step 7: Update missing_line_detector.py

Implement actual QariOCR-as-LLM integration:

```python
def _generate_llm_suggestion(self, missing_text, context, surah, 
                             reference_text=None, extracted_text=None):
    """Generate intelligent suggestions using QariOCR as LLM."""
    if not self.llm_available or not self.ocr_model:
        return self._generate_basic_suggestion(missing_text, context, surah)
    
    try:
        # Use QariOCR verification model to analyze the discrepancy
        analysis = self.ocr_model.analyze_error(
            extracted_text=extracted_text,
            reference_text=reference_text,
            context=context
        )
        
        return self._format_llm_suggestion(missing_text, context, surah, analysis)
    
    except Exception as e:
        print(f"⚠️ LLM analysis failed: {e}")
        return self._generate_basic_suggestion(missing_text, context, surah)
```

### Step 8: Update app_enhanced.py

Add UI selector for FT2 models:

```python
# In sidebar
model_version = st.sidebar.selectbox(
    "🤖 Model Version",
    options=["FT1 (Current)", "FT2 Extraction", "FT2 Verification"],
    help="FT2 models trained to prevent auto-correction"
)

# Load appropriate model
if model_version == "FT2 Extraction":
    ocr_model = QariOCR("models/FT2_QariOCR_Extraction", model_type="extraction")
elif model_version == "FT2 Verification":
    ocr_model = QariOCR("models/FT2_QariOCR_Verification", model_type="verification")
else:
    ocr_model = QariOCR("models/FT1_QariOCR")
```

---

## 🧪 Testing & Validation

### Test Cases

1. **Perfect Page Test**
   - Upload clean Quran page
   - Both models should extract correctly
   - No false positives

2. **Missing Character Test**
   - Upload page with missing character
   - Extraction: Shows gap/underscore
   - Verification: Reports error with details

3. **Wrong Diacritic Test**
   - Upload page with wrong diacritic
   - Both models detect (no auto-correction)
   - Verification provides detailed analysis

4. **Multiple Errors Test**
   - Upload page with multiple errors
   - Verification provides comprehensive report
   - LLM analysis shows error types, locations, severity

5. **RAG + LLM Integration Test**
   - Verification model provides context-aware suggestions
   - Similar verses retrieved
   - Intelligent error descriptions

### Success Criteria

- ✅ Extraction model reports gaps instead of auto-correcting
- ✅ Verification model provides detailed error reports
- ✅ Both models show <5% hallucination rate
- ✅ Error detection accuracy >90% on synthetic errors
- ✅ No regression on perfect page extraction (maintain >95% accuracy)
- ✅ RAG + LLM integration working (verification model as LLM)

---

## 📊 Expected Improvements Over FT1

| Metric | FT1 | FT2 Target |
|--------|-----|------------|
| Perfect page accuracy | ~95% | >95% (maintained) |
| Error detection rate | ~60% | >90% |
| Auto-correction rate | High | <5% |
| Hallucination rate | ~15% | <5% |
| Data balance | 53/47 | 40/60 |
| LoRA rank | 16 | 24 |
| Training epochs | 3 | 5 |

---

## 📝 Documentation

### Create FT2_TRAINING_REPORT.md

After training completes, document:
1. Training methodology
2. Data distribution (40/60 split)
3. Prompt engineering changes
4. Training metrics comparison (FT1 vs FT2)
5. Test results on error detection
6. Hallucination analysis
7. Recommendations for FT3

---

## 🎯 Summary

**Completed:**
- ✅ All data generation scripts
- ✅ Training configurations
- ✅ Sample outputs validated
- ✅ Plan updated with QariOCR-as-LLM integration

**Remaining:**
1. Run data generation scripts (~35 min)
2. Create Kaggle notebook
3. Upload to Kaggle
4. Train models (4-6 hours)
5. Integrate into app
6. Test and validate
7. Document results

**Total Time Estimate:** ~6-8 hours (mostly training)

---

## 🚀 Quick Start Commands

```bash
# Navigate to scripts directory
cd /Users/Engku/Downloads/v3quran_verificator/QariOCR_Finetuning/scripts

# Run all data generation
python3 augment_perfect_pages.py --augmentations 2
python3 generate_synthetic_errors_v2.py --target-samples 800
python3 rebalance_dataset.py --model-type both

# Check outputs
ls -lh ../training_data/augmented_perfect/
ls -lh ../training_data/synthetic_errors_v2/
ls -lh ../training_data/ft2/

# Ready for Kaggle upload!
```

