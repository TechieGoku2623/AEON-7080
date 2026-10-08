# Architecture

AEON 7080 is a monorepo with a FastAPI service and a Next.js workstation.

```text
apps/api            HTTP, auth, SQLAlchemy models, academy seed
apps/web            Laboratory UI
simulation_engine   Models, solvers, virtual patients, drug-response study
ai_scientist        Planner, allowlisted tools, critic, reports
data                Profiling, quality heuristic, units, mapping, lineage
ml                  Numpy logistic regression; optional PyTorch
```

The AI Scientist does not receive a Python, shell, or database tool. A question becomes a plan. The orchestrator runs at most one cycle and calls computational code. Optional language-model narration is discarded when it introduces numbers that are absent from the evidence.

Heavy numerical work is vectorized with NumPy for the population and Monte Carlo paths. The browser does not integrate the ODEs.

Unimplemented scientific domains are listed by `GET /api/simulations/models` as extension points.
