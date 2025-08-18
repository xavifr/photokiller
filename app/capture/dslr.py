from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtGui import QImage


def capture_dslr_photos(
    device_index: int,
    resolution: Tuple[int, int],
    num_photos: int,
    output_dir: Path,
    capture_delay: float = 1.0,
    preview_callback: Optional[callable] = None,
) -> list[Path]:
    """
    Capture photos using DSLR with optional preview callback.
    
    Args:
        device_index: Not used for DSLR (kept for signature compatibility)
        resolution: Not used for DSLR (kept for signature compatibility)
        num_photos: Number of photos to capture
        output_dir: Directory to save photos
        capture_delay: Delay between shots in seconds
        preview_callback: Optional callback for live preview (QImage -> None)
    
    Returns:
        List of captured photo paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    captured: list[Path] = []
    
    for idx in range(num_photos):
        print(f"Capturing DSLR shot {idx + 1} of {num_photos}...")
        
        # Use gphoto2 to capture and download
        tempdir = tempfile.mkdtemp(prefix="photokiller_")
        tempdir_path = Path(tempdir)
        
        try:
            # Capture and download single photo
            cmd = [
                "gphoto2",
                "--capture-image-and-download",
                "--filename",
                str(tempdir_path / f"shot_{idx + 1}.jpg"),
                "--force-overwrite",
            ]
            subprocess.run(cmd, check=True)
            
            # Move first jpg found to output_dir
            jpgs = sorted(tempdir_path.glob("*.jpg"))
            if not jpgs:
                print(f"No photo captured for shot {idx + 1}")
                continue
                
            dest = output_dir / f"shot_{idx + 1}.jpg"
            jpgs[0].rename(dest)
            captured.append(dest)
            print(f"DSLR captured: {dest}")
            
            # Note: DSLR doesn't support live preview, so preview_callback is ignored
            # But we maintain the same interface for consistency
            
        except subprocess.CalledProcessError as e:
            print(f"DSLR capture failed for shot {idx + 1}: {e}")
        except Exception as e:
            print(f"Unexpected error for shot {idx + 1}: {e}")
        finally:
            # Clean up temp directory
            import shutil
            shutil.rmtree(tempdir, ignore_errors=True)
        
        # Wait between captures (except for the last shot)
        if idx < num_photos - 1:
            print(f"Waiting {capture_delay} seconds before next shot...")
            time.sleep(capture_delay)
    
    print(f"DSLR captured {len(captured)} photos out of {num_photos} requested")
    return captured