from __future__ import annotations

from pathlib import Path

import cups


def print_file_cups(image_path: Path, printer_name: str, copies: int = 1, paper_name: str | None = None) -> int:
    conn = cups.Connection()
    printers = conn.getPrinters()
    if printer_name and printer_name not in printers:
        raise RuntimeError(f"Printer '{printer_name}' not found. Available: {', '.join(printers.keys())}")
    target = printer_name or list(printers.keys())[0]
    
    # CUPS print options for photo paper
    print_options = {
        "copies": str(copies),
        "fit-to-page": "true",  # Fit image to page
        "scaling": "100",  # 100% scaling
        "position": "center",  # Center the image
        "print-quality": "4",  # High quality (4 = 300 DPI)
        "print-color-mode": "color",  # Color printing
        "print-scaling": "fit",  # Fit to page
    }
    
    # Only add media option if paper_name is specified
    if paper_name is not None:
        print_options["media"] = paper_name
    
    job_id = conn.printFile(target, str(image_path), "Photokiller Job", print_options)
    return job_id


