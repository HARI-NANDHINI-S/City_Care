# CivicVision AI — Tabular ML Training Results

## 1. Experimental Run Summary

The manual training and evaluation for the Random Forest and Decision Tree regression models were executed on the Ontario 2023 pavement dataset.

**Dataset Configuration:**
- Total valid rows: 1,890 (0 dropped)
- Splitting Strategy: `GroupShuffleSplit` (grouped by `Highway`)
- Train set: 1,396 rows
- Test set: 494 rows
- Target: `IRI` (International Roughness Index)
- Features: `DMI` (Distress Manifestation Index), `Pave_Type`, `FUNC_CLASS`

**Evaluation Metrics:**

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| DummyRegressor baseline | 0.5574 | 0.7192 | -0.0228 |
| Decision Tree | 0.3050 | 0.4368 | 0.6228 |
| Random Forest | 0.3445 | 0.4881 | 0.5289 |

### Metric Analysis
- Both models successfully outperformed the naive baseline (R² < 0), indicating that DMI, Pave_Type, and FUNC_CLASS contain genuine predictive signal for estimating IRI.
- **Decision Tree (R² 0.6228)** performed better than Random Forest (R² 0.5289) in this specific run. This indicates that a simpler tree model (likely constrained to `max_depth=5`) successfully generalized to the test set without overfitting, whereas the Random Forest may require hyperparameter tuning. 
- *Note*: These results prove the technical feasibility of the prediction task. They **do not** claim universal superiority of the Decision Tree or signify that the models are ready for production deployment.

## 2. Limitations

1. **Domain Generalization:** The models were trained exclusively on Ontario, Canada road data. Generalizing these numeric deterioration curves to Tamil Nadu, India, requires substantial validation and likely recalibration due to different weather patterns and road construction standards.
2. **Spatial Overlap Vulnerability:** The `GroupShuffleSplit` verified 0 highway overlaps between train and test sets. However, unresolved parallel lanes and overlapping continuous intervals exist in the raw data, meaning total elimination of geographic correlation cannot be guaranteed.
3. **DMI Definition:** The dataset's `DMI` input represents an official structural engineering assessment (0-10 scale). It is **not automatically equivalent** to the "severity" confidence output by CivicVision's YOLO pipeline. 

## 3. Pre-Integration Audit (API Input Availability)

A static inspection of the current live backend (`app.api.v1.endpoints.issues.py` and `Issue` models) reveals critical gaps between what the tabular models require and what the application currently provides:

| Required Input | Current API Availability | Resolution Required |
|---|---|---|
| `DMI` | **Missing.** API only provides `severity` and `ai_confidence` from YOLO. | A mathematical or heuristic mapping function must be developed to translate YOLO damage severities into the 0-10 DMI scale. |
| `Pave_Type` | **Missing.** | The application does not collect pavement material type. This must either be asked of the user during reporting or fetched from a municipal GIS database using the report's `latitude`/`longitude`. |
| `FUNC_CLASS`| **Missing.** | The application does not collect highway functional class. This must be fetched via a GIS API (e.g., OpenStreetMap) using the report's coordinates. |

## 4. Recommended Validation Steps Before Integration

Before proceeding to Step 4 (Model Integration), the following blockers must be resolved:

1. **Feature Engineering / GIS Integration:** Implement backend logic to derive `Pave_Type` and `FUNC_CLASS` from user-reported GPS coordinates.
2. **DMI Mapping:** Establish and test a mapping layer that reliably converts YOLO bounding-box detections into the Ontario `DMI` scale expected by the tabular models.
3. **Robustness Checks:** Evaluate the models' behavior when default or "Unknown" values are passed for `Pave_Type` or `FUNC_CLASS` in the event of GIS lookup failures.
