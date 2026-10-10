# International Road Condition Dataset — Search & Acquisition Report

## Executive Summary
After confirming the unavailability of genuine, downloadable, tabular Indian road condition datasets, the search expanded to international sources. We focused on highly mature open data portals (San Francisco, San Diego, New York City) to locate a suitable tabular dataset that could support Random Forest, Decision Tree, Logistic Regression, and Gradient Boosting models.

**Result**: We successfully acquired the **San Francisco Pavement Condition Index (PCI) Scores** dataset (19,461 rows). However, upon inspection, it **lacks the required predictive features** to properly support the predictive models without fabricating thresholds.

---

## Sources Checked

### 1. San Francisco Open Data (DataSF)
*   **Dataset**: Streets Data - Pavement Condition Index (PCI) Scores
*   **ID**: `5aye-4rtt`
*   **Status**: **DOWNLOADED** (`raw/sf_pavement_condition.csv`)
*   **Limitation**: The dataset contains the valid target variable (`PCI_Score`), but its features are strictly limited to geographical location (Latitude, Longitude), ID (CNN), Neighborhood, and Street names. It completely lacks the rich structural predictors necessary to make a meaningful predictive ML model (e.g., Average Annual Daily Traffic [AADT], Rutting, Cracking, IRI, Rainfall, Pavement Age). Building models on this dataset would result in models memorizing spatial coordinates rather than learning structural deterioration patterns.

### 2. San Diego Open Data
*   **Dataset**: Pavement Condition Assessments
*   **Status**: **REJECTED**
*   **Reason**: The direct API endpoint returned a 404 Not Found error during the automated fetch attempt. The schema was evaluated, but it suffers from the same feature sparsity as the SF dataset (primarily location and final score, lacking upstream physical metrics).

### 3. New York City Open Data
*   **Dataset**: Street Pavement Rating
*   **ID**: `2cav-chmn`
*   **Status**: **REJECTED**
*   **Reason**: The view ID `2cav-chmn` returned a `not_found` error, indicating either a restricted dataset, a changed API endpoint, or an authentication requirement.

### 4. Mendeley Data & Academic Repositories
*   **Dataset**: Pavement Condition Index (PCI) Data for 5271 Urban Roads (León, Mexico)
*   **Status**: **REJECTED**
*   **Reason**: Academic repositories like Mendeley often embed their CSV datasets inside complex ZIP archives requiring JavaScript or authenticated downloads, preventing automated programmatic acquisition without bypassing security controls.

---

## Blockers and Final Verdict
*   **Unsatisfied Requirement**: Random Forest, Decision Tree, Logistic Regression, and Gradient Boosting models remain **BLOCKED** (`DATASET_NOT_READY`).
*   **Why**: The only successfully downloaded dataset (SF PCI) contains the target variable but lacks the features (predictors) required to train valid models. The prompt explicitly forbids fabricating maintenance labels or deploying models on completely unsupported datasets.
*   **Completed Workarounds**: The backend endpoints (`/api/v1/ml/lab/datasets` and `/api/v1/ml/lab/models`) and the React frontend Model Lab UI have been fully built. The UI correctly displays the acquired datasets, their severe limitations, and correctly marks the downstream tabular models as blocked awaiting data procurement. 
*   **Next Steps**: A fully featured PMS (Pavement Management System) database export must be acquired either through a formal academic data sharing agreement, an RTI request to the NHAI, or a paid vendor API.
