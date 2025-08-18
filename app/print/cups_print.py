from __future__ import annotations

from pathlib import Path

import cups


def print_file_cups(image_path: Path, printer_name: str, copies: int = 1) -> int:
    conn = cups.Connection()
    printers = conn.getPrinters()
    if printer_name and printer_name not in printers:
        raise RuntimeError(f"Printer '{printer_name}' not found. Available: {', '.join(printers.keys())}")
    target = printer_name or list(printers.keys())[0]
    job_id = conn.printFile(target, str(image_path), "Photokiller Job", {})
    # Set copies using CUPS attributes if needed; basic print is fine for Selphy
    return job_id


