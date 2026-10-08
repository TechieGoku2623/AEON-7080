"""Runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STORAGE = Path(os.environ.get("AEON_STORAGE", ROOT / "storage"))
DATABASE_URL = os.environ.get("AEON_DATABASE_URL", f"sqlite:///{STORAGE / 'aeon7080.db'}")
SECRET = os.environ.get("AEON_SECRET", "aeon-7080-dev-secret-change-me")
TOKEN_HOURS = int(os.environ.get("AEON_TOKEN_HOURS", "168"))
DEMO_EMAIL = os.environ.get("AEON_DEMO_EMAIL", "demo@aeon7080.local")
DEMO_PASSWORD = os.environ.get("AEON_DEMO_PASSWORD", "demo")
DEMO_NAME = "AEON 7080 demo"
SOFTWARE_VERSION = "0.1.0"
