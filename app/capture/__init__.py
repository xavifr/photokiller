from __future__ import annotations

from pathlib import Path
from typing import Literal

from .webcam import capture_webcam_photos
from .dslr import capture_dslr_photos


def capture_photos(
    camera_mode: Literal["webcam", "dslr"],
    device_index: int,
    resolution: Tuple[int, int],
    output_dir: Path,
    preview_callback: callable | None = None,
) -> list[Path]:
    """
    Unified capture function that delegates to appropriate camera module.
    
    Note: Both webcam and DSLR capture functions now only support single photos.
    Multiple captures are handled by the application calling this function
    multiple times.
    
    Args:
        camera_mode: "webcam" or "dslr"
        device_index: Camera device index (for webcam)
        resolution: Camera resolution (width, height)
        output_dir: Directory to save photo
        preview_callback: Optional callback for live preview (QImage -> None)
    
    Returns:
        List containing single captured photo path
    """
    if camera_mode == "webcam":
        return capture_webcam_photos(
            device_index, resolution, output_dir, preview_callback
        )
    elif camera_mode == "dslr":
        return capture_dslr_photos(
            output_dir
        )
    else:
        raise ValueError(f"Unknown camera mode: {camera_mode}")


__all__ = ["capture_photos", "capture_webcam_photos", "capture_dslr_photos"]

