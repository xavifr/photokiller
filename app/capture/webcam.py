from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtGui import QImage
import time

def capture_webcam_photos(
    device_index: int,
    resolution: Tuple[int, int],
    output_dir: Path,
    preview_callback: Optional[callable] = None,
) -> list[Path]:
    """
    Capture a single photo using webcam.
    
    Args:
        device_index: Camera device index
        resolution: Camera resolution (width, height)
        output_dir: Directory to save photo
        preview_callback: Optional callback for live preview (QImage -> None)
    
    Returns:
        List containing single captured photo path
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a new capture instance for this session
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {device_index}")
    
    width, height = resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Wait a moment for camera to settle
    time.sleep(0.5)
    
    captured: list[Path] = []
    
    # Capture multiple frames to get a good one
    for _ in range(3):
        ok, frame = cap.read()
        if ok and frame is not None and frame.size > 0:
            break
        time.sleep(0.1)
    
    if not ok or frame is None or frame.size == 0:
        print("Failed to capture frame")
        cap.release()
        return captured
        
    # Convert to QImage for preview if callback provided
    if preview_callback:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimage = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        preview_callback(qimage.copy())
        
    out_path = output_dir / "shot.jpg"
    success = cv2.imwrite(str(out_path), frame)
    if success:
        captured.append(out_path)
        print(f"Captured: {out_path}")
    else:
        print(f"Failed to save: {out_path}")
    
    cap.release()
    print(f"Captured {len(captured)} photo")
    return captured


