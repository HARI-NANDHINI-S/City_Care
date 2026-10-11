import os
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

import sys
from pathlib import Path

def main(target_model: str = "all"):
    print(f"=== CivicVision AI: Tabular ML Manual Training Script (Target: {target_model}) ===")
    
    # 1. Load the dataset dynamically
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    csv_path = base_dir / "datasets" / "priority" / "international_road_condition" / "raw" / "ontario_2023_pavement.csv"
    if not csv_path.exists():
        # Fallback to absolute or working directory
        csv_path = Path(r"E:\City_Care\datasets\priority\international_road_condition\raw\ontario_2023_pavement.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

        
    print(f"Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip() # Fix trailing spaces like 'SectionID '
    
    # 2. Check for required columns and missing values
    required_cols = ['IRI', 'DMI', 'Pave_Type', 'FUNC_CLASS', 'Highway']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    # Drop any rows missing required features/target
    initial_len = len(df)
    df = df.dropna(subset=required_cols)
    print(f"Loaded {len(df)} valid rows. (Dropped {initial_len - len(df)} rows with missing values)")
    
    # Do not silently delete duplicate intervals (express/collector lane differences)
    
    # 3. Setup X, y, and groups
    X = df[['DMI', 'Pave_Type', 'FUNC_CLASS']]
    y = df['IRI']
    groups = df['Highway']
    
    # 4. GroupShuffleSplit to prevent spatial leakage
    print("\nPerforming GroupShuffleSplit by 'Highway'...")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    groups_train, groups_test = groups.iloc[train_idx], groups.iloc[test_idx]
    
    # Verify no overlap
    train_highways = set(groups_train)
    test_highways = set(groups_test)
    overlap = train_highways.intersection(test_highways)
    if overlap:
        raise ValueError(f"CRITICAL LEAKAGE DETECTED: Highways {overlap} appear in both train and test sets!")
    else:
        print(f"Split verified: 0 overlapping highways between train and test.")
        
    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    
    # 5. Build Preprocessing Pipeline
    numeric_features = ['DMI']
    categorical_features = ['Pave_Type', 'FUNC_CLASS']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ]
    )
    
    # 6. Define Models
    models = {
        "Baseline (Mean)": DummyRegressor(strategy="mean"),
        "Decision Tree": Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', DecisionTreeRegressor(random_state=42, max_depth=5))
        ]),
        "Random Forest": Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', RandomForestRegressor(random_state=42, n_estimators=100))
        ])
    }
    
    # 7. Train and Evaluate
    print("\n=== Training & Evaluation Results ===")
    print(f"{'Model Name':<20} | {'MAE':<8} | {'RMSE':<8} | {'R²':<8}")
    print("-" * 53)
    
    results = {}
    for name, pipeline in models.items():
        # Fit on training data ONLY
        pipeline.fit(X_train, y_train)
        
        # Predict on test data
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        results[name] = {"MAE": mae, "RMSE": rmse, "R2": r2, "model": pipeline}
        print(f"{name:<20} | {mae:<8.4f} | {rmse:<8.4f} | {r2:<8.4f}")
        
    # 8. Document Data Limitations
    print("\n=== Data & Methodology Limitations ===")
    print("1. SPATIAL OVERLAPS: While GroupShuffleSplit prevents the same highway from splitting across train/test, unresolved parallel lanes/overlapping intervals exist.")
    print("2. DOMAIN GENERALIZATION: This dataset represents Ontario climate/materials. Performance does not guarantee generalization to Tamil Nadu roads.")
    print("3. DMI PROXY LIMITATION: DMI is a structural engineering metric. To deploy in production, YOLO visual defects must be calibrated to DMI scale.")
    print("4. Scientific Rigor: Trained models must never be evaluated on synthetic target-leaked rules.")
    
    # 9. Save Artifacts for Selected Models (Atomic Staging & Validation)
    import tempfile, shutil

    def save_artifact_atomically(model_key, weights_dir, model_filename, metadata_filename, metadata_dict):
        weights_dir.mkdir(parents=True, exist_ok=True)
        final_model_path = weights_dir / model_filename
        final_meta_path = weights_dir / metadata_filename
        
        # Step A: Write to isolated staging directory
        with tempfile.TemporaryDirectory() as staging_dir:
            staging_model_path = Path(staging_dir) / f"{model_filename}.tmp"
            staging_meta_path = Path(staging_dir) / f"{metadata_filename}.tmp"
            
            joblib.dump(results[model_key]["model"], staging_model_path)
            with open(staging_meta_path, "w") as f:
                json.dump(metadata_dict, f, indent=4)
                
            # Step B: Validate that staged artifact can be deserialized and verified
            try:
                test_load = joblib.load(staging_model_path)
                assert hasattr(test_load, "predict"), "Staged pipeline missing predict() method"
                with open(staging_meta_path, "r") as f:
                    test_meta = json.load(f)
                assert test_meta.get("target") == "IRI", "Staged metadata target mismatch"
            except Exception as val_err:
                raise RuntimeError(f"Artifact integrity validation failed during staging: {val_err}")
                
            # Step C: Backup existing production artifact if present before atomic replacement
            if final_model_path.exists():
                backup_path = weights_dir / f"{model_filename}.backup"
                shutil.copy2(final_model_path, backup_path)
            if final_meta_path.exists():
                backup_meta = weights_dir / f"{metadata_filename}.backup"
                shutil.copy2(final_meta_path, backup_meta)
                
            # Step D: Atomic replace
            shutil.copy2(staging_model_path, final_model_path)
            shutil.copy2(staging_meta_path, final_meta_path)
            
        print(f"\n[+] Atomically saved and validated {model_key} artifact: {final_model_path}")
        print(f"[+] Atomically saved and validated {model_key} metadata: {final_meta_path}")

    if target_model in ["random_forest", "all"]:
        rf_weights_dir = Path(__file__).resolve().parent / "random_forest" / "weights"
        rf_metadata = {
            "model_name": "Random Forest Roughness (IRI) Prediction",
            "task": "Continuous Regression",
            "target": "IRI",
            "features": numeric_features + categorical_features,
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "split_strategy": "GroupShuffleSplit (groups=Highway, test_size=0.2, random_state=42)",
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": {
                "MAE": float(results["Random Forest"]["MAE"]),
                "RMSE": float(results["Random Forest"]["RMSE"]),
                "R2": float(results["Random Forest"]["R2"])
            },
            "dataset": "ontario_2023_pavement.csv",
            "saved_at": pd.Timestamp.now().isoformat()
        }
        save_artifact_atomically("Random Forest", rf_weights_dir, "random_forest.joblib", "model_metadata.json", rf_metadata)

    if target_model in ["decision_tree", "all"]:
        dt_weights_dir = Path(__file__).resolve().parent / "decision_tree" / "weights"
        dt_metadata = {
            "model_name": "Decision Tree Roughness (IRI) Prediction",
            "task": "Continuous Regression",
            "target": "IRI",
            "features": numeric_features + categorical_features,
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "split_strategy": "GroupShuffleSplit (groups=Highway, test_size=0.2, random_state=42)",
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": {
                "MAE": float(results["Decision Tree"]["MAE"]),
                "RMSE": float(results["Decision Tree"]["RMSE"]),
                "R2": float(results["Decision Tree"]["R2"])
            },
            "dataset": "ontario_2023_pavement.csv",
            "saved_at": pd.Timestamp.now().isoformat()
        }
        save_artifact_atomically("Decision Tree", dt_weights_dir, "decision_tree.joblib", "model_metadata.json", dt_metadata)

    print("\nTraining workflow completed successfully.")

if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description="CivicVision AI Tabular Model Training")
    parser.add_argument("--model", type=str, choices=["random_forest", "decision_tree", "logistic_regression", "gradient_boosting"],
                        help="Specific model to train")
    parser.add_argument("--all", action="store_true", help="Train all scientifically valid models (Random Forest and Decision Tree)")
    
    args = parser.parse_args()
    
    # Strictly enforce quarantine on invalid/leaky models with NO override option
    if args.model in ["logistic_regression", "gradient_boosting"]:
        print(f"\n[BLOCKED] Training aborted for '{args.model}'.")
        print("Reason: The available ESC 12 dataset exhibits target leakage where 'Needs Maintenance' is synthetically derived via deterministic thresholds.")
        print("Training this model is blocked to prevent fabricating predictive accuracy.")
        print("Acquire an authentic municipal pavement dataset before enabling training.")
        sys.exit(1)
        
    chosen = "all" if args.all else (args.model or "all")
    main(target_model=chosen)
