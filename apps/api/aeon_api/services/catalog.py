"""Serialize academy records."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from aeon_api.models import Video, VideoChapter, VideoTranscript


def video_summary(video: Video) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "category": video.category,
        "video_url": video.video_url,
        "thumbnail_url": video.thumbnail_url,
        "duration": video.duration_seconds,
        "difficulty": video.difficulty,
        "tags": video.tags_json,
        "interactive_demo_id": video.interactive_demo_id,
        "template_id": video.template_id,
    }


def video_detail(session: Session, video: Video) -> dict:
    chapters = session.scalars(
        select(VideoChapter).where(VideoChapter.video_id == video.id).order_by(VideoChapter.sort_order)
    ).all()
    lines = session.scalars(
        select(VideoTranscript).where(VideoTranscript.video_id == video.id).order_by(VideoTranscript.sort_order)
    ).all()
    payload = video_summary(video)
    payload["chapters"] = [
        {"start_seconds": c.start_seconds, "title": c.title} for c in chapters
    ]
    payload["transcript"] = [
        {"start_seconds": line.start_seconds, "text": line.text} for line in lines
    ]
    return payload
