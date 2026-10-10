# Indian Road Condition Dataset — Search & Acquisition Report

## Executive Summary
An exhaustive search was conducted to locate and download a genuine, non-synthetic, India-specific tabular dataset suitable for pavement maintenance modeling (Random Forest, Decision Tree, Logistic Regression, Gradient Boosting). 

**Result**: **No suitable public tabular dataset is currently available for direct download.** Open data portals currently lack this specific data, and academic datasets are trapped behind publisher paywalls or require direct author authorization.

---

## Sources Checked

### 1. Indian Open Government Data (OGD) Portal
*   **URL Checked**: [https://up.data.gov.in/dataset-group-name/Roads](https://up.data.gov.in/dataset-group-name/Roads)
*   **Access Condition**: Open / Public
*   **Status**: **REJECTED**
*   **Reason**: The dataset group page serves as a category placeholder but currently hosts no downloadable CSV payloads containing specific road segment deterioration metrics, pavement condition indices (PCI), or maintenance logs.

### 2. Patiala Pavement Deterioration Research (Wiley)
*   **URL Checked**: [https://onlinelibrary.wiley.com/doi/10.1155/2018/1253108](https://onlinelibrary.wiley.com/doi/10.1155/2018/1253108)
*   **Access Condition**: Restricted / Publisher Paywall (HTTP 403 Forbidden)
*   **Status**: **REJECTED**
*   **Reason**: Access to the underlying supplementary tabular dataset requires institutional credentials or purchasing the article. Per project constraints, bypassing access controls is strictly prohibited. The dataset requires a direct request to the authors for the raw CSV.

### 3. Andhra Pradesh Pavement-Condition Research (ASCE)
*   **URL Checked**: [https://doi.org/10.1061/JPEODX.PVENG-1359](https://doi.org/10.1061/JPEODX.PVENG-1359)
*   **Access Condition**: Restricted / Publisher Paywall (HTTP 403 Forbidden)
*   **Status**: **REJECTED**
*   **Reason**: Similar to the Wiley publication, the ASCE repository strictly restricts automated or unauthorized access. The raw experimental metrics and structural evaluations are paywalled. 

### 4. General Open Web & Academic Repositories (Mendeley, GitHub, Kaggle)
*   **Access Condition**: Open
*   **Status**: **REJECTED**
*   **Reason**: Web searches successfully returned numerous Indian pavement datasets (e.g., PaveDistress), but these are exclusively **image-based datasets** used for computer vision tasks (like YOLO). Tabular numerical datasets (time-series deterioration, traffic volume, historical maintenance routing) are tightly guarded by state Public Works Departments (PWDs) or the National Highways Authority of India (NHAI) and are not published openly as CSVs.

---

## Blockers and Limitations
*   **Tabular vs. Image Data**: While image datasets for pavement distress are plentiful globally, tabular Pavement Management System (PMS) data (like PCI, IRI, AADT) is proprietary municipal data.
*   **Constraint Enforcement**: Generating synthetic rows or fabricating missing values to force the existing synthetic pipeline to work is strictly forbidden under the project requirements. Therefore, no fallback datasets were deployed.

---

## Next Realistic Options
To proceed with the civic tabular ML models (Random Forest, Decision Tree, Logistic Regression, Gradient Boosting), one of the following manual interventions is required:

1.  **Direct Academic Request**: Draft an email to the corresponding authors of the Patiala or Andhra Pradesh studies requesting permission to use their supplementary tabular CSVs for an open-source civic project.
2.  **Right to Information (RTI) Request**: File a formal data request with the local state PWD or NHAI asking for anonymized road segment condition and maintenance histories.
3.  **Halt Tabular ML**: Acknowledge that predicting maintenance needs purely via tabular data is unfeasible for this startup stage, and pivot entirely to the YOLO computer vision pipeline (which evaluates visible damage rather than structural deterioration histories).
