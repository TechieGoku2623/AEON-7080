# Video system

`VideoStorageProvider` in this build is the local directory `storage/videos`. The API serves bytes from the path stored on `video_attachments`. Replacing that directory with object storage means changing the attachment resolver, not the React player.

Administrators (`is_admin`) can `POST /api/academy/videos` with an MP4. The demo user is an admin so local authoring works. Production should use a separate admin account.

Captions are WebVTT. Chapters seek the HTML video element.
