import os
import json
import time
import pandas as pd
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

from app.ai_model.logistic_regression.config import (
    DATASET_PATH,
    MODEL_OUTPUT_PATH,
    METADATA_PATH,
    COEFFICIENTS_PATH,
    WEIGHTS_DIR,
    RANDOM_STATE,
    TEST_SIZE,
    MAX_ITER,
    C_VALUE,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)

def train():
    print("=== Logistic Regression Model Training (Label Reproduction Experiment) ===")
    print("WARNING: As established in the Random Forest audit, this dataset contains")
    print("synthetic labels. This training process serves only as a rule-reproduction")
    print("baseline, not proof of real-world predictive ability.")
    
    if not DATASET_PATH.exists():
        print(f"Dataset not found at {DATASET_PATH}")
        return

    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset shape: {df.shape}")
    
    required_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns: {missing_cols}")
        return
    
    if df.empty:
        print("Error: Dataset is empty")
        return
        
    df.dropna(subset=required_columns, inplace=True)
    
    target_vals = df[TARGET_COLUMN].unique()
    if not set(target_vals).issubset({0, 1}):
        print(f"Error: Target column contains values other than 0 and 1: {target_vals}")
        return
        
    print(f"Target distribution:\n{df[TARGET_COLUMN].value_counts()}")

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET_COLUMN]

    print("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), NUMERIC_FEATURES),
            ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES)
        ]
    )

    lr = LogisticRegression(
        random_state=RANDOM_STATE,
        max_iter=MAX_ITER,
        C=C_VALUE,
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', lr)
    ])

    print("Training Logistic Regression model...")
    start_time = time.time()
    pipeline.fit(X_train, y_train)
    end_time = time.time()
    print(f"Training completed in {end_time - start_time:.2f} seconds.")

    print("Evaluating model on held-out test set...")
    y_pred = pipeline.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall: {rec:.4f}")
    print(f"F1-score: {f1:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"Model saved to {MODEL_OUTPUT_PATH}")

    # Coefficients
    try:
        cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat']
        cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
        all_feature_names = NUMERIC_FEATURES + list(cat_feature_names)
        
        coefs = lr.coef_[0]
        coef_df = pd.DataFrame({
            'feature': all_feature_names,
            'coefficient': coefs,
            'abs_coefficient': [abs(c) for c in coefs]
        }).sort_values(by='abs_coefficient', ascending=False)
        
        coef_df.to_csv(COEFFICIENTS_PATH, index=False)
        print("\nTop Coefficients:")
        print(coef_df.head(10))
        
    except Exception as e:
        print(f"Error extracting coefficients: {e}")

    # Save Metadata
    metadata = {
        "model_name": "Logistic Regression Maintenance Need Prediction (Synthetic Rule Reproduction)",
        "target": TARGET_COLUMN,
        "feature_names": NUMERIC_FEATURES + CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "training_sample_count": len(X_train),
        "test_sample_count": len(X_test),
        "random_state": RANDOM_STATE,
        "hyperparameters": {
            "max_iter": MAX_ITER,
            "C": C_VALUE,
            "solver": lr.solver
        },
        "evaluation_metrics": {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1
        },
        "dataset_filename": "ESC 12 Pavement Dataset.csv",
        "trained_timestamp": datetime.now().isoformat(),
        "limitations": "Dataset uses synthetic rule-generated labels. Model is only valid as a rule-reproduction baseline."
    }
    
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved to {METADATA_PATH}")

if __name__ == "__main__":
    train()
