# Gradient Boosting Maintenance Prediction — Validation Report

## Executive Summary
This report details the implementation, training, testing, and validation of the Gradient Boosting model located at `backend/app/ai_model/gradient_boosting/weights/gradient_boosting.joblib`.

**Final Classification:** VALIDATED AS A SYNTHETIC RULE-REPRODUCTION BASELINE (NOT VALID FOR REAL-WORLD PREDICTION)

The Gradient Boosting model accurately reproduces the hardcoded synthetic rules present in the `ESC 12 Pavement Dataset.csv` dataset, behaving very similarly to the Decision Tree and Random Forest models. Because the dataset targets are synthetically derived and not naturally observed, the model's near-perfect metrics represent heuristic-approximation rather than real-world predictive validity.

---

## Phase 1 & 2: Dataset Limitations Inherited
*   **Dataset File**: `datasets/priority/ESC 12 Pavement Dataset.csv`
*   **Target**: `Needs Maintenance`.
*   **Limitation Confirmed**: Following the previous model audits, it is definitively established that this dataset contains synthetically generated labels. The Gradient Boosting model, therefore, learns to reverse-engineer the generation thresholds, inheriting the identical strict limitation against real-world generalization.

---

## Phase 3 & 4: Pipeline & Training Execution
*   **Data Strategy**: The dataset was randomly downsampled to 100,000 instances to ensure optimal execution time for sequentially-built gradient boosting trees without altering the determinism of the synthetic labels. 
*   **Data Splitting**: 80% Train (80,000 samples) / 20% Test (20,000 samples) using `stratify=y` and `random_state=42`.
*   **Preprocessing**: 
    *   `OneHotEncoder` applied to categorical features (`Road Type`, `Asphalt Type`).
    *   `passthrough` applied to numeric features.
*   **Hyperparameters**: 
    *   `n_estimators`: 100
    *   `learning_rate`: 0.1
    *   `max_depth`: 5
*   **Training Time**: ~29.6 seconds.
*   **Evaluation Metrics (Test Set)**:
    *   Accuracy: 0.9999
    *   Precision: 1.0000
    *   Recall: 0.9998
    *   F1-score: 0.9999
*   **Feature Importances**:
    The model extracted the dominant features identically to the pure Decision Tree:
    1.  `Rutting`: 0.9456
    2.  `PCI`: 0.0397
    3.  `Last Maintenance`: 0.0066

---

## Phase 5: Model Artifact Testing
The model artifact was verified securely via Python API integration tests (`backend/app/ai_model/gradient_boosting/test.py`):
1.  **Artifact Loading**: Successfully loaded via `joblib`.
2.  **Valid Predictions**: Correctly processed inputs, extracting probabilities (e.g., predicted `1` with 99.4% confidence on the test vector).
3.  **Error Handling**: Safely bypassed failures when attributes were missing or mismatched in type (e.g., trapped `"STRING_NOT_FLOAT"` ValueError).

---

## Remaining Limitations & Blockers
**BLOCKED FOR LIVE INTEGRATION**
The Gradient Boosting model remains blocked from live deployment due to:
1.  Dependency on genuine (non-synthetic) municipal target observations.
2.  Database schema incompatibility (real issues lack `PCI`, `AADT`, `Rutting` contexts).
3.  The model is quarantined and returns structured unavailability indicators securely, just like the other baseline models.
