# CivicVision AI — Model Implementation Audit (Revised)

This report assesses the models based on explicit metrics. Scores are calculated using weights (Wt).

## 1. YOLOv8 (Visual Defect Detection)
**Overall Completion**: **81%** (Calculated: 6.5 / 8.0)
- **Problem Def** (Wt 1): 1.0 (Valid defect detection)
- **Data Quality** (Wt 1): 1.0 (Prepared and trained)
- **Training Script** (Wt 1): 1.0 (Code verified)
- **Actual Training** (Wt 1): 1.0 (`weights/best.pt` exists)
- **Evaluation** (Wt 1): 0.5 (Missing physical Indian context calibration)
- **Artifacts Saved** (Wt 1): 1.0
- **API Integration** (Wt 2): 0.5 (Verified via isolated pytest environment; retains 0.5 score pending real-world validation)

## 2. Random Forest Regressor (Tabular)
**Overall Completion**: **50%** (Calculated: 4.5 / 9.0)
- **Problem Def** (Wt 1): 1.0
- **Data Quality** (Wt 1): 0.5 (Ontario valid, but overlaps unresolved)
- **Training Script** (Wt 1): 1.0 (`train_tabular_models.py` verified)
- **Actual Training** (Wt 1): 1.0 (User reported metrics: R² 0.5289)
- **Evaluation** (Wt 1): 1.0
- **Artifact Saving** (Wt 1): 0.0 (Script explicitly comments out saving; existing `.joblib` files are from deprecated leaky runs)
- **Artifact Loading** (Wt 1): 0.0
- **API Integration** (Wt 2): 0.0 (Endpoint disabled intentionally)

## 3. Decision Tree Regressor (Tabular)
**Overall Completion**: **50%** (Calculated: 4.5 / 9.0)
- **Problem Def** (Wt 1): 1.0
- **Data Quality** (Wt 1): 0.5
- **Training Script** (Wt 1): 1.0
- **Actual Training** (Wt 1): 1.0 (User reported metrics: R² 0.6228)
- **Evaluation** (Wt 1): 1.0
- **Artifact Saving** (Wt 1): 0.0
- **Artifact Loading** (Wt 1): 0.0
- **API Integration** (Wt 2): 0.0 

## 4. Logistic Regression
**Overall Completion**: **0%** (Permanently Blocked)
- **Verified Fact**: Predicting material type from deterioration is an invalid task.

## 5. Gradient Boosting
**Overall Completion**: **0%** (Permanently Blocked)
- **Verified Fact**: Predicting PCI from static inputs without traffic/age induces memorization.

---

## Summaries

| Model | Completion | Training Executed | Artifact Saved | API Integration | Readiness |
|---|---|---|---|---|---|
| YOLOv8 | 81% | 100% | 100% | 50% (Static) | 50% |
| Random Forest | 50% | 100% | 0% | 0% | 10% |
| Decision Tree | 50% | 100% | 0% | 0% | 10% |
| Logistic Reg. | 0% | 0% | 0% | 0% | 0% |
| Gradient Boost | 0% | 0% | 0% | 0% | 0% |
