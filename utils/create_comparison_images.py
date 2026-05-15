#!/usr/bin/env python3
"""
Create side-by-side comparison images from base/head/diff screenshots.

Creates a single image with three panels:
- BEFORE (base)
- AFTER (head)
- DIFF (visual difference with highlighting)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


def create_comparison_image(
    base_path: Path,
    head_path: Path,
    output_path: Path,
    panel_width: int = 480,
    padding: int = 10,
    label_height: int = 40,
) -> bool:
    """Create a side-by-side comparison image with labels."""
    try:
        with Image.open(base_path) as base_img, Image.open(head_path) as head_img:
            # Convert to RGB
            base = base_img.convert("RGB")
            head = head_img.convert("RGB")

            # Resize images to match if needed
            if base.size != head.size:
                target_h = max(base.height, head.height)
                target_w = max(base.width, head.width)
                
                base_canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
                head_canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
                base_canvas.paste(base, (0, 0))
                head_canvas.paste(head, (0, 0))
                base = base_canvas
                head = head_canvas

            # Resize to panel width while maintaining aspect ratio
            aspect = base.height / base.width
            panel_height = int(panel_width * aspect)
            
            base_resized = base.resize((panel_width, panel_height), Image.Resampling.LANCZOS)
            head_resized = head.resize((panel_width, panel_height), Image.Resampling.LANCZOS)

            # Create diff visualization (enhanced for visibility)
            diff_img = ImageChops.difference(base, head)
            
            # Enhance diff by converting to grayscale and inverting for better visibility
            diff_gray = diff_img.convert("L")
            
            # Create a colored diff overlay
            diff_colored = Image.new("RGB", diff_img.size, (255, 255, 255))
            for y in range(diff_img.height):
                for x in range(diff_img.width):
                    r, g, b = diff_img.getpixel((x, y))
                    if r > 10 or g > 10 or b > 10:  # Threshold for change detection
                        # Highlight changes in red
                        diff_colored.putpixel((x, y), (255, 0, 0))
            
            # Blend diff with original for context
            diff_overlay = Image.blend(head, diff_colored, 0.5)
            diff_resized = diff_overlay.resize((panel_width, panel_height), Image.Resampling.LANCZOS)

            # Create combined image canvas
            total_width = (panel_width * 3) + (padding * 4)
            total_height = panel_height + label_height + (padding * 3)
            
            canvas = Image.new("RGB", (total_width, total_height), (240, 240, 240))
            draw = ImageDraw.Draw(canvas)

            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except OSError:
                font = ImageFont.load_default()

            # Add labels
            labels = ["BEFORE", "AFTER", "CHANGES HIGHLIGHTED"]
            x_positions = [
                padding,
                padding * 2 + panel_width,
                padding * 3 + panel_width * 2,
            ]

            for label, x_pos in zip(labels, x_positions):
                # Calculate text bbox for centering
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = x_pos + (panel_width - text_width) // 2
                
                # Draw label
                draw.text((text_x, padding), label, fill=(0, 0, 0), font=font)

            # Paste images
            y_offset = label_height + padding * 2
            canvas.paste(base_resized, (x_positions[0], y_offset))
            canvas.paste(head_resized, (x_positions[1], y_offset))
            canvas.paste(diff_resized, (x_positions[2], y_offset))

            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output_path, quality=95)
            
            logger.info(f"Created comparison: {output_path}")
            return True

    except Exception as exc:
        logger.error(f"Failed to create comparison for {base_path.name}: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create side-by-side comparison images"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        required=True,
        help="Directory containing BEFORE screenshots",
    )
    parser.add_argument(
        "--head-dir",
        type=Path,
        required=True,
        help="Directory containing AFTER screenshots",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for comparison images",
    )
    parser.add_argument(
        "--panel-width",
        type=int,
        default=480,
        help="Width of each panel in pixels (default: 480)",
    )

    args = parser.parse_args()

    if not args.base_dir.exists():
        logger.error(f"Base directory not found: {args.base_dir}")
        return 1

    if not args.head_dir.exists():
        logger.error(f"Head directory not found: {args.head_dir}")
        return 1

    # Find all base images
    base_images = list(args.base_dir.glob("*.png"))
    if not base_images:
        logger.error(f"No PNG images found in {args.base_dir}")
        return 1

    logger.info(f"Found {len(base_images)} base images to process")
    
    all_ok = True
    for base_path in base_images:
        head_path = args.head_dir / base_path.name
        
        if not head_path.exists():
            logger.warning(f"Skipping {base_path.name} - no matching head image")
            continue

        output_path = args.output_dir / base_path.name
        
        ok = create_comparison_image(base_path, head_path, output_path, args.panel_width)
        all_ok = all_ok and ok

    if all_ok:
        logger.info(f"\nAll comparison images created in {args.output_dir}")
        return 0
    else:
        logger.warning("\nSome comparisons failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
