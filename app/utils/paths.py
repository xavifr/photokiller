from __future__ import annotations

from datetime import datetime
from pathlib import Path


def make_session_dir(base_dir: str) -> Path:
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session = base / ts
    session.mkdir(parents=True, exist_ok=True)
    return session


