# AEON 7080

AEON 7080 is a laptop-first computational laboratory for learning, simulation, and reproducible analysis.

It is not a medical device, a diagnostic system, or a source of medical advice. Simulated output is labeled:

> SIMULATION RESULT — NOT CLINICAL EVIDENCE, DIAGNOSIS, OR MEDICAL ADVICE.

## What this build actually runs

- Synthetic virtual patients from a seeded generator
- Oral and IV pharmacokinetic models, including analytical checks
- An illustrative indirect glucose response and cardiovascular / respiratory bookkeeping
- Abstract SIR and SEIR models
- Monte Carlo parameter uncertainty and one-at-a-time sensitivity
- A synthetic ECG and a logistic model trained only on synthetic morphology classes
- An AI Scientist that plans with allowlisted tools and reports solver output
- A scientific critic that flags problems and does not rewrite parameters
- CSV / TSV / JSON upload, profiling, confirmed mapping, and computed table questions
- Academy videos with chapters, captions, and transcripts
- Experiment storage, reports, and replay

Drug discovery, genomics, imaging, clinical-trial simulation, nutrition, aging, and foundation-model training are extension points. They do not emit fabricated scores.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=.:apps/api uvicorn aeon_api.main:app --port 8000
```

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000. The workstation signs into the demo workspace (`demo@aeon7080.local` / `demo`).

```bash
PYTHONPATH=.:apps/api pytest
cd apps/web && npm test
```

PostgreSQL and Redis are described in `docker/docker-compose.yml`. Local development uses SQLite under `storage/` so the laboratory runs without those services. Celery is not wired; simulations run in the API process.

## Layout

See `docs/ARCHITECTURE.md`.
