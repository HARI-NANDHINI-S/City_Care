# CivicVision AI — AI Model & Dataset Specification

## Overview
CivicVision AI uses Computer Vision and Deep Learning (Ultralytics YOLOv8 / YOLOv11 & OpenCV) for automated public infrastructure defect detection.

This document details the dataset requirements, annotation standard, model training pipeline, and backend integration instructions.

---

## 1. Supported Issue Classes

| Class ID | Class Name | Description | Key Visual Indicators |
| :--- | :--- | :--- | :--- |
| `0` | `Pothole` | Asphalt cracks, surface depressions, road holes | Circular/irregular tarmac breaks |
| `1` | `Garbage Accumulation` | Overflowing dumpsters, roadside trash piles | Scattered waste bags, plastic waste |
| `2` | `Waterlogging` | Submerged roads, standing rainwater pools | High reflection water covering lane |
| `3` | `Broken Streetlight` | Damaged light poles, dark unlit fixtures | Fractured glass, fallen street lamps |
| `4` | `Open Manhole` | Missing or displaced sewer cover rings | Uncovered dark round/square holes |
| `5` | `Road Damage` | Long pavement fissures, asphalt crumbling | Parallel cracks, structural degradation |

---

## 2. Dataset Requirements & Annotation Standard

- **Recommended Image Quantity**: 1,000 to 5,000 annotated images per class.
- **Image Resolution**: Minimum 640x640 pixels (JPEG/PNG format).
- **Annotation Format**: Standard YOLO v8 Darknet format.
  - One `.txt` label file per image with normalized bounding coordinates:
    ```text
    <class_id> <x_center> <y_center> <width> <height>
    ```
  - Coordinates normalized between `0.0` and `1.0`.

### Recommended Open-Source Datasets:
1. **Roboflow Universe**: Search for "Smart City Infrastructure", "Pothole Detection Dataset", "Open Manhole Bounding Boxes".
2. **Kaggle Pothole & Road Damage Dataset**: "Global Road Damage Detection Challenge (GRDDC)".

---

## 3. Training Instructions

### Step 1: Create Data Specification File (`civic_sense.yaml`)
```yaml
path: ./dataset
train: images/train
val: images/val
test: images/test

names:
  0: Pothole
  1: Garbage Accumulation
  2: Waterlogging
  3: Broken Streetlight
  4: Open Manhole
  5: Road Damage
```

### Step 2: Run Ultralytics YOLO Training Command
```bash
yolo detect train \
  data=civic_sense.yaml \
  model=yolov8n.pt \
  epochs=50 \
  imgsz=640 \
  batch=16 \
  name=civicvision_v1
```

### Step 3: Export Trained Model Weights
Once training completes, the best weights will be saved to `runs/detect/civicvision_v1/weights/best.pt`.
Copy `best.pt` into `backend/app/services/weights/best.pt`.

---

## 4. Backend Integration
The `ai-model/model_loader.py` script automatically checks for `best.pt`.
If custom weights are detected, it invokes real PyTorch YOLO inference. If weights are not present during local evaluation, it dynamically defaults to the CivicVision Vision Engine.
