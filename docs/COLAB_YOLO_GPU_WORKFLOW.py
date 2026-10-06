# ==============================================================================
# CIVICVISION AI — GOOGLE COLAB CUDA GPU TRAINING & TEST EVALUATION SCRIPT
# ==============================================================================
# Instructions for User:
# 1. Open Google Colab (https://colab.research.google.com/)
# 2. Go to Runtime -> Change runtime type -> Select T4 GPU (or any available CUDA GPU)
# 3. Paste and run each cell below in sequence.
# ==============================================================================

# ------------------------------------------------------------------------------
# CELL 1: VERIFY GPU & CUDA ENVIRONMENT
# ------------------------------------------------------------------------------
import torch
print("====================================")
print("GOOGLE COLAB GPU ENVIRONMENT CHECK")
print("====================================")
cuda_avail = torch.cuda.is_available()
print(f"CUDA Available: {cuda_avail}")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Version: {torch.version.cuda}")

if cuda_avail:
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"GPU Name: {gpu_name}")
    print(f"GPU Memory: {gpu_mem:.2f} GB")
else:
    print("GPU: NONE — Please enable T4 GPU runtime before proceeding!")
    assert False, "GPU Runtime required!"

# ------------------------------------------------------------------------------
# CELL 2: CLONE REPOSITORY & INSTALL DEPENDENCIES
# ------------------------------------------------------------------------------
# %cd /content
# !git clone https://github.com/HARI-NANDHINI-S/City_Care.git
# %cd City_Care
# !pip install -q ultralytics

import os
import ultralytics
print(f"[+] Ultralytics Version: {ultralytics.__version__}")
print(f"[+] Current Working Directory: {os.getcwd()}")

# ------------------------------------------------------------------------------
# CELL 3: DATASET VALIDATION BEFORE TRAINING
# ------------------------------------------------------------------------------
# !python backend/app/ml/validate_yolo_dataset.py --data datasets/RDD2020/data.yaml

# ------------------------------------------------------------------------------
# CELL 4: EXECUTE REAL YOLOv8 TRAINING ON GPU
# ------------------------------------------------------------------------------
from ultralytics import YOLO

print("\n====================================")
print("STARTING REAL YOLOv8 GPU TRAINING")
print("====================================")

model = YOLO("yolov8n.pt")

results = model.train(
    data="datasets/RDD2020/data.yaml",
    epochs=50,
    imgsz=640,
    batch=16,
    name="civicvision_colab_run",
    project="runs/detect",
    device=0
)

best_pt_path = "runs/detect/civicvision_colab_run/weights/best.pt"
print(f"\n[+] Genuine Trained Model Saved At: {best_pt_path}")
print(f"[+] Model Exists: {os.path.exists(best_pt_path)}")

# ------------------------------------------------------------------------------
# CELL 5: HELD-OUT TEST SET EVALUATION (323 IMAGES)
# ------------------------------------------------------------------------------
print("\n====================================")
print("HELD-OUT TEST SET EVALUATION (323 IMAGES)")
print("====================================")

trained_model = YOLO(best_pt_path)

# Evaluate on test split
test_metrics = trained_model.val(
    data="datasets/RDD2020/data.yaml",
    split="test",
    imgsz=640,
    batch=16
)

print("\n[+] TEST SET METRICS:")
print(f"    - Precision: {test_metrics.box.mp:.4f}")
print(f"    - Recall: {test_metrics.box.mr:.4f}")
print(f"    - mAP@0.5: {test_metrics.box.map50:.4f}")
print(f"    - mAP@0.5:0.95: {test_metrics.box.map:.4f}")

print("\n[+] PER-CLASS METRICS:")
for i, name in trained_model.names.items():
    p = test_metrics.box.p[i] if i < len(test_metrics.box.p) else 0.0
    r = test_metrics.box.r[i] if i < len(test_metrics.box.r) else 0.0
    map50 = test_metrics.box.ap50[i] if i < len(test_metrics.box.ap50) else 0.0
    print(f"    - Class {i} ({name}): Precision={p:.4f}, Recall={r:.4f}, mAP50={map50:.4f}")

# ------------------------------------------------------------------------------
# CELL 6: DOWNLOAD TRAINED WEIGHTS TO LOCAL PROJECT
# ------------------------------------------------------------------------------
# from google.colab import files
# files.download(best_pt_path)
# 
# Place downloaded best.pt into:
# backend/app/services/weights/best.pt
