# CivicVision AI — Tabular ML Integration Plan

## 1. DMI Mapping (Distress Manifestation Index)

### Current State
The existing CivicVision YOLO pipeline outputs object detection bounding boxes, confidence scores, and categorized distress classes (e.g., longitudinal cracks, potholes). It outputs a coarse categorical severity (e.g., "High", "Low"). The Ontario tabular models require a continuous `DMI` score (a 0-10 engineering index).

### Resolution Plan
- **Limitation:** It is scientifically invalid to directly equate YOLO bounding-box counts, categorical severities, or confidence scores to an engineering DMI score without a calibrated mathematical formula.
- **Validation Requirement:** A mapping layer cannot be guessed or fabricated. To safely use YOLO for DMI input, we must either:
  1. Procure a paired dataset containing both street-level images and official DMI ratings to train a mapping regression model.
  2. Adopt a documented pavement engineering formula (e.g., ASTM D6433) that computes a score based on the specific density and severity of the bounding boxes, provided the YOLO classes directly align with the formula's distress types.
- **Current Block:** Until this mapping is scientifically validated, live DMI estimation from user photos is unsupported.

## 2. Pavement Type (`Pave_Type`)

### Current State
The application receives GPS coordinates (`latitude`, `longitude`) but no pavement material data. The models require `Pave_Type` (e.g., Asphalt Concrete, Portland Cement Concrete).

### Resolution Plan
- **Citizen Input:** We will *not* ask citizens to input pavement type. The general public cannot reliably distinguish between asphalt types, concrete, and surface treatments, leading to high garbage-in rates.
- **GIS Sources:** OpenStreetMap (OSM) contains a `surface=*` tag (e.g., `surface=asphalt`, `surface=concrete`). However, in the target deployment region (Tamil Nadu), surface tags are extremely sparse.
- **Authoritative Sources:** We must investigate integration with municipal asset management databases or the NHAI (National Highways Authority of India) GIS portal.
- **Current Block:** If an authoritative API is unavailable or the OSM surface tag is missing for a coordinate, the `Pave_Type` feature is irretrievable.

## 3. Functional Class (`FUNC_CLASS`)

### Current State
The models require the functional class of the road (e.g., Freeway, Arterial, Collector, Local). 

### Resolution Plan
- **GIS Sources:** The OpenStreetMap `highway=*` tag (e.g., `motorway`, `primary`, `secondary`, `residential`) is generally well-populated worldwide.
- **Mapping Strategy:** It is conceptually defensible to map OSM tags to Ontario classes (e.g., `highway=motorway` -> `FWY`; `highway=primary/secondary` -> `ART`; `highway=residential` -> `LOC`).
- **Limitations:** 
  1. **GPS Snapping:** User smartphone GPS has significant drift (often 10-30 meters). Snapping a coordinate to the correct OSM way (especially near intersections or parallel service roads) introduces mismatch errors.
  2. **Definition Drift:** An Ontario "Arterial" road does not experience the exact same traffic loading characteristics as a Tamil Nadu "Primary" road.

## 4. Missing-Data and Fallback Behavior

Because we cannot guarantee that every coordinate will resolve to a known road, or that YOLO can accurately map to DMI, explicit fail-safes are required.

- **No Fabrication:** We will never silently inject default values (e.g., assuming "Asphalt" or "Local" road) when a lookup fails. We will not fabricate DMI values from unmapped YOLO severities.
- **Graceful Degradation:** If `Pave_Type`, `FUNC_CLASS`, or `DMI` cannot be definitively established for an incoming report, the Tabular IRI Prediction workflow is **aborted**.
- **System Preservation:** The existing CivicVision YOLO workflow (AI object detection, category routing, priority scoring based on visual severity) operates independently. It will continue to function normally, log the issue, and alert officers, even if the tabular unobservable-roughness prediction is skipped.

## 5. Model Validity and Generalization

- **Evaluation Context:** The reported MAE, RMSE, and R² metrics were achieved strictly on a held-out split of Ontario, Canada highways. 
- **Domain Shift:** Road construction materials, base layers, subgrades, and climate (freeze-thaw cycles vs. tropical monsoons) in Ontario differ vastly from Tamil Nadu. We **do not claim** that the Ontario-trained weights will accurately predict physical roughness in India.
- **Camera-Only Prediction:** We **do not claim** that the system currently supports camera-only IRI prediction. 
- **Deployment Criteria:** Before these tabular models can be activated in production, we require:
  1. A validated YOLO-to-DMI mathematical translation.
  2. A reliable geospatial coordinate-matching API for administrative features.
  3. A pilot recalibration study using local Indian ground-truth IRI data to assess domain generalization.
