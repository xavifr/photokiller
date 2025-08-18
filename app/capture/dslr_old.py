from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import List


def capture_dslr_photos(num_photos: int, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    captured: list[Path] = []
    for idx in range(num_photos):
        tempdir = tempfile.mkdtemp(prefix="photokiller_")
        tempdir_path = Path(tempdir)
        # Use gphoto2 to capture and download
        # --force-overwrite to ensure same names won't break
        cmd: list[str] = [
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
            continue
        dest = output_dir / f"shot_{idx + 1}.jpg"
        jpgs[0].rename(dest)
        captured.append(dest)
    return captured


