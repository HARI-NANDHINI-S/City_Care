# Logistic Regression Maintenance Prediction — Validation Report

## Executive Summary
This report details the implementation, training, testing, and validation of the Logistic Regression model located at `backend/app/ai_model/logistic_regression/weights/logistic_regression.joblib`.

**Final Classification:** VALIDATED AS A SYNTHETIC RULE-REPRODUCTION BASELINE (NOT VALID FOR REAL-WORLD PREDICTION)

The Logistic Regression model effectively reproduces the hardcoded synthetic rules present in the `ESC 12 Pavement Dataset.csv` dataset by forming a nearly perfect linear boundary. Because the dataset targets are synthetically derived and not naturally observed, the model's high evaluation metrics do not reflect genuine real-world predictive validity.

---

## Phase 1 & 2: Dataset Limitations Inherited
*   **Dataset File**: `datasets/priority/ESC 12 Pavement Dataset.csv`
*   **Target**: `Needs Maintenance`.
*   **Limitation Confirmed**: Following the Random Forest and Decision Tree audits, it is definitively established that this dataset contains synthetically generated labels. The Logistic Regression model arithmetically reverses this labeling script but cannot be considered generalized to real pavement failure mechanics.

---

## Phase 3 & 4: Pipeline & Training Execution
*   **Data Splitting**: 80% Train (840,000 samples) / 20% Test (210,000 samples) using `stratify=y` and `random_state=42`.
*   **Preprocessing**: 
    *   `StandardScaler` applied to numeric features (`PCI`, `AADT`, `Last Maintenance`, `Average Rainfall`, `Rutting`, `IRI`) to ensure coefficient scale parity.
    *   `OneHotEncoder` applied to categorical features (`Road Type`, `Asphalt Type`).
*   **Hyperparameters**: 
    *   `C`: 1.0 (Standard Regularization)
    *   `max_iter`: 1000
    *   `solver`: lbfgs
*   **Evaluation Metrics (Test Set)**:
    *   Accuracy: 0.9999
    *   Precision: 0.9999
    *   Recall: 1.0000
    *   F1-score: 0.9999
*   **Extracted Coefficients**:
    The model separated the synthetic rules using strong linear weights. The most impactful features (by absolute magnitude) were:
    1.  `Last Maintenance`: -6.24
    2.  `Rutting`: 5.57
    3.  `Asphalt Type_Concrete`: -5.08
    4.  `Asphalt Type_Asphalt`: 4.67
    5.  `PCI`: -3.30

---

## Phase 5: Model Artifact Testing
The model artifact was verified securely via Python API integration tests (`backend/app/ai_model/logistic_regression/test.py`):
1.  **Artifact Loading**: Successfully loaded via `joblib`.
2.  **Valid Predictions**: Correctly processed inputs, extracting probabilities (e.g., predicted `1` with 100% confidence on the test vector).
3.  **Error Handling**: Safely bypassed failures when attributes were missing or mismatched in type.

---

## Remaining Limitations & Blockers
**BLOCKED FOR LIVE INTEGRATION**
The Logistic Regression model, alongside Random Forest and Decision Tree, remains blocked from live deployment due to:
1.  Absolute dependency on the collection of genuine (non-synthetic) municipal target observations.
2.  Database schema incompatibility (real issues lack `PCI`, `AADT`, `Rutting` contexts).
3.  The model is quarantined and returns structured unavailability indicators rather than predicting randomly.
