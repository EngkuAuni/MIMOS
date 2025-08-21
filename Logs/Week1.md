# Internship Log — Week 1 (Aug 13–15)

### Project: AIPOPA (Loose Fruitlet Collector)
Trained a custom object detection model for a robotics use case using YOLOv8. The model identifies ripe fruitlets to assist the AIPOPA robot in selective vacuuming/retrieving tasks.

#### 1. Dataset Annotation & Training
- Annotated ~300 fruitlet images in **Roboflow**.
- Created a YOLOv8-compatible dataset version.
- Trained the dataset using **YOLOv8** on **Google Colab** (50 epochs).
- Exported and reviewed:
  - `best.pt` (trained weights)
  - `pmetrics.png` (performance metrics)
- Weight file was successfully tested on the physical robot — able to detect good-condition fruitlets selectively.

#### 2. Streamlit Environment Setup
- Created a basic **Streamlit test app** on local VSC environment to verify setup.

#### 3. Documentation Support – AIPOPA Unit Testing Report
- Assisted Mr. Amirullah with unit testing documentation.
- Converted Functionality & Reliability Testing content from PDF to Excel for use in UTR (Unit Testing Requirement) report preparation.

---

### Tools Used
- Roboflow (image annotation & versioning)
- Google Colab (model training)
- YOLOv8 (Ultralytics)
- Python, PyTorch
- Streamlit
- Visual Studio Code

---

### Project Artifacts (Stored locally; not all committed to repo)
- `best.pt` — final trained weights
- `pmetrics.png` — training loss/accuracy graph
- `test_app.py` — basic app to verify deployment readiness
- `docs/AIPOPA-LFC_UTR.xlsx` — internal document, extracted from PDF

---

### Notes
- This was my first time contributing to a robotics-related deployment — very rewarding to see the model run successfully on hardware.
- Roboflow’s annotation tools were helpful, but annotating grass-background fruitlets was time-intensive.
- Looking forward to shifting into the GenAI application track next week.

---