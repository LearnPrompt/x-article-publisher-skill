#!/usr/bin/env python3
"""
Optimize Markdown media blocks for X Articles.

X Articles can silently ignore uploads after a practical body-media limit. This
helper reduces media block count by merging adjacent image-only runs into one
vertical collage, preserving videos as separate uploadable media blocks.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image, ImageOps


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".mpeg", ".mpg"}
IMAGE_PATTERN = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")
LINK_PATTERN = re.compile(r"^\[([^\]]*)\]\(([^)]+)\)$")
HTML_VIDEO_PATTERN = re.compile(
    r"^<video[^>]*(?:src=[\"']([^\"']+)[\"']|>.*?<source[^>]*src=[\"']([^\"']+)[\"'])",
    re.IGNORECASE | re.DOTALL,
)


def is_remote(path: str) -> bool:
    return urlparse(path).scheme in {"http", "https"}


def media_type(path: str) -> str:
    ext = Path(path.split("?", 1)[0].split("#", 1)[0]).suffix.lower()
    return "video" if ext in VIDEO_EXTENSIONS else "image"


def split_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code = False
    code: list[str] = []

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                code.append(line)
                blocks.append("\n".join(code))
                code = []
                in_code = False
            else:
                if current:
                    blocks.append("\n".join(current))
                    current = []
                code = [line]
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not stripped:
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        if IMAGE_PATTERN.match(stripped) or stripped.startswith(("#", ">")) or re.match(r"^---+$", stripped):
            if current:
                blocks.append("\n".join(current))
                current = []
            blocks.append(stripped)
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current))
    if code:
        blocks.append("\n".join(code))
    return blocks


def detect_media(block: str) -> tuple[str, str] | None:
    stripped = block.strip()
    image = IMAGE_PATTERN.match(stripped)
    if image:
        return "image", image.group(2)

    link = LINK_PATTERN.match(stripped)
    if link and media_type(link.group(2)) == "video":
        return "video", link.group(2)

    html_video = HTML_VIDEO_PATTERN.match(stripped)
    if html_video:
        src = html_video.group(1) or html_video.group(2)
        if src:
            return "video", src
    return None


def resolve_media_path(base: Path, media_path: str) -> Path:
    decoded = unquote(media_path)
    if is_remote(decoded):
        raise ValueError(f"remote media cannot be collaged: {decoded}")
    path = Path(decoded)
    if not path.is_absolute():
        path = base / path
    return path


def balanced_row_counts(image_count: int) -> list[int]:
    if image_count < 1:
        raise ValueError("collage requires at least one image")

    row_count = max(1, round(math.sqrt(image_count)))
    base, remainder = divmod(image_count, row_count)
    # Put the fuller rows last so five screenshots become a balanced 2 + 3 grid.
    return [base] * (row_count - remainder) + [base + 1] * remainder


def make_collage(
    image_paths: list[Path],
    output_path: Path,
    width: int,
    padding: int,
) -> dict:
    if width <= padding * 2:
        raise ValueError("collage width must be greater than twice the padding")
    if padding < 0:
        raise ValueError("collage padding cannot be negative")

    images = []
    for path in image_paths:
        with Image.open(path) as image:
            images.append(image.convert("RGB"))

    row_counts = balanced_row_counts(len(images))
    rows = []
    image_index = 0
    usable_width = width - padding * 2

    for column_count in row_counts:
        cell_width = max(
            1,
            (usable_width - padding * (column_count - 1)) // column_count,
        )
        # Constrain unusually tall screenshots without cropping them.
        cell_height = max(1, round(cell_width * 1.5))
        row_images = []
        for image in images[image_index : image_index + column_count]:
            row_images.append(
                ImageOps.contain(
                    image,
                    (cell_width, cell_height),
                    Image.Resampling.LANCZOS,
                )
            )
        image_index += column_count
        rows.append((cell_width, max(image.height for image in row_images), row_images))

    total_height = sum(row_height for _, row_height, _ in rows) + padding * (len(rows) + 1)
    canvas = Image.new("RGB", (width, total_height), "white")
    y = padding
    for cell_width, row_height, row_images in rows:
        row_width = sum(image.width for image in row_images) + padding * (len(row_images) - 1)
        x = max(padding, (width - row_width) // 2)
        for image in row_images:
            image_y = y + (row_height - image.height) // 2
            canvas.paste(image, (x, image_y))
            x += image.width + padding
        y += row_height + padding

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=92)
    return {
        "layout": "adaptive_grid",
        "rows": len(row_counts),
        "row_counts": row_counts,
        "width": canvas.width,
        "height": canvas.height,
    }


def image_runs(blocks: list[str], cover_block_index: int | None) -> list[list[int]]:
    runs: list[list[int]] = []
    current: list[int] = []
    for idx, block in enumerate(blocks):
        media = detect_media(block)
        is_body_image = media and media[0] == "image" and idx != cover_block_index
        if is_body_image:
            current.append(idx)
            continue
        if len(current) >= 2:
            runs.append(current)
        current = []
    if len(current) >= 2:
        runs.append(current)
    return runs


def count_body_media(blocks: list[str], cover_block_index: int | None) -> int:
    count = 0
    for idx, block in enumerate(blocks):
        if idx == cover_block_index:
            continue
        if detect_media(block):
            count += 1
    return count


def first_image_index(blocks: list[str]) -> int | None:
    for idx, block in enumerate(blocks):
        media = detect_media(block)
        if media and media[0] == "image":
            return idx
    return None


def optimize(markdown_path: Path, output_path: Path, max_body_media: int, width: int, padding: int) -> dict:
    original = markdown_path.read_text(encoding="utf-8")
    blocks = split_blocks(original)
    base = markdown_path.parent
    cover_idx = first_image_index(blocks)
    original_body_media = count_body_media(blocks, cover_idx)

    if original_body_media <= max_body_media:
        output_path.write_text(original, encoding="utf-8")
        return {
            "input": str(markdown_path),
            "output": str(output_path),
            "changed": False,
            "body_media_before": original_body_media,
            "body_media_after": original_body_media,
            "collages": [],
        }

    needed_reduction = original_body_media - max_body_media
    runs = sorted(image_runs(blocks, cover_idx), key=len, reverse=True)
    collages = []
    replacements: dict[int, str] = {}
    skip: set[int] = set()
    reduced = 0

    for collage_index, run in enumerate(runs, start=1):
        if reduced >= needed_reduction:
            break
        image_paths = []
        for block_index in run:
            media = detect_media(blocks[block_index])
            if not media:
                continue
            image_paths.append(resolve_media_path(base, media[1]))
        if any(not path.exists() for path in image_paths):
            missing = [str(path) for path in image_paths if not path.exists()]
            raise FileNotFoundError(f"cannot collage missing image(s): {missing}")

        collage_name = f"x_article_collage_{collage_index:02d}.png"
        collage_path = base / "static" / collage_name
        layout = make_collage(image_paths, collage_path, width=width, padding=padding)
        rel_path = collage_path.relative_to(base).as_posix()
        replacements[run[0]] = f"![Collage {collage_index}]({rel_path})"
        skip.update(run[1:])
        reduced += len(run) - 1
        collages.append(
            {
                "path": str(collage_path),
                "merged_count": len(run),
                "source_paths": [str(path) for path in image_paths],
                **layout,
            }
        )

    new_blocks = []
    for idx, block in enumerate(blocks):
        if idx in skip:
            continue
        new_blocks.append(replacements.get(idx, block))

    optimized = "\n\n".join(new_blocks) + "\n"
    output_path.write_text(optimized, encoding="utf-8")
    after_body_media = count_body_media(new_blocks, first_image_index(new_blocks))

    return {
        "input": str(markdown_path),
        "output": str(output_path),
        "changed": bool(collages),
        "body_media_before": original_body_media,
        "body_media_after": after_body_media,
        "target_body_media": max_body_media,
        "collages": collages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge adjacent image runs to stay under X body-media limits")
    parser.add_argument("markdown_file", help="Markdown file to optimize")
    parser.add_argument("--output", help="Output markdown path; default: <stem>.optimized.md")
    parser.add_argument("--max-body-media", type=int, default=24, help="Safe target for body media blocks")
    parser.add_argument("--width", type=int, default=1920, help="Final collage width")
    parser.add_argument("--padding", type=int, default=18, help="Collage padding in pixels")
    args = parser.parse_args()

    markdown_path = Path(args.markdown_file).expanduser().resolve()
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else markdown_path.with_name(f"{markdown_path.stem}.optimized{markdown_path.suffix}")
    )
    try:
        result = optimize(markdown_path, output_path, args.max_body_media, args.width, args.padding)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
