from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


def compose_10x15_strip(images: Iterable[Path], output_path: Path, base_mask_path: Path | None = None, background_mask_path: Path | None = None) -> Path:
    # 10x15 cm at 300 DPI -> ~1181 x 1772 px. Use 1200x1800 for simplicity.
    canvas_w, canvas_h = 1200, 1800
    
    # Start with white canvas
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(255, 255, 255))
    
    # Apply background mask if provided (as first layer)
    if background_mask_path and background_mask_path.exists():
        try:
            print(f"Loading background mask from: {background_mask_path}")
            background = Image.open(background_mask_path)
            # Resize background to match canvas dimensions
            background = background.resize((canvas_w, canvas_h), Image.LANCZOS)
            # Convert to RGBA if not already
            if background.mode != 'RGBA':
                background = background.convert('RGBA')
            # Composite: white canvas first, then background on top
            canvas = Image.alpha_composite(canvas.convert('RGBAA'), background).convert('RGB')
            print(f"Background mask applied successfully: {background_mask_path}")
        except Exception as e:
            print(f"Warning: Could not apply background mask {background_mask_path}: {e}")
    else:
        print(f"No background mask provided or file doesn't exist: {background_mask_path}")

    imgs = [Image.open(p) for p in images]

    if len(imgs) == 1:
        imgs = imgs + imgs + imgs

    # 3-photo vertical strip with specific dimensions
    # 46mm x 35mm images with 2mm margins at 300 DPI
    # Convert mm to pixels: 1mm = 11.81 pixels at 300 DPI
    # 46mm = 543px, 35mm = 413px, 2mm = 24px
    image_w, image_h = 543, 413
    margin_mm = 24  # 2mm in pixels
    
    split_canvas_w = canvas_w // 2
    available_height = canvas_h - 300  # 300px margin only from bottom
    
    # Calculate spacing between images to distribute them evenly
    total_image_height = image_h * 3
    remaining_height = available_height - total_image_height
    spacing = remaining_height // 4  # 4 gaps: top, between images, and bottom
    
    # Start y position: top margin + spacing
    y = margin_mm + spacing
    
    for im in imgs[:3]:
        ph = im.copy()
        
        # Crop and resize to maintain aspect ratio while fitting 46mm x 35mm
        target_ratio = image_w / image_h  # 543/413 ≈ 1.31 (wider than tall)
        
        # Calculate crop dimensions to maintain aspect ratio
        if ph.width / ph.height > target_ratio:
            # Image is wider than target ratio, crop width
            new_height = ph.height
            new_width = int(ph.height * target_ratio)
            left = (ph.width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = ph.height
        else:
            # Image is taller than target ratio, crop height
            new_width = ph.width
            new_height = int(ph.width / target_ratio)
            left = 0
            top = (ph.height - new_height) // 2
            right = ph.width
            bottom = top + new_height
        
        # Crop to maintain aspect ratio
        ph = ph.crop((left, top, right, bottom))
        
        # Resize to exact dimensions: 46mm x 35mm
        ph = ph.resize((image_w, image_h), Image.LANCZOS)

        x = (split_canvas_w - image_w) // 2
        canvas.paste(ph, (x, y))

        x = (split_canvas_w - image_w) // 2 + split_canvas_w
        canvas.paste(ph, (x, y))            

        y += image_h + spacing  # move to next image position


    # Apply base mask if provided (overlay on final composition)
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
            print(f"Base mask applied: {base_mask_path}")
        except Exception as e:
            print(f"Warning: Could not apply base mask {base_mask_path}: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=95)
    return output_path


