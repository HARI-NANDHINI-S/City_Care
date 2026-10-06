# GPU Training Guide

Since your local Windows environment does not have CUDA/GPU acceleration, training YOLO locally will be extremely slow. 

Follow this process to train the YOLO model using a free external GPU environment and integrate it back into CivicVision.

### 1. Preparation
Ensure you have completed the `DATASET_SETUP_CHECKLIST.md` and your `datasets/RDD2020` directory is fully prepared locally. Zip this directory:
```bash
zip -r rdd2020_yolo.zip datasets/RDD2020/
```

### 2. Choose a GPU Platform
You can use **Google Colab** or **Kaggle** (both offer free GPU access). Google Colab is recommended for simplicity.

### 3. Google Colab Setup
1. Go to [Google Colab](https://colab.research.google.com/).
2. Create a new notebook.
3. Go to **Runtime > Change runtime type** and select **T4 GPU**.
4. Upload your `rdd2020_yolo.zip` to the Colab environment.

### 4. Training Script in Colab
Run the following cells in your Colab notebook:

**Cell 1: Setup**
```python
!pip install ultralytics
!unzip -q rdd2020_yolo.zip -d /content/
```

**Cell 2: Train**
```python
from ultralytics import YOLO

# Initialize
model = YOLO('yolov8n.pt')

# Train (Make sure data.yaml paths point to absolute /content/... paths inside Colab)
results = model.train(data='/content/datasets/RDD2020/data.yaml', epochs=50, imgsz=640, batch=16, project='/content/runs')
```

### 5. Download the Weights
Once training completes, the best weights will be saved in Colab at:
`/content/runs/train/weights/best.pt`

Right-click this file in the Colab file explorer and click **Download**.

### 6. Integrate into CivicVision
Place the downloaded `best.pt` file into the local project:
`e:\City_Care\backend\app\services\weights\best.pt`

### 7. Priority Model Training (Local)
The priority models (Random Forest, etc.) do not require GPU acceleration and can be trained quickly on your local CPU once the priority CSV is ready:
```bash
python backend/app/ml/train_priority_models.py --data datasets/priority/actual_dataset.csv
```
