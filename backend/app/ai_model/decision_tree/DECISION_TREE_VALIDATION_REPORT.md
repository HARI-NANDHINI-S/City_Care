# Decision Tree Maintenance Prediction — Validation Report

## Executive Summary
This report details the implementation, training, testing, and validation of the Decision Tree model located at `backend/app/ai_model/decision_tree/weights/decision_tree.joblib`.

**Final Classification:** VALIDATED AS A SYNTHETIC RULE-REPRODUCTION BASELINE (NOT VALID FOR REAL-WORLD PREDICTION)

The Decision Tree model accurately reproduces the hardcoded synthetic rules present in the `ESC 12 Pavement Dataset.csv` dataset. However, because the dataset targets are synthetically derived and not naturally observed, the model's near-perfect metrics do not represent real-world predictive ability.

---

## Phase 1: Dataset Limitations Inherited
*   **Dataset File**: `datasets/priority/ESC 12 Pavement Dataset.csv`
*   **Target**: `Needs Maintenance`.
*   **Limitation Confirmed**: The Random Forest audit established that this dataset contains synthetically generated labels using deterministic thresholds. The Decision Tree inherits these limitations and serves strictly as an algorithm-reproduction experiment rather than a genuine machine learning model generalizing real-world variance.

---

## Phase 2 & 3: Pipeline & Training Execution
*   **Data Splitting**: 80% Train (840,000 samples) / 20% Test (210,000 samples) using `stratify=y` and `random_state=42`.
*   **Preprocessing**: `ColumnTransformer` with `OneHotEncoder` for categorical features (`Road Type`, `Asphalt Type`) and `passthrough` for numeric features.
*   **Hyperparameters**: 
    *   `max_depth`: 10
    *   `min_samples_split`: 10
    *   `min_samples_leaf`: 4
*   **Evaluation Metrics (Test Set)**:
    *   Accuracy: 0.9990
    *   Precision: 0.9988
    *   Recall: 0.9992
    *   F1-score: 0.9990
*   **Feature Importances**: The single dominant feature extracted by the Decision Tree was `Rutting` (94.4% importance), followed by `PCI` (3.8%), aligning heavily with the synthetic generation script's rule paths identified previously.

---

## Phase 4: Model Artifact Testing
The model artifact was verified directly via Python API (`backend/app/ai_model/decision_tree/test.py`):
1.  **Artifact Loading**: Successfully loaded via `joblib`.
2.  **Valid Predictions**: Successfully classified valid numeric inputs and yielded deterministic prediction states.
3.  **Missing/Invalid Features**: Safely trapped `missing features` exceptions and returned expected string formatting errors when invalid data types were provided.

---

## Remaining Limitations & Blockers
**BLOCKED FOR LIVE PRODUCTION INFERENCE**
The Decision Tree model exhibits the same blockers as the Random Forest model:
1.  It requires an official municipal priority dataset featuring non-synthetic maintenance outcomes.
2.  It requires the backend database schema to be expanded to collect the `PCI`/`Rutting`/`AADT` vectors dynamically.
3.  Until these requirements are fulfilled, the model remains safely quarantined from live prediction endpoints.

## Phase 5: Final Artifact Lifecycle & Input Validation Verification
*   **Target & Task**: Continuous regression on International Roughness Index (`IRI`).
*   **Pipeline Structure**: Verified full pipeline containing `ColumnTransformer` (`StandardScaler` for `DMI`, `OneHotEncoder(handle_unknown='ignore')` for `Pave_Type` & `FUNC_CLASS`) plus `DecisionTreeRegressor`.
*   **Artifact State & Quarantine**: The existing artifact in `weights/decision_tree.joblib` is from the legacy ESC 12 classification experiment. The inference function `is_valid_ontario_artifact()` explicitly validates `target == "IRI"` and rejects synthetic ESC 12 datasets. The live API endpoints honestly report `not_trained` (trained: false).
*   **Atomic Staging & Recovery**: `train_tabular_models.py` uses temporary staging directories and validates deserialization before replacing production weights, preserving `.backup` files to ensure failed runs cannot corrupt weights or metadata.
*   **Isolated Fixture Tests**: Tested without training using an isolated temporary fixture:
    1. Valid types: Output valid prediction.
    2. Missing/Partial attributes: Structured error returned (`Missing features`).
    3. Type mismatch (String in numeric field): Safely trapped `ValueError`.
    4. Unseen categorical values: Handled gracefully without error via `handle_unknown='ignore'`.
    5. Corrupted artifacts: Trapped safely on deserialization.
*   **Production Integrity**: Hashes for `yolo/weights/best.pt`, `civicsense.db`, and existing weights remained bit-for-bit identical before and after testing.

## Manual Training Command
```powershell
cd E:\City_Care\backend
python -m app.ai_model.train_tabular_models --model decision_tree
```

