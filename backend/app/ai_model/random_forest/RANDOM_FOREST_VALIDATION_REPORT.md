# Random Forest Maintenance Prediction — Validation Report

## Executive Summary
This report details the audit, validation, and testing of the Random Forest model located at `backend/app/ai_model/random_forest/weights/random_forest.joblib`.

**Final Classification:** VALIDATED AS A RULE-REPRODUCTION BASELINE (NOT VALID FOR REAL-WORLD PREDICTION)

The model is functionally robust, loads correctly, and handles missing/invalid features safely. However, the evaluation metrics (Accuracy ~1.0) are the result of target leakage. The `Needs Maintenance` labels in the training dataset are synthetically generated using hardcoded rules rather than observed municipal data. The model is currently reproducing a heuristic formula rather than learning real-world pavement degradation.

---

## Phase 1: Dataset Audit
*   **Dataset File**: `datasets/priority/ESC 12 Pavement Dataset.csv`
*   **Size**: 1,050,000+ rows.
*   **Features**: `PCI`, `AADT`, `Last Maintenance`, `Average Rainfall`, `Rutting`, `IRI`, `Road Type`, `Asphalt Type`.
*   **Target**: `Needs Maintenance`.
*   **Leakage/Rule Identification**:
    A decision tree audit of the dataset revealed that `Needs Maintenance` is deterministically derived from combinations of input thresholds. For instance:
    *   If `Rutting > 16.94`, `PCI <= 73.41`, and `Last Maintenance <= 2021`, the class is consistently `1`.
    *   If `Rutting <= 16.94`, `PCI > 34.73`, `Average Rainfall <= 80.49`, and `Last Maintenance > 2012`, the class is consistently `0`.
*   **Conclusion**: The dataset represents synthetic/rule-generated labels, explicitly warned against in `DATA_SOURCE.md`.

---

## Phase 2: Pipeline Audit
*   **Data Splitting**: `train.py` correctly implements a 20% holdout split using `stratify=y`.
*   **Preprocessing**: `ColumnTransformer` handles scaling and `OneHotEncoder` safely maps categorical features without label leaking into the features directly.
*   **Metrics**: The 99.999% Accuracy, 1.0 Precision, and 0.999 Recall are correctly calculated from the holdout test set. However, these metrics reflect the model's ability to reverse-engineer the synthetic generation script, not its real-world predictive power.

---

## Phase 3 & 4: Evaluation & Retraining Justification
*   **Evaluation**: The model achieves near-perfect cross-validation on the test set strictly because the dataset features have no real-world noise overriding the synthetic target rules. Top features are `Rutting` (36.6%), `PCI` (22.1%), and `Average Rainfall` (18.1%).
*   **Retraining**: **NOT JUSTIFIED**. Retraining on the existing dataset will only produce an identical rule-reproducing artifact. A genuine municipal dataset with true target observations is required before retraining can yield a production-ready model. The original artifact is preserved.

---

## Phase 5: Model Artifact Testing
The existing model artifact was tested directly via Python API (`predict()`) bypassing HTTP integration:
1.  **Artifact Loading**: Successfully loaded via `joblib`.
2.  **Valid Predictions**: Successfully classified valid numeric inputs (e.g., `PCI: 65, Rutting: 5.2`) and returned probabilities.
3.  **Missing/Invalid Features**: The preprocessing pipeline successfully aborted and returned a structured error when required features (e.g., `PCI`) were missing or when numeric fields were fed string types, preventing runtime crashes.

---

## Remaining Limitations & Blockers
**BLOCKED FOR LIVE INTEGRATION**
The Random Forest model cannot be integrated into live prediction workflows until:
1.  An official municipal priority dataset containing non-synthetic maintenance targets is acquired.
2.  The model is retrained on the real-world dataset.
3.  The database schema is expanded to collect and store the required road-context variables (`PCI`, `Rutting`, `AADT`) for incoming civic issues.
