"""Academy catalog. Media paths come from the database."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from aeon_api.config import STORAGE
from aeon_api.db import get_session
from aeon_api.models import (
    User,
    Video,
    VideoAttachment,
    VideoChapter,
    VideoProgress,
    VideoTranscript,
)
from aeon_api.security import current_user, new_id
from aeon_api.services.catalog import video_detail, video_summary

router = APIRouter(prefix="/api/academy", tags=["academy"])


@router.get("/videos")
def list_videos(session: Session = Depends(get_session)) -> dict:
    rows = session.scalars(select(Video).order_by(Video.title)).all()
    return {"videos": [video_summary(row) for row in rows]}


@router.get("/search")
def search(q: str, session: Session = Depends(get_session)) -> dict:
    query = f"%{q.lower()}%"
    videos = session.scalars(select(Video)).all()
    hits = []
    for video in videos:
        haystack = " ".join([video.title, video.description, video.category, " ".join(video.tags_json or [])]).lower()
        chapters = session.scalars(select(VideoChapter).where(VideoChapter.video_id == video.id)).all()
        transcripts = session.scalars(select(VideoTranscript).where(VideoTranscript.video_id == video.id)).all()
        chapter_hit = next((c.title for c in chapters if q.lower() in c.title.lower()), None)
        line_hit = next((line.text for line in transcripts if q.lower() in line.text.lower()), None)
        if q.lower() in haystack or chapter_hit or line_hit:
            hits.append(
                {
                    "video": video_summary(video),
                    "chapter": chapter_hit,
                    "transcript": line_hit,
                }
            )
    return {"query": q, "hits": hits, "unused": query}


@router.get("/videos/{video_id}")
def get_video(video_id: str, session: Session = Depends(get_session)) -> dict:
    video = session.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")
    return video_detail(session, video)


@router.get("/videos/{video_id}/media")
def media(video_id: str, session: Session = Depends(get_session)):
    return _attachment(session, video_id, "mp4", "video/mp4")


@router.get("/videos/{video_id}/thumbnail")
def thumbnail(video_id: str, session: Session = Depends(get_session)):
    return _attachment(session, video_id, "thumbnail", "image/png")


@router.get("/videos/{video_id}/captions")
def captions(video_id: str, session: Session = Depends(get_session)):
    return _attachment(session, video_id, "captions", "text/vtt")


@router.post("/videos/{video_id}/progress")
def progress(video_id: str, body: dict, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict:
    video = session.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")
    row = session.scalar(select(VideoProgress).where(VideoProgress.user_id == user.id, VideoProgress.video_id == video_id))
    if row is None:
        row = VideoProgress(id=new_id(), user_id=user.id, video_id=video_id)
        session.add(row)
    row.position_seconds = float(body.get("position_seconds", 0))
    row.completed = bool(body.get("completed", False))
    session.commit()
    return {"position_seconds": row.position_seconds, "completed": row.completed}


@router.post("/videos")
def upload_video(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("getting-started"),
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> dict:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Only an administrator can upload academy video.")
    video_id = str(uuid.uuid4())
    folder = STORAGE / "videos"
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"{video_id}.mp4"
    destination.write_bytes(file.file.read())
    video = Video(
        id=video_id,
        title=title,
        description=description,
        category=category,
        video_url=f"/api/academy/videos/{video_id}/media",
        thumbnail_url="",
        duration_seconds=0,
        interactive_demo_id="",
        template_id="",
    )
    session.add(video)
    session.add(VideoAttachment(id=new_id(), video_id=video_id, kind="mp4", path=str(destination)))
    session.commit()
    return video_summary(video)


def _attachment(session: Session, video_id: str, kind: str, media_type: str):
    row = session.scalar(
        select(VideoAttachment).where(VideoAttachment.video_id == video_id, VideoAttachment.kind == kind)
    )
    if row is None or not Path(row.path).exists():
        raise HTTPException(status_code=404, detail=f"No {kind} file for this video.")
    return FileResponse(row.path, media_type=media_type)
