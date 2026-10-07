# Random Forest Maintenance Need Prediction

## Purpose
This module implements a binary classification Random Forest model to predict whether a road segment requires maintenance. It serves as an ML signal to the overall CivicVision priority engine.

**Note:** This is a binary maintenance-need model (Needs Maintenance: 0 or 1), NOT the final 4-class CivicVision priority model.

## Dataset
- **Source:** Real pavement dataset.
- **File Location:** `datasets/priority/ESC 12 Pavement Dataset.csv`
- **Rows:** 1,050,000

## Target Definition
- **Column:** `Needs Maintenance`
- **0:** No maintenance needed
- **1:** Maintenance needed

## Features
### Numeric Features
- `PCI`
- `AADT`
- `Last Maintenance`
- `Average Rainfall`
- `Rutting`
- `IRI`

### Categorical Features
- `Road Type`
- `Asphalt Type`

### Excluded
- `Segment ID`

## Preprocessing
- Missing values in required columns are dropped.
- Numeric features are passed through directly (Random Forest does not require scaling).
- Categorical features are transformed using `OneHotEncoder(handle_unknown='ignore')`.

## Configuration
- `random_state`: 42
- `test_size`: 0.20 (stratified split based on the target column)
- `n_estimators`: 200
- `max_depth`: 20
- `min_samples_split`: 10
- `min_samples_leaf`: 4

## Evaluation Metrics
During training, the model's performance on the 20% untouched test split is evaluated using:
- Accuracy
- Precision
- Recall
- F1-Score
- Classification Report
- Confusion Matrix

Metrics are documented after actual training in `weights/model_metadata.json`.

## Artifacts
The trained model and metadata are saved in the `weights/` directory:
- `random_forest.joblib`: The complete fitted pipeline (preprocessor + estimator).
- `model_metadata.json`: Contains hyperparameters, feature names, and evaluation metrics.
- `feature_importance.csv`: Contains the top features ranked by importance.

## Usage

### Training
```bash
python -m backend.app.ai_model.random_forest.train
```

### Evaluation
```bash
python -m backend.app.ai_model.random_forest.evaluate
```

### Prediction
```bash
python -m backend.app.ai_model.random_forest.predict
```
The `predict.py` module exposes a `predict(features: dict)` function that returns a JSON-serializable dictionary with the prediction label and probability.

### Testing
```bash
python -m backend.app.ai_model.random_forest.test
```
