# 🚀 Quick Start - Quran Verification Engine

## Access the Application
```
http://localhost:8501
```

---

## 🎯 For KDN Verification Work

### Recommended Settings:
1. Open sidebar → **"🔍 OCR Mode"**
2. Select: **"Tesseract (Raw - no hallucination)"**
3. Upload Quran page images
4. Review results

**Why Tesseract?**
- ✅ Detects missing characters/errors
- ✅ Won't auto-correct (shows actual issues)
- ✅ Fast: 2-3 seconds per page
- ✅ 1200-1800 pages/hour (12-18x KDN requirement)

---

## 🔍 If You Suspect Hallucination

### Use Hybrid Mode:
1. Sidebar → **"Hybrid (Show both)"**
2. Upload image
3. Compare two outputs:
   - 🤖 QariOCR (may auto-correct)
   - 🔍 Tesseract (raw extraction)
4. Watch for **🚨 HALLUCINATION ALERT**

**When Alert Appears:**
- QariOCR likely filled in errors
- Use Tesseract output for verification
- Report the actual error found

---

## 📊 What You'll See

### Section 1: Extracted Text
Two boxes (if Hybrid mode):
- QariOCR output (accurate but may correct)
- Tesseract output (raw, no correction)

### Section 2: Extracted Verses
Line-by-line display of verses

### Section 3: Verification Results
- OCR Accuracy %
- Mismatches Found
- Visual Flags

### Section 4: Database Comparison Table
- OCR Extracted column
- Database Reference column
- Match % scores
- Status (✅ Match or ❌ Mismatch)

---

## ⚡ Quick Commands

### Check Status
```bash
/Users/Engku/Downloads/v3quran_verificator/Server/check_status.sh
```

### Monitor OCR Processing
```bash
/Users/Engku/Downloads/v3quran_verificator/Server/monitor_ocr.sh
```

### Restart Container
```bash
cd /Users/Engku/Downloads/v3quran_verificator/Server
docker-compose -f docker-compose-mac-studio-dev.yml restart
```

### View Logs
```bash
docker logs quran-verifier-mac-studio-dev -f
```

### Stop Container
```bash
cd /Users/Engku/Downloads/v3quran_verificator/Server
docker-compose -f docker-compose-mac-studio-dev.yml down
```

---

## 🎯 Testing Your Findings

### Test Missing Character Issue:
1. Upload image with missing character
2. Use Hybrid mode
3. Verify:
   - ✅ Tesseract shows gap
   - ⚠️ QariOCR may fill it
   - 🚨 Alert appears

---

## 📈 Performance

| Mode | Time/Page | Pages/Hour | Best For |
|------|-----------|------------|----------|
| **Tesseract** | 2-3 sec | 1200-1800 | Error detection |
| **Hybrid** | 60-90 sec | 40-60 | Thorough verification |
| QariOCR | 60-90 sec | 40-60 | Clean images only |

**KDN Requirement**: 100 pages/hour  
**Tesseract Mode**: 1200-1800 pages/hour (✅ 12-18x faster!)

---

## 🆘 Troubleshooting

### Can't Access http://localhost:8501
```bash
# Check container is running
docker ps | grep quran-verifier

# If not running, start it:
cd /Users/Engku/Downloads/v3quran_verificator/Server
docker-compose -f docker-compose-mac-studio-dev.yml up -d
```

### OCR Taking Too Long
- Switch to Tesseract mode (2-3 sec vs 60-90 sec)

### Seeing Hallucinations
- Use Tesseract mode or Hybrid mode
- Check alert boxes for warnings

---

**Ready to start verifying!** 🚀

Open: http://localhost:8501
