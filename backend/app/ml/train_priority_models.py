import os
import argparse
import pandas as pd
from app.ml.models import CivicVisionPriorityModels
from app.ml.dataset import generate_synthetic_priority_dataset

def main():
    parser = argparse.ArgumentParser(description="Train Priority ML Models")
    parser.add_argument("--data", type=str, help="Path to real structured priority dataset (CSV)", default=None)
    parser.add_argument("--synthetic", action="store_true", help="Generate and use synthetic development data instead of real data")
    parser.add_argument("--out", type=str, help="Output directory for saved models", default="backend/app/services/weights")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.out, exist_ok=True)

    print(f"=====================================")
    print(f" PRIORITY MODEL TRAINING PIPELINE")
    print(f"=====================================")
    
    if args.data and os.path.exists(args.data):
        print(f"[INFO] Loading real dataset from {args.data}")
        df = pd.read_csv(args.data)
        dataset_type = "REAL"
    elif args.synthetic:
        print(f"[INFO] No real dataset provided. Generating synthetic priority dataset.")
        df = generate_synthetic_priority_dataset(2000)
        dataset_type = "SYNTHETIC (Mocked Data)"
    else:
        print(f"[ERROR] No real dataset provided, and --synthetic flag is not set.")
        print(f"[ERROR] Please provide --data <path> or use --synthetic.")
        return

    print(f"[INFO] Dataset size: {len(df)} records")
    
    # Initialize Model System
    ml_system = CivicVisionPriorityModels(model_dir=args.out)
    
    print("[INFO] Training Decision Tree, Logistic Regression, Random Forest, Gradient Boosting...")
    results = ml_system.train_and_evaluate(df)
    
    print("\n[EVALUATION RESULTS]")
    for model_name, metrics in results.items():
        print(f" - {model_name}: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.4f}")
    
    # Record metadata
    metadata = {
        "dataset_type": dataset_type,
        "dataset_size": len(df),
        "results": results
    }
    import json
    with open(os.path.join(args.out, "priority_models_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n[INFO] Models and metadata saved to {args.out}")
    print(f"[STATUS] Training completed successfully using {dataset_type} dataset.")

if __name__ == "__main__":
    main()
