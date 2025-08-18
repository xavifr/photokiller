from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


def compose_10x15_strip(images: Iterable[Path], output_path: Path, base_mask_path: Path | None = None) -> Path:
    # 10x15 cm at 300 DPI -> ~1181 x 1772 px. Use 1200x1800 for simplicity.
    canvas_w, canvas_h = 1200, 1800
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(255, 255, 255))

    imgs = [Image.open(p) for p in images]

    if len(imgs) == 1:
        # Single photo centered, with visible border
        target_w, target_h = 1100, 1650
        img = imgs[0].copy()
        img.thumbnail((target_w, target_h), Image.LANCZOS)
        x = (canvas_w - img.width) // 2
        y = int(float((canvas_h - img.height)) * 0.4)
        canvas.paste(img, (x, y))
    else:
        # 3-photo vertical strip centered, each with border
        margin = 30
        slot_h = (canvas_h - margin * 4) // 3
        slot_w = canvas_w - 2 * margin
        y = margin
        for im in imgs[:3]:
            ph = im.copy()
            ph.thumbnail((slot_w, slot_h), Image.LANCZOS)
            ph = ImageOps.scale(ph, 0.9)
            x = (canvas_w - ph.width) // 2
            canvas.paste(ph, (x, y))
            y += ph.height + margin  # ensure spacing accounts for border

    # Apply base mask if provided
    if base_mask_path and base_mask_path.exists():
        try:
            mask = Image.open(base_mask_path)
            # Resize mask to match canvas dimensions
            mask = mask.resize((canvas_w, canvas_h), Image.LANCZOS)
            # Convert to RGBA if not already
            if mask.mode != 'RGBA':
                mask = mask.convert('RGBA')
            # Composite the mask over the canvas
            canvas = Image.alpha_composite(canvas.convert('RGBA'), mask).convert('RGB')
        except Exception as e:
            print(f"Warning: Could not apply base mask {base_mask_path}: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=95)
    return output_path


