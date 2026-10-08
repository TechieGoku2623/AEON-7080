"""Isolate API tests from any developer database."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_ROOT = Path(tempfile.mkdtemp(prefix="aeon7080-"))
os.environ["AEON_DATABASE_URL"] = f"sqlite:///{_ROOT / 'test.db'}"
os.environ["AEON_STORAGE"] = str(_ROOT)
os.environ["AEON_SECRET"] = "test-secret"
os.environ["AEON_DEMO_EMAIL"] = "demo@aeon7080.local"
os.environ["AEON_DEMO_PASSWORD"] = "demo"
