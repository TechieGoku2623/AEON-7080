"""AEON 7080 API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aeon_api.config import SOFTWARE_VERSION
from aeon_api.routers import academy, ai, auth, data_routes, experiments, lab
from aeon_api.seed import seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    seed()
    yield


app = FastAPI(title="AEON 7080", version=SOFTWARE_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(lab.router)
app.include_router(experiments.router)
app.include_router(ai.router)
app.include_router(data_routes.router)
app.include_router(academy.router)


@app.get("/api/health")
def health() -> dict:
    return {
        "name": "AEON 7080",
        "full_name": "AEON 7080 — AI Scientific Discovery, Virtual Healthcare Experimentation, Digital Biology & User Data Platform",
        "version": SOFTWARE_VERSION,
        "banner": "SIMULATION RESULT — NOT CLINICAL EVIDENCE, DIAGNOSIS, OR MEDICAL ADVICE.",
    }
