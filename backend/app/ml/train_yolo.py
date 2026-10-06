import os
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 for CivicVision")
    parser.add_argument("--data", type=str, help="Path to data.yaml (e.g., datasets/RDD2020/data.yaml)", required=True)
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Pretrained YOLO model to start with")
    parser.add_argument("--name", type=str, default="civicvision_v1", help="Name of the training run")
    
    args = parser.parse_args()
    
    print(f"=====================================")
    print(f" YOLO MODEL TRAINING PIPELINE")
    print(f"=====================================")
    
    if not os.path.exists(args.data):
        print(f"[ERROR] Dataset configuration {args.data} not found.")
        print(f"Training not executed because hardware/dataset availability is insufficient.")
        sys.exit(1)
        
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] ultralytics package not installed. Cannot train YOLO.")
        print(f"Training not executed because hardware/dataset availability is insufficient.")
        sys.exit(1)
        
    print(f"[INFO] Initializing YOLO model with {args.model}")
    model = YOLO(args.model)
    
    print(f"[INFO] Starting training on {args.data} for {args.epochs} epochs")
    try:
        # Run training
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            name=args.name,
            project="runs/detect"
        )
        print("\n[EVALUATION RESULTS]")
        # Evaluate model performance on the validation set
        metrics = model.val()
        print(f"mAP50-95: {metrics.box.map}")
        print(f"mAP50: {metrics.box.map50}")
        
        print("\n[INFO] Training complete.")
        print(f"[INFO] Best weights saved to runs/detect/{args.name}/weights/best.pt")
        
    except Exception as e:
        print(f"[ERROR] Training failed: {str(e)}")
        print(f"Training not executed because hardware/dataset availability is insufficient.")

if __name__ == "__main__":
    main()
