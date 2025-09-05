from __future__ import annotations

from pathlib import Path

import cups


def print_file_cups(image_path: Path, printer_name: str, copies: int = 1, custom_options: dict[str, str] | None = None) -> int:
    conn = cups.Connection()
    printers = conn.getPrinters()
    if printer_name and printer_name not in printers:
        raise RuntimeError(f"Printer '{printer_name}' not found. Available: {', '.join(printers.keys())}")
    target = printer_name or list(printers.keys())[0]
    
    # Start with basic print options
    print_options = {
        "copies": str(copies),
    }
    
    # Add custom options from config if provided
    if custom_options:
        print_options.update(custom_options)
    
    print(f"Printing to {target} with options: {print_options}")
    
    job_id = conn.printFile(target, str(image_path), "Photokiller Job", print_options)
    return job_id


