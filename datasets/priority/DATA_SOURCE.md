# Priority Dataset Data Source Manifest

## Status
**NO SUITABLE PRIORITY-LABELLED DATASET FOUND IN LOCAL REPOSITORY**

## Provenance Audit
- **Local Directory:** `datasets/priority/`
- **Current Files:** `priority_dataset_template.csv` (Template header only)
- **Synthetic Data Generation:** Disabled for production ML.
- **Model Training Status:** Blocked until a genuine municipal priority dataset is acquired.

## Criteria for Future Dataset Inclusion
Any future dataset placed in `datasets/priority/priority_dataset.csv` must meet the following criteria:
1. Must originate from an official municipal or public open-data authority.
2. Must contain ground-truth priority classifications (Low=1, Medium=2, High=3, Critical=4) or an officially documented mapping from repair SLA timeframes.
3. Must not use synthetic or randomly generated feature vectors.
4. Any spatial joins (e.g. traffic volume or school proximity) must be computed using true GPS coordinates via verifiable GIS tools (e.g., GeoPandas/QGIS).
