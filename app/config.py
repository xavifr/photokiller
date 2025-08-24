from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class CameraConfig(BaseModel):
    mode: Literal["webcam", "dslr"] = "webcam"
    device_index: int = 0
    skip_preview: bool = False
    resolution: tuple[int, int] = (1280, 720)
    dslr_preview_interval: float = 1.0  # Seconds between DSLR preview captures


class SessionConfig(BaseModel):
    shots: Literal[1, 3] = 3
    countdown_seconds: int = 3
    capture_delay: float = 3.0  # Delay between shots in seconds
    save_dir: str = "sessions"


class PrintConfig(BaseModel):
    enabled: bool = True
    printer_name: str = ""
    copies: int = 1
    paper_size_mm: tuple[int, int] = (100, 150)


class LayoutConfig(BaseModel):
    base_mask: str = ""
    background_mask: str = ""


class GpioConfig(BaseModel):
    enabled: bool = False
    button_shoot_pin: int = 17
    button_print_pin: int = 27


class AppConfig(BaseModel):
    camera: CameraConfig = Field(default_factory=CameraConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    printing: PrintConfig = Field(default_factory=PrintConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    gpio: GpioConfig = Field(default_factory=GpioConfig)

    # Misc
    ui_fullscreen: bool = True


DEFAULT_CONFIG_PATH = Path("config/config.json")


def load_config(path: Path | None = None) -> AppConfig:
    cfg_path = path or DEFAULT_CONFIG_PATH
    if cfg_path.exists():
        data = json.loads(cfg_path.read_text())
        return AppConfig.model_validate(data)
    cfg = AppConfig()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg.model_dump(mode="json"), indent=2))
    return cfg


