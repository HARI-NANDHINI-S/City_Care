# CivicVision AI — Dataset Validation, Model Readiness & End-to-End Verification

## 1. Actual Datasets Downloaded and Verified

### San Francisco Pavement Condition Index (SF PCI)
- **Status**: Verified and Marked **INCOMPATIBLE**
- **Row Count**: 19,461
- **Columns**: 20
- **Target**: `PCI_Score` (0-100)
- **Reason for Rejection**: As confirmed by manual inspection of the downloaded CSV, this dataset provides the `PCI_Score` but **strictly lacks the structural inputs** (IRI, Rutting, DMI) required for legitimate engineering prediction. Predicting PCI purely from spatial inputs (e.g. `Neighborhoods`, `Latitude`, `Longitude`) would force the model to memorize geography rather than learn physical deterioration patterns. The `Treatment_or_Survey` column was also identified as highly leaky (always correlates with PCI=100 for treatments). Thus, this dataset was correctly marked INCOMPATIBLE to prevent unscientific ML behavior.

### Ontario Pavement Condition for Provincial Highways (2023)
- **Status**: Downloaded, Verified, and Marked **READY**
- **Source**: Ontario Data Catalogue
- **URL**: [Direct Download](https://data.ontario.ca/dataset/01dfc06c-6ef0-4fd0-a010-8ba20e3c9d10/resource/3ebf51cf-f457-4a17-a297-2d9fe01c5dbe/download/2023_opendata.csv)
- **Data Dictionary**: [Dictionary DOCX](https://data.ontario.ca/dataset/01dfc06c-6ef0-4fd0-a010-8ba20e3c9d10/resource/6875fad4-cbec-4d8a-827b-a17df9f5d60b/download/pavement_condition_data_dictionary.docx)
- **License**: Open Government Licence - Ontario
- **Local Path**: `datasets/priority/international_road_condition/raw/ontario_2023_pavement.csv`
- **Row Count**: 1,890 valid rows.
- **Key Columns**: `PCI`, `DMI`, `IRI`, `Pave_Type`, `FUNC_CLASS`
- **Data Quality & Anomalies**:
  - `SectionID`: Blank in all 1,890 rows. The reason for the blank column is currently **unknown**, as we cannot conclusively verify the discontinuation of LHRS IDs against official documentation at this moment.
  - **Overlaps & Duplicates**: There are 29 pairs of duplicate Highway-Direction-Distance keys and 78 overlapping intervals. Because explicit lane identity fields are absent, these must be classified as **unresolved repeated/overlapping intervals**. They will be preserved without fabricating identifiers or deleting rows, but they represent a data quality limitation.
  - **PCI Methodology & Leakage**: PCI is a mathematically composite index officially calculated from physical surface distresses (DMI) and roughness (IRI). The observed correlations (PCI–DMI +0.919, PCI–IRI −0.645) are a direct consequence of this mathematical formula, not merely empirical correlations. Therefore, using DMI or IRI to predict PCI would constitute explicit, severe **target leakage**.
- **Reason for Acceptance**: Since Indian open data portals strictly do not publish raw CSV files containing physical road surface indices, this Canadian dataset provides an excellent international fallback. It contains genuine physical condition measurements alongside material types and functional classes, enabling non-leaky tabular prediction tasks.

## 2. Audit of the Four Proposed Model Tasks

We investigated the four tasks to ensure they are mathematically sound, free of target leakage, and scientifically meaningful for the CivicVision AI context. We specify exactly one valid modeling objective for the two accepted models.

| Model | Target | Task Type | Validity & Evidence | Status |
|-------|--------|-----------|----------------------|--------|
| **Random Forest** | `IRI` | Regression | **Valid.** Predicting unobservable roughness (IRI) from visual distress manifestations (DMI) and road properties (`Pave_Type`, `FUNC_CLASS`). **Use Case:** Roughness profiling requires expensive laser vans, while DMI can be estimated via standard cameras (e.g., CivicVision YOLO). This model allows cities to estimate IRI purely from visual inputs available at prediction time. | **READY_FOR_MANUAL_TRAINING** |
| **Decision Tree** | `IRI` | Regression | **Valid.** Solves the identical prediction task as the Random Forest to establish an interpretable baseline model. | **READY_FOR_MANUAL_TRAINING** |
| **Logistic Regression** | `Pave_Type` | Classification | **Invalid Task.** Predicting whether a road is Asphalt or Concrete based on its deterioration pattern is an artificial academic exercise. Cities already know their pavement materials. It has no utility for *CivicVision AI's maintenance prediction goal*. | **BLOCKED** |
| **Gradient Boosting** | `PCI` | Regression | **Invalid Task.** Because PCI is mathematically derived from DMI and IRI, we must exclude them to prevent direct leakage. Attempting to predict PCI using only the remaining features (`Pave_Type`, `FUNC_CLASS`, `DIR`, `Segment_Length`) means predicting structural deterioration entirely from static administrative properties without any Traffic (AADT) or Age variables. The model would merely memorize the mean PCI for a road class. | **BLOCKED** |

## 3. Validation Strategy and Splitting Limitations

Because the dataset contains 78 unresolved overlapping intervals and 29 duplicate coordinate keys on the same highways, a random train/test split will cause spatial target leakage. 

- **Proposed Safeguard**: A `GroupShuffleSplit` on the `Highway` column is recommended. This groups all identical highways (and their unresolved overlaps) into either the train or test set, preventing fragments of the same road from appearing in both.
- **Unresolved Limitation**: While this mitigates leakage at the highway level, it does not guarantee that all spatial leakage is completely eliminated. Without distinct physical lane identifiers, the unresolved overlapping intervals remain a data quality limitation that cannot be perfectly handled.

## 4. Handling Model-to-Model Dependencies

- The previously envisioned "Civic Prioritization Score" downstream model remains explicitly **BLOCKED**.
- **Reason**: Synthetic prioritization data cannot be safely generated until real upstream tabular models are fully trained and integrated. Inventing downstream synthetic labels now without genuine upstream outputs would introduce silent dependency leakage into the project.

## 4. Tests and Verification (Without Training)

- **Dataset Schema Validation**: The Ontario CSV headers, row count (1,890), and data types were successfully verified via pandas analysis without executing any ML `.fit()` methods. No duplicate rows were found, and the dataset is a single cross-section (2023), eliminating longitudinal leakage.
- **Backend Startup**: The backend successfully hot-reloaded the `ml.py` updates, which correctly mark two tasks as READY and two as BLOCKED_INVALID_TASK.
- **Frontend Integration**: The Model Intelligence Lab dynamically consumes these accurate statuses. Invalid tasks now display specific blockers rather than a misleading `READY` status.
- **YOLO Status**: The YOLOv8 model artifacts, inference scripts, and class mappings were strictly protected and untouched.

## 5. Final Conclusion and Next Steps

The application is completely integrated without fabricating results. You are unblocked to manually train the Random Forest and Decision Tree models using `ontario_2023_pavement.csv`. 

For Logistic Regression and Gradient Boosting, do not proceed with training until a dataset is obtained that genuinely supports classification of a *maintenance category* and provides *traffic/age features* for overall PCI deterioration.
