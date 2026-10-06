# CivicVision AI — Architecture & Technical Reference

## System Architecture

CivicVision AI is engineered using a decoupled modern web architecture separating the React + TypeScript frontend from the FastAPI Python backend and computer vision pipeline.

```
                               ┌───────────────────────────────────────────────┐
                               │           REACT + VITE FRONTEND (TSX)         │
                               │   - React Leaflet, Tailwind CSS, Lucide       │
                               └───────────────────────┬───────────────────────┘
                                                       │ REST API (JSON / Multipart)
                                                       ▼
                               ┌───────────────────────────────────────────────┐
                               │               FASTAPI BACKEND                 │
                               │   - OAuth2 / JWT Auth (PBKDF2-SHA256)         │
                               │   - SQLAlchemy ORM & Pydantic Validation     │
                               └───────────────┬───────────────┬───────────────┘
                                               │               │
                               ┌───────────────┘               └───────────────┐
                               ▼                                               ▼
   ┌──────────────────────────────────────────────┐         ┌─────────────────────────────────────┐
   │             CV & ENGINE PIPELINE             │         │         RELATIONAL DATABASE         │
   │ - OpenCV Bounding Box Annotator              │         │ - Users, Departments, Issues        │
   │ - YOLO v8 Interface                          │         │ - IssueImages, StatusHistory        │
   │ - Explainable Priority Engine (0-100)         │         │ - DuplicateIssueRelations           │
   │ - Haversine Duplicate Detector (50m, 72h)    │         └─────────────────────────────────────┘
   └──────────────────────────────────────────────┘
```

## Explainable Priority Algorithm

The system prioritizes issues dynamically using a transparent multi-factor mathematical formula:

$$P = \min\left(100, \text{Round}\left( w_{\text{cat}} \cdot S_{\text{cat}} + w_{\text{conf}} \cdot S_{\text{conf}} + w_{\text{area}} \cdot S_{\text{area}} + w_{\text{dup}} \cdot S_{\text{dup}} + w_{\text{age}} \cdot S_{\text{age}} \right)\right)$$

### Priority Thresholds:
- **0–30**: LOW
- **31–60**: MEDIUM
- **61–80**: HIGH
- **81–100**: CRITICAL

---

## Haversine Duplicate Detection Algorithm

When a citizen reports a defect at coordinates $(\text{lat}_1, \text{lng}_1)$ with category $C$:
1. Query unresolved issues with matching category $C$ created within the past $T = 72$ hours.
2. Compute distance $D$ using Haversine formula:
   $$D = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
3. If $D \le 50.0\text{ meters}$, link the report as a duplicate match and increment the original issue priority score.
