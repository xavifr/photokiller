from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication

from .config import load_config, AppConfig
from .ui.main_window import MainWindow


def ensure_directories(config: AppConfig) -> None:
    Path(config.session.save_dir).mkdir(parents=True, exist_ok=True)


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv
    os.environ.setdefault("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "xcb"))

    config = load_config()
    ensure_directories(config)

    app = QApplication(argv)
    window = MainWindow(config)
    window.show()  # show() will display in fullscreen mode as set in __init__
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

