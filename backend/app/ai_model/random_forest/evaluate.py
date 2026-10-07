import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from backend.app.ai_model.random_forest.config import (
    DATASET_PATH,
    MODEL_OUTPUT_PATH,
    RANDOM_STATE,
    TEST_SIZE,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)

def evaluate_model(model_path=None, data_path=None):
    if model_path is None:
        model_path = MODEL_OUTPUT_PATH
    if data_path is None:
        data_path = DATASET_PATH

    if not model_path.exists():
        print(f"Error: Model not found at {model_path}. Please train first.")
        return
        
    if not data_path.exists():
        print(f"Error: Dataset not found at {data_path}.")
        return

    print("Loading model...")
    pipeline = joblib.load(model_path)
    
    print("Loading dataset...")
    df = pd.read_csv(data_path)
    
    required_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
    df.dropna(subset=required_columns, inplace=True)
    
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET_COLUMN]

    print("Splitting dataset...")
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    
    print("Evaluating model on test split...")
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


if __name__ == "__main__":
    evaluate_model()
