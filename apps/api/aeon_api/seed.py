"""Seed the demo workspace, synthetic tables, and academy media."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import uuid
from pathlib import Path

from sqlalchemy import select

from aeon_api.config import DEMO_EMAIL, DEMO_NAME, DEMO_PASSWORD, STORAGE
from aeon_api.db import Base, SessionLocal, engine
from aeon_api.models import (
    Dataset,
    DatasetPermission,
    DatasetVersion,
    User,
    Video,
    VideoAttachment,
    VideoCategory,
    VideoChapter,
    VideoTranscript,
    Workspace,
)
from aeon_api.security import hash_password
from data.ingestion.profiler import profile_frame, read_table
from data.validation.quality import quality_report
from simulation_engine.patients.virtual_patient import generate_population

LESSONS = [
    {
        "slug": "what-is-aeon-7080",
        "title": "What is AEON 7080?",
        "description": "A short orientation to the computational laboratory, the AI Scientist, and the safety labels.",
        "category": "getting-started",
        "demo": "orientation",
        "template": "",
        "duration": 24,
        "slides": [
            (0, "AEON 7080", "A computational laboratory. Not a medical device."),
            (6, "Learn, then compute", "Academy videos lead into interactive demos."),
            (12, "Numbers come from tools", "The AI Scientist calls solvers. It does not invent results."),
            (18, "Your data stays yours", "Training and analytics sharing default to off."),
        ],
    },
    {
        "slug": "drug-response",
        "title": "Drug response in a virtual patient",
        "description": "Walk through a hypothetical PK/PD comparison on one synthetic record.",
        "category": "pharmacology",
        "demo": "drug-response",
        "template": "drug-response",
        "duration": 36,
        "slides": [
            (0, "Introduction", "Two hypothetical parameter sets. Not real drugs."),
            (6, "Create a synthetic patient", "Age, glucose, and weight come from a seeded generator."),
            (12, "Start the simulation", "Oral one-compartment PK and an indirect glucose response."),
            (18, "Administer the intervention", "Concentration, glucose, and a hypothetical heart-rate parameter."),
            (24, "AI analysis", "Monte Carlo bands, sensitivity, and a critic that only flags."),
            (30, "Generate the report", "The report quotes the computed numbers and cites nothing it did not retrieve."),
        ],
    },
]


def seed() -> None:
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        user = session.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                id=str(uuid.uuid4()),
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                display_name=DEMO_NAME,
                is_admin=True,
            )
            session.add(user)
            session.flush()
            session.add(Workspace(id=str(uuid.uuid4()), owner_id=user.id, name="Demo workspace"))
            session.flush()
        workspace = session.scalar(select(Workspace).where(Workspace.owner_id == user.id))
        if workspace is None:
            workspace = Workspace(id=str(uuid.uuid4()), owner_id=user.id, name="Demo workspace")
            session.add(workspace)
            session.flush()
        _seed_dataset(session, workspace.id)
        _seed_videos(session)
        session.commit()
    finally:
        session.close()


def _seed_dataset(session, workspace_id: str) -> None:
    existing = session.scalar(select(Dataset).where(Dataset.workspace_id == workspace_id, Dataset.name == "Synthetic diabetes records"))
    if existing:
        return
    population = generate_population(7, 40, "synthetic_diabetes")
    path = STORAGE / "datasets" / workspace_id
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "synthetic_diabetes.csv"
    with file_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["age", "weight_kg", "height_cm", "glucose_mg_dl", "heart_rate_bpm", "systolic", "diastolic"],
        )
        writer.writeheader()
        for patient in population["patients"]:
            writer.writerow(
                {
                    "age": patient["age"],
                    "weight_kg": patient["weight_kg"],
                    "height_cm": patient["height_cm"],
                    "glucose_mg_dl": patient["glucose_mg_dl"],
                    "heart_rate_bpm": patient["heart_rate_bpm"],
                    "systolic": patient["blood_pressure_mmhg"]["systolic"],
                    "diastolic": patient["blood_pressure_mmhg"]["diastolic"],
                }
            )
    frame = read_table(file_path)
    profile = profile_frame(frame)
    quality = quality_report(frame, profile)
    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
    dataset_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())
    session.add(Dataset(id=dataset_id, workspace_id=workspace_id, name="Synthetic diabetes records", kind="tabular"))
    session.add(
        DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=1,
            storage_path=str(file_path),
            content_hash=digest,
            source="synthetic-generator",
            notes="SYNTHETIC DATA. Seed 7. Not real people.",
            row_count=profile["rows"],
            schema_json={"columns": profile["column_names"], "label": "SYNTHETIC DATA"},
            profile_json=profile,
            quality_json=quality,
        )
    )
    session.add(
        DatasetPermission(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            use_in_experiments=True,
            allow_training=False,
            allow_analytics=False,
        )
    )


def _seed_videos(session) -> None:
    for lesson in LESSONS:
        if session.scalar(select(Video).where(Video.title == lesson["title"])):
            continue
        media = _render_lesson(lesson)
        video_id = str(uuid.uuid4())
        session.add(
            Video(
                id=video_id,
                title=lesson["title"],
                description=lesson["description"],
                category=lesson["category"],
                video_url=f"/api/academy/videos/{video_id}/media",
                thumbnail_url=f"/api/academy/videos/{video_id}/thumbnail",
                duration_seconds=lesson["duration"],
                difficulty="intro",
                tags_json=["aeon-7080", lesson["category"]],
                interactive_demo_id=lesson["demo"],
                template_id=lesson["template"],
            )
        )
        if session.scalar(select(VideoCategory).where(VideoCategory.slug == lesson["category"])) is None:
            session.add(
                VideoCategory(
                    id=str(uuid.uuid4()),
                    slug=lesson["category"],
                    name=lesson["category"].replace("-", " ").title(),
                )
            )
        for index, (start, title, text) in enumerate(lesson["slides"]):
            session.add(VideoChapter(id=str(uuid.uuid4()), video_id=video_id, start_seconds=start, title=title, sort_order=index))
            session.add(VideoTranscript(id=str(uuid.uuid4()), video_id=video_id, start_seconds=start, text=text, sort_order=index))
        session.add(VideoAttachment(id=str(uuid.uuid4()), video_id=video_id, kind="mp4", path=str(media["mp4"])))
        session.add(VideoAttachment(id=str(uuid.uuid4()), video_id=video_id, kind="thumbnail", path=str(media["png"])))
        session.add(VideoAttachment(id=str(uuid.uuid4()), video_id=video_id, kind="captions", path=str(media["vtt"])))


def _render_lesson(lesson: dict) -> dict[str, Path]:
    folder = STORAGE / "videos"
    folder.mkdir(parents=True, exist_ok=True)
    mp4 = folder / f"{lesson['slug']}.mp4"
    png = folder / f"{lesson['slug']}.png"
    vtt = folder / f"{lesson['slug']}.vtt"
    if not mp4.exists():
        font = _font()
        filters = []
        for start, title, text in lesson["slides"]:
            end = start + 6
            filters.append(
                f"drawtext=fontfile='{font}':text='{_ffmpeg_text(title)}':fontsize=54:fontcolor=0x5eead4:"
                f"x=(w-text_w)/2:y=h/2-70:enable='between(t,{start},{end})'"
            )
            filters.append(
                f"drawtext=fontfile='{font}':text='{_ffmpeg_text(text)}':fontsize=28:fontcolor=0xe6eef2:"
                f"x=(w-text_w)/2:y=h/2+10:enable='between(t,{start},{end})'"
            )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x071018:s=1280x720:d={lesson['duration']}:r=24",
                "-vf",
                ",".join(filters),
                "-pix_fmt",
                "yuv420p",
                str(mp4),
            ],
            check=True,
            capture_output=True,
        )
    if not png.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp4), "-frames:v", "1", str(png)],
            check=True,
            capture_output=True,
        )
    if not vtt.exists():
        lines = ["WEBVTT", ""]
        for start, title, text in lesson["slides"]:
            lines.append(f"{_ts(start)} --> {_ts(start + 6)}")
            lines.append(f"{title}. {text}")
            lines.append("")
        vtt.write_text("\n".join(lines))
    return {"mp4": mp4, "png": png, "vtt": vtt}


def _ffmpeg_text(value: str) -> str:
    return (
        value.replace("\\", "")
        .replace(":", "\\:")
        .replace("'", "")
        .replace(",", "\\,")
        .replace("%", "")
    )


def _font() -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("No font available for academy video rendering.")


def _ts(seconds: float) -> str:
    total = int(seconds)
    return f"00:{total // 60:02d}:{total % 60:02d}.000"
