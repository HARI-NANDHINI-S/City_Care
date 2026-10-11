# CivicVision AI — Remaining Work Roadmap

This document outlines the top prioritized tasks required to advance the CivicVision project from a local prototype to a deployable, real-world application.

## Priority 1: Finalize Tabular Artifacts
- **Task**: Execute the `train_tabular_models.py` script with the artifact-saving commands uncommented.
- **Dependency**: None. (Script and Ontario dataset are already prepared).
- **Completion Criteria**: `.joblib` files are successfully saved to `app/ai_model/random_forest/weights/` and `app/ai_model/decision_tree/weights/`.

## Priority 2: GIS Administrative Feature Resolution
- **Task**: Build a backend service that accepts a GPS coordinate and returns the `Pave_Type` and `FUNC_CLASS` using OpenStreetMap (OSM) or a municipal GIS API.
- **Dependency**: External API access/keys.
- **Completion Criteria**: The API successfully maps coordinates to valid string categories, with graceful fallback logic if the mapping fails.

## Priority 3: YOLO-to-DMI Translation Layer
- **Task**: Develop a mathematical heuristic to translate the categorical severity returned by the YOLO image service into the 0-10 engineering `DMI` scale required by the tabular models.
- **Dependency**: YOLO inference pipeline.
- **Completion Criteria**: Bounding box severity categories map reliably to a `float` DMI value without crashing.

## Priority 4: Tabular API Integration
- **Task**: Connect the `issues.py` endpoint to the saved Random Forest `.joblib` artifact. Feed it the YOLO-derived DMI and GIS-derived Pave_Type/FUNC_CLASS to generate a real-time `IRI` prediction.
- **Dependency**: Priorities 1, 2, and 3.
- **Completion Criteria**: A new issue submission automatically calculates and saves an `IRI` prediction without requiring manual user input for materials or roughness.

## Priority 5: Real-World Tamil Nadu Calibration
- **Task**: Gather a small, localized dataset of Tamil Nadu road imagery and ground-truth IRI/DMI measurements to validate the Ontario-trained tabular weights.
- **Dependency**: Prior tabular integration.
- **Completion Criteria**: Publication of an evaluation report detailing domain-shift accuracy and necessary recalibration steps.

## Priority 6: Production Database Migration
- **Task**: Replace the local SQLite `civicsense.db` with a scalable PostgreSQL instance.
- **Dependency**: Docker/Cloud infrastructure.
- **Completion Criteria**: SQLAlchemy correctly interfaces with the Postgres instance; Alembic migrations run successfully.

## Priority 7: Cloud Storage Integration
- **Task**: Modify the `issues.py` image upload logic to push original and annotated images to an S3-compatible cloud bucket rather than the local filesystem.
- **Dependency**: AWS/S3 credentials.
- **Completion Criteria**: Image URLs resolve to public cloud links instead of local `/uploads/` paths.

## Priority 8: Deployment and CI/CD
- **Task**: Containerize the FastAPI backend and React frontend. Establish GitHub Actions (or similar) for automated testing and deployment.
- **Dependency**: Priorities 6 and 7.
- **Completion Criteria**: The application is accessible securely over HTTPS on a production domain.
