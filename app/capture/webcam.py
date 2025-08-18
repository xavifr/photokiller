from __future__ import annotations

import time
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
from PySide6.QtGui import QImage


def capture_webcam_photos(
    device_index: int,
    resolution: Tuple[int, int],
    num_photos: int,
    output_dir: Path,
    capture_delay: float = 1.0,
    preview_callback: Optional[callable] = None,
) -> list[Path]:
    """
    Capture photos using webcam with optional preview callback.
    
    Args:
        device_index: Camera device index
        resolution: Camera resolution (width, height)
        num_photos: Number of photos to capture
        output_dir: Directory to save photos
        capture_delay: Delay between shots in seconds
        preview_callback: Optional callback for live preview (QImage -> None)
    
    Returns:
        List of captured photo paths
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
    for idx in range(num_photos):
        # Capture multiple frames to get a good one
        for _ in range(3):
            ok, frame = cap.read()
            if ok and frame is not None and frame.size > 0:
                break
            time.sleep(0.1)
        
        if not ok or frame is None or frame.size == 0:
            print(f"Failed to capture frame {idx + 1}")
            continue
            
        # Convert to QImage for preview if callback provided
        if preview_callback:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimage = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            preview_callback(qimage.copy())
            
        out_path = output_dir / f"shot_{idx + 1}.jpg"
        success = cv2.imwrite(str(out_path), frame)
        if success:
            captured.append(out_path)
            print(f"Captured: {out_path}")
        else:
            print(f"Failed to save: {out_path}")
        
        # Wait between captures (except for the last shot)
        if idx < num_photos - 1:
            print(f"Waiting {capture_delay} seconds before next shot...")
            time.sleep(capture_delay)
    
    cap.release()
    print(f"Captured {len(captured)} photos out of {num_photos} requested")
    return captured


