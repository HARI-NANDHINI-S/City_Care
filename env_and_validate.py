import sys
import os

try:
    import torch
    import ultralytics
    import numpy
    import cv2
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

print("ENVIRONMENT")
print(f"Python: {sys.version.split()[0]}")
print(f"PyTorch: {torch.__version__}")
print(f"Ultralytics: {ultralytics.__version__}")
print(f"NumPy: {numpy.__version__}")
print(f"OpenCV: {cv2.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA device memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print("Training device: GPU")
else:
    print("GPU: None")
    print("Training device: CPU")

sys.path.append(os.path.abspath('backend/app/ml'))
from validate_yolo_dataset import validate_yolo_dataset

print("\nDATASET VALIDATION")
yaml_path = r"E:\City_Care\datasets\RDD2020\data.yaml"
if not validate_yolo_dataset(yaml_path):
    print("Validation failed!")
    sys.exit(1)
print("Validation passed!")
