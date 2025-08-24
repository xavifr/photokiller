from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def capture_dslr_photos(
    output_dir: Path,
) -> list[Path]:
    """
    Capture a single photo using DSLR.
    
    Args:
        output_dir: Directory to save photo
    
    Returns:
        List containing single captured photo path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    captured: list[Path] = []
    
    print("Capturing DSLR shot...")
    
    # Use gphoto2 to capture and download
    tempdir = tempfile.mkdtemp(prefix="photokiller_")
    tempdir_path = Path(tempdir)
    
    try:
        # Capture and download single photo
        cmd = [
            "gphoto2",
            "--capture-image-and-download",
            "--filename",
            str(tempdir_path / "shot.jpg"),
            "--force-overwrite",
        ]
        subprocess.run(cmd, check=True)
        
        # Move first jpg found to output_dir
        jpgs = sorted(tempdir_path.glob("*.jpg"))
        if not jpgs:
            print("No photo captured")
            return captured
            
        dest = output_dir / "shot.jpg"
        jpgs[0].rename(dest)
        captured.append(dest)
        print(f"DSLR captured: {dest}")
        
    except subprocess.CalledProcessError as e:
        print(f"DSLR capture failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Clean up temp directory
        import shutil
        shutil.rmtree(tempdir, ignore_errors=True)
    
    print(f"DSLR captured {len(captured)} photo")
    return captured