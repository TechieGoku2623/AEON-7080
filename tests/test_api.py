"""API integration for the working vertical slice."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aeon_api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/auth/login",
            json={"email": "demo@aeon7080.local", "password": "demo"},
        )
        assert login.status_code == 200
        test_client.headers["Authorization"] = f"Bearer {login.json()['token']}"
        yield test_client


def test_health_names_the_platform(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["name"] == "AEON 7080"


def test_exponential_endpoint_and_patient(client):
    simulated = client.post(
        "/api/simulations/run",
        json={"model": "exponential_decay", "parameters": {"C0": 4, "k": 0.5}, "duration": 2, "dt": 0.05, "seed": 3},
    )
    assert simulated.status_code == 200
    body = simulated.json()
    assert body["model_name"] == "exponential_decay"
    assert body["results"]["max_abs_error"] < 1e-5
    patient = client.post("/api/patients/generate", json={"seed": 9, "condition": "synthetic_diabetes"})
    assert patient.status_code == 200
    assert patient.json()["label"] == "SYNTHETIC DATA"


def test_experiment_run_replay_and_report(client):
    created = client.post(
        "/api/experiments",
        json={
            "title": "API slice",
            "config": {"monte_carlo": {"n": 12, "cv": 0.05}, "duration_h": 6, "dt_h": 0.2, "mode": "patient"},
        },
    )
    assert created.status_code == 200
    experiment_id = created.json()["id"]
    ran = client.post(f"/api/experiments/{experiment_id}/run")
    assert ran.status_code == 200, ran.text
    result = ran.json()["result"]
    assert "Treatment_B" in result["drugs"]
    assert "NOT CLINICAL" in result["labels"][0]
    replay = client.post(f"/api/experiments/{experiment_id}/replay")
    assert replay.status_code == 200
    assert replay.json()["matched_previous"] is True
    report = client.get(f"/api/reports/{ran.json()['report_id']}")
    assert "No external citations" in report.json()["markdown"]


def test_unknown_model_and_disallowed_advice(client):
    missing = client.post("/api/simulations/run", json={"model": "binding_affinity", "parameters": {}})
    assert missing.status_code == 404
    advice = client.post("/api/ai/execute", json={"message": "Diagnose me and prescribe a dose"})
    assert advice.status_code == 200
    assert advice.json()["executed"] is False


def test_upload_profile_map_and_question(client):
    uploaded = client.post(
        "/api/data/upload",
        files={"file": ("study.csv", b"age,glucose,heart_rate\n55,145,78\n56,150,80\n", "text/csv")},
        data={"name": "Study", "use_in_experiments": "true", "allow_training": "false", "allow_analytics": "false"},
    )
    assert uploaded.status_code == 200, uploaded.text
    dataset_id = uploaded.json()["id"]
    assert uploaded.json()["profile"]["rows"] == 2
    assert uploaded.json()["quality"]["score"] > 0
    refused = client.post(
        f"/api/data/{dataset_id}/map",
        json={"mapping": [{"column": "glucose", "parameter": "physiology.glucose_mg_dl"}], "confirmed": False},
    )
    assert refused.status_code == 409
    mapped = client.post(
        f"/api/data/{dataset_id}/map",
        json={
            "mapping": [{"column": "glucose", "parameter": "physiology.glucose_mg_dl", "confirmed": True}],
            "confirmed": True,
        },
    )
    assert mapped.status_code == 200
    assert mapped.json()["label"] == "DATA-CONDITIONED COMPUTATIONAL MODEL"
    answer = client.post(f"/api/data/{dataset_id}/analyze", json={"question": "What is associated with glucose?"})
    assert answer.status_code == 200
    assert answer.json()["supported"] is True
    permission = client.get(f"/api/data/{dataset_id}").json()["permission"]
    assert permission["allow_training"] is False
    assert permission["allow_analytics"] is False


def test_academy_catalog_is_not_hardcoded_empty(client):
    videos = client.get("/api/academy/videos")
    assert videos.status_code == 200
    rows = videos.json()["videos"]
    assert len(rows) >= 2
    detail = client.get(f"/api/academy/videos/{rows[0]['id']}")
    assert detail.json()["chapters"]
    assert detail.json()["video_url"].endswith("/media")
    media = client.get(detail.json()["video_url"])
    assert media.status_code == 200
    assert media.headers["content-type"].startswith("video/")
    found = client.get("/api/academy/search", params={"q": "PK"})
    assert found.status_code == 200
