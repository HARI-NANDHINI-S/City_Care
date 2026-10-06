# Priority Dataset Acquisition & Mapping Guide

This document defines the requirements for obtaining a legitimate Municipal Road Maintenance dataset and transforming it into the exact schema required by CivicVision AI.

## Required Features & Mapping Strategy

| Required Feature | Required Meaning | Expected Type | Possible Legitimate Source | Transformation Needed |
| :--- | :--- | :--- | :--- | :--- |
| `issue_count` | Number of issues reported for a road segment | Integer | 311 Service Requests / Open Data NI | Aggregate historical requests by segment or coordinate radius. |
| `damage_area` | Affected physical area in sq. meters | Float | Visual inspection logs / Contractor reports | Usually must be estimated or joined from specific inspection datasets. |
| `detection_confidence` | AI bounding box confidence | Float | CivicVision AI Pipeline (YOLO) | This is dynamically generated at inference, but for training, use historical YOLO validation scores or synthesize *only* this pipeline metric safely. |
| `severity` | Base physical severity (1-4) | Integer | 311 Service Requests (e.g. "Pothole" vs "Crack") | Map text classifications (e.g., Pothole = 4, Crack = 2). |
| `road_age_years` | Years since last total resurfacing | Float | Department of Transportation (DOT) Paving Schedules | Subtract "Last Paved Year" from current year. |
| `road_condition` | Normalized metric representing overall wear | Float (0.0 - 1.0) | Pavement Condition Index (PCI) datasets | Normalize PCI (0-100) to 0.0-1.0. |
| `traffic_volume` | Average vehicles per day (AADT) | Integer | DOT Traffic Count Datasets | Spatial join AADT counts to the road segment. |
| `accident_history` | Number of accidents in past year | Integer | Police/Traffic collision open datasets | Count collisions within X meters of the road segment in the last 12 months. |
| `nearby_school` | Within school zone (Yes/No) | Binary (1/0) | City Zoning / Points of Interest (POI) | Spatial join: 1 if within 200 meters of a school. |
| `nearby_hospital` | Within hospital/emergency route | Binary (1/0) | Emergency Routes / POI datasets | Spatial join: 1 if within 500 meters or on designated route. |
| `drainage_condition` | Drainage rating (Poor/Fair/Good) | Categorical (1-3) | Stormwater / Public Works asset condition | Map text ratings to integers (1=Poor, 2=Fair, 3=Good). |
| `days_since_maintenance` | Days since last minor/major repair | Integer | Public Works Work Orders | DateDiff between current date and last completed work order date. |
| `priority_class` | Target Variable (Low/Med/High/Crit) | Integer (1-4) | Maintenance completion timeframes | Define methodology: e.g., if fixed in < 48 hours = 4. If fixed in > 30 days = 1. Must be clearly documented. |

## Source Analysis

No single public dataset contains all of these features. Legitimate sources include:
- **San Diego Open Data**: Excellent for 311 requests and Pavement Condition Index (PCI).
- **Open Data NI**: Good for general road network and traffic data.
- **OpenStreetMap (OSM)**: Can provide the spatial context for `nearby_school` and `nearby_hospital`.

**Strategy**: You will likely need to perform a geospatial join (e.g., using QGIS or Python `geopandas`) to merge a 311/Pothole dataset with a Traffic (AADT) dataset and a Zoning (Schools/Hospitals) dataset to produce the final `actual_dataset.csv`.
