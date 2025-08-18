from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional, Literal

from .webcam import capture_webcam_photos
from .dslr import capture_dslr_photos


def capture_photos(
    camera_mode: Literal["webcam", "dslr"],
    device_index: int,
    resolution: Tuple[int, int],
    num_photos: int,
    output_dir: Path,
    capture_delay: float = 1.0,
    preview_callback: Optional[callable] = None,
) -> List[Path]:
    """
    Unified capture function that delegates to appropriate camera module.
    
    Args:
        camera_mode: "webcam" or "dslr"
        device_index: Camera device index (for webcam)
        resolution: Camera resolution (width, height)
        num_photos: Number of photos to capture
        output_dir: Directory to save photos
        capture_delay: Delay between shots in seconds
        preview_callback: Optional callback for live preview (QImage -> None)
    
    Returns:
        List of captured photo paths
    """
    if camera_mode == "webcam":
        return capture_webcam_photos(
            device_index, resolution, num_photos, output_dir, capture_delay, preview_callback
        )
    elif camera_mode == "dslr":
        return capture_dslr_photos(
            device_index, resolution, num_photos, output_dir, capture_delay, preview_callback
        )
    else:
        raise ValueError(f"Unknown camera mode: {camera_mode}")


__all__ = ["capture_photos", "capture_webcam_photos", "capture_dslr_photos"]

