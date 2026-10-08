# Academy

Lessons are rows in `videos`, `video_chapters`, and `video_transcripts`. The workstation reads `video_url` from the API. It does not hard-code media paths.

The seed renders two short MP4 lessons with ffmpeg into `storage/videos/`, plus a PNG thumbnail and a WebVTT caption file.

Search looks through titles, descriptions, chapters, and transcript lines.

Progress is stored per user when playback pauses or ends.
