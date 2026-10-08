# Development

Python 3.12, Node 22, and ffmpeg are enough for the local loop.

```bash
PYTHONPATH=.:apps/api uvicorn aeon_api.main:app --reload --port 8000
cd apps/web && npm run dev
```

`AEON_DATABASE_URL` defaults to SQLite at `storage/aeon7080.db`. Alembic's initial revision creates the same tables as the SQLAlchemy metadata.

Demo credentials are `demo@aeon7080.local` / `demo`, overridable with `AEON_DEMO_EMAIL` and `AEON_DEMO_PASSWORD`.

Set `AEON_SECRET` to a long random value outside a private laptop. The default is for development only.

Tests:

```bash
PYTHONPATH=.:apps/api pytest
cd apps/web && npm test
```

The API test module renders the academy videos once, so the first run needs ffmpeg and a font such as DejaVu Sans.
