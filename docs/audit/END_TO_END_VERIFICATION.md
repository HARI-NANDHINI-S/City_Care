# CivicVision AI — End-to-End Functional Verification

| User Journey | Frontend | API | Backend Logic | Database | Verified? | Missing Work |
|---|---|---|---|---|---|---|
| **User Registration/Login** | Form routes, JWT token storage | `/api/v1/auth/login` | Password hashing, JWT generation | `users` table check | ✅ Yes (Static) | Rate limiting, email verification |
| **Image Upload & Inference** | File input, loading UI | `/api/v1/issues/analyze-image` | Disk storage, YOLO object detection | Local disk, `IssueImage` model | ✅ Yes (Static) | Migration to S3 storage |
| **Issue Creation** | Multi-step form, GPS integration | `POST /api/v1/issues` | Priority calc, Department routing | `issues` table insert | ✅ Yes (Static) | GIS validation of coordinates |
| **Map & Issue Retrieval** | Mapbox/Leaflet rendering | `GET /api/v1/issues/map-data` | Filter queries | SELECT from `issues` | ✅ Yes (Static) | Pagination for large data |
| **Issue Status Updates** | Admin/Officer action buttons | `PATCH /api/v1/issues/{id}` | Status transitions, RBAC checks | `issue_status_history` insert | ✅ Yes (Static) | WebSocket/Push notifications |
| **Tabular ML Prediction** | Disabled in UI | `/api/v1/ml/lab/models` | Hardcoded status returns | None | ❌ NOT VERIFIED | Requires GIS feature lookup and DMI mapping integration |

*Verification Methodology: These workflows were verified via static code inspection of the frontend React components (`src/pages/*`) and the backend FastAPI routers (`app/api/v1/endpoints/*`). Destructive runtime tests were purposefully avoided to protect existing databases.*
