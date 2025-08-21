# Robotics Object Detection: AIPOPA Loose Fruitlet Collector

This module documents the object detection training workflow for the AIPOPA (Loose Fruitlet Collector) robot — part of the Strategic ICT R&D initiative at MIMOS Berhad.

The objective was to train a lightweight fruitlet detection model using **YOLOv8**, enabling the robot to selectively identify and vacuum ripe oil palm fruitlets from the ground.

> See also: [Week 1 Internship Log](../Logs/Week1.md)

---

## Training Notebook

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/EngkuAuni/MIMOS-GenAi/blob/main/Robotics_ObjDetection/LFC_Training.ipynb)

This notebook walks through the full training pipeline:
- Dataset loading from Roboflow (~240 annotated images)
- YOLOv8 configuration and training on Google Colab
- Model evaluation and export of trained weights

---

## Objective

- Enable fruitlet detection on natural ground scenes
- Ensure compatibility with AIPOPA’s embedded hardware
- Support real-time robotic vacuum selection logic

---

## Training Summary

| Item | Details |
|------|---------|
| Framework | YOLOv8 (Ultralytics) |
| Dataset | 306 images (Roboflow annotation) |
| Training | 50 epochs on Google Colab |
| Outputs | `best.pt`, `pmetrics.png`, test video |
| Deployment | Successfully tested on the AIPOPA robot |

---

## Results

| File | Description |
|------|-------------|
| `results/best.pt` | Final trained YOLOv8 weights |
| `results/pmetrics.png` | Loss & accuracy graph from training |
| `results/AIPOPA_training.mp4` | Robot field test using trained model |

### Video Demo

▶️ [Watch Robot Test Video](./results/AIPOPA_training.mp4)

> Demonstrates the robot identifying ripe fruitlets using the trained model.

---

## Tools Used

- Roboflow (image annotation)
- Google Colab (training environment)
- YOLOv8 (Ultralytics)
- Python, PyTorch
- Visual Studio Code