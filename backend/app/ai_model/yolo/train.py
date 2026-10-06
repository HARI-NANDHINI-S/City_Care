import os
import argparse
import sys
import shutil
import torch
from pathlib import Path
from ultralytics import YOLO
from backend.app.ai_model.yolo import config

def train_model(data_path=config.DATASET_YAML, epochs=config.EPOCHS, batch=config.BATCH_SIZE, imgsz=config.IMG_SIZE, device_override=None):
    if not os.path.exists(data_path):
        print(f'[ERROR] Dataset configuration {data_path} not found.')
        sys.exit(1)
        
    cuda_available = torch.cuda.is_available()
    device = device_override if device_override else (0 if cuda_available else 'cpu')
    print(f'[INFO] Hardware check: CUDA available = {cuda_available} (Device: {device})')
    
    if str(device) == 'cpu':
        print('[WARNING] CUDA is NOT available. Running on CPU mode.')
        print('YOLO CODE READY\nTRAINING NOT RUN LOCALLY\nGPU REQUIRED/RECOMMENDED FOR PRACTICAL TRAINING')
        return

    print(f'[INFO] Initializing YOLO model with {config.MODEL_NAME}')
    model = YOLO(config.MODEL_NAME)
    
    try:
        results = model.train(
            data=str(data_path),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            name='yolo_run',
            project='runs/detect',
            device=device
        )
        
        save_dir = getattr(model.trainer, 'save_dir', 'runs/detect/yolo_run')
        best_weights_src = Path(save_dir) / 'weights' / 'best.pt'
        
        if best_weights_src.exists():
            os.makedirs(config.ARTIFACT_DIR, exist_ok=True)
            shutil.copy(best_weights_src, config.BEST_MODEL_PATH)
            print(f'[SUCCESS] Trained weights saved & copied to {config.BEST_MODEL_PATH}')
        else:
            print(f'[WARNING] Could not find best.pt at {best_weights_src}')
            
    except Exception as e:
        print(f'[ERROR] Training failed: {str(e)}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default=str(config.DATASET_YAML))
    parser.add_argument('--epochs', type=int, default=config.EPOCHS)
    parser.add_argument('--imgsz', type=int, default=config.IMG_SIZE)
    parser.add_argument('--batch', type=int, default=config.BATCH_SIZE)
    parser.add_argument('--device', type=str, default=None)
    args = parser.parse_args()
    
    train_model(args.data, args.epochs, args.batch, args.imgsz, args.device)
