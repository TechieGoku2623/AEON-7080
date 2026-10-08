# API

Authentication is a bearer token from `POST /api/auth/login`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Name and version |
| GET | `/api/simulations/models` | Implemented models and extension points |
| POST | `/api/simulations/run` | Run one registered model |
| POST | `/api/patients/generate` | Synthetic patient |
| POST | `/api/populations/generate` | Synthetic population summary |
| POST | `/api/experiments` | Store a configuration |
| POST | `/api/experiments/{id}/run` | Execute the drug-response study |
| POST | `/api/experiments/{id}/replay` | Re-execute and compare endpoints |
| GET | `/api/experiments/compare?ids=` | Side-by-side stored endpoints |
| POST | `/api/ai/plan` | Planner only |
| POST | `/api/ai/execute` | Plan and one tool cycle |
| POST | `/api/data/upload` | Table upload |
| POST | `/api/data/{id}/profile` | Recompute profile |
| POST | `/api/data/{id}/map` | Confirmed mapping |
| POST | `/api/data/{id}/analyze` | Computed table question |
| POST | `/api/ml/train` | Synthetic morphology model |
| GET | `/api/academy/videos` | Lesson catalog |
| POST | `/api/reports/generate` | Store the report markdown |

Errors use HTTP 400 for bad parameters, 401 for auth, 404 for unknown records, and 409 when a mapping is unconfirmed or a sensitive table is not acknowledged.
