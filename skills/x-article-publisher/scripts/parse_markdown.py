#!/usr/bin/env python3
"""
Parse Markdown for X Articles publishing.

Extracts:
- Title (from first H1/H2 or first line)
- Cover image (first image)
- Content media (images + videos) with block index for precise positioning
- Dividers (---) with block index for menu insertion
- HTML content (media and dividers stripped)

Usage:
    python parse_markdown.py <markdown_file> [--output json|html]

Output (JSON):
{
    "title": "Article Title",
    "cover_image": "/path/to/cover.jpg",
    "content_media": [
        {"type": "image", "path": "/path/to/img.jpg", "block_index": 3, "after_text": "context..."},
        {"type": "video", "path": "/path/to/video.mp4", "block_index": 8, "after_text": "context..."},
        ...
    ],
    "content_images": [...],  // backwards compatible
    "content_videos": [...],
    "dividers": [
        {"block_index": 7, "after_text": "context..."},
        ...
    ],
    "html": "<p>Content...</p><h2>Section</h2>...",
    "total_blocks": 25
}

The block_index indicates which block element (0-indexed) the image/divider should follow.
This allows precise positioning without relying on text matching.

Note: Dividers must be inserted via X Articles' Insert > Divider menu, not HTML <hr> tags.
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path


# Common search directories for missing media
SEARCH_DIRS = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Pictures",
]

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".mpeg", ".mpg"}


def is_remote_path(media_path: str) -> bool:
    """Whether media_path is a remote URL."""
    parsed = urllib.parse.urlparse(media_path)
    return parsed.scheme in ("http", "https")


def media_type_for_path(media_path: str) -> str:
    """Infer media type from path extension."""
    clean = media_path.split("?", 1)[0].split("#", 1)[0]
    ext = Path(clean).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "image"


def find_media_file(original_path: str, filename: str, media_type: str) -> tuple[str, bool]:
    """Find a media file, searching common directories if not found at original path.
    
    Args:
        original_path: The resolved absolute path from markdown
        filename: Just the filename to search for
        media_type: "image" or "video"
    
    Returns:
        (found_path, exists): The path to use and whether file exists
    """
    if os.path.isfile(original_path):
        return original_path, True
    
    for search_dir in SEARCH_DIRS:
        candidate = search_dir / filename
        if candidate.is_file():
            print(
                f"[parse_markdown] {media_type.capitalize()} not found at '{original_path}', using '{candidate}' instead",
                file=sys.stderr
            )
            return str(candidate), True
    
    print(
        f"[parse_markdown] WARNING: {media_type.capitalize()} not found: '{original_path}' "
        f"(also searched {[str(d) for d in SEARCH_DIRS]})",
        file=sys.stderr
    )
    return original_path, False


def split_into_blocks(markdown: str) -> list[str]:
    """Split markdown into logical blocks (paragraphs, headers, quotes, code blocks, etc.)."""
    blocks = []
    current_block = []
    in_code_block = False
    code_block_lines = []

    lines = markdown.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle code block boundaries
        if stripped.startswith('```'):
            if in_code_block:
                # End of code block
                in_code_block = False
                if code_block_lines:
                    # Mark as code block with special prefix for later processing
                    # Use ___CODE_BLOCK_START___ and ___CODE_BLOCK_END___ to preserve content
                    blocks.append('___CODE_BLOCK_START___' + '\n'.join(code_block_lines) + '___CODE_BLOCK_END___')
                code_block_lines = []
            else:
                # Start of code block
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                in_code_block = True
            i += 1
            continue

        # If inside code block, collect ALL lines (including empty lines)
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Group contiguous blockquote lines as one block to preserve multiline callouts.
        if stripped.startswith('>'):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            quote_lines = []
            while i < len(lines):
                q_line = lines[i]
                if not q_line.strip().startswith('>'):
                    break
                quote_lines.append(q_line.strip())
                i += 1
            if quote_lines:
                blocks.append('\n'.join(quote_lines))
            continue

        # Empty line signals end of paragraph block
        if not stripped:
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            i += 1
            continue

        # Horizontal rule (divider) is its own block
        if re.match(r'^---+$', stripped):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append('___DIVIDER___')
            i += 1
            continue

        # Headers are their own blocks
        if stripped.startswith('#'):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append(stripped)
            i += 1
            continue

        # Image on its own line is its own block
        if re.match(r'^!\[.*\]\(.*\)$', stripped):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append(stripped)
            i += 1
            continue

        current_block.append(line)
        i += 1

    if current_block:
        blocks.append('\n'.join(current_block))

    # Handle unclosed code block
    if code_block_lines:
        blocks.append('___CODE_BLOCK_START___' + '\n'.join(code_block_lines) + '___CODE_BLOCK_END___')

    return blocks


def extract_media_and_dividers(markdown: str, base_path: Path) -> tuple[list[dict], list[dict], str, int]:
    """Extract media and dividers with their block index positions.

    Returns:
        (media_list, divider_list, markdown_without_media_and_dividers, total_blocks)
    """
    blocks = split_into_blocks(markdown)
    media_items = []
    dividers = []
    clean_blocks = []

    img_pattern = re.compile(r'^!\[([^\]]*)\]\(([^)]+)\)$')
    link_pattern = re.compile(r'^\[([^\]]*)\]\(([^)]+)\)$')
    html_video_src_pattern = re.compile(r'^<video[^>]*src=["\']([^"\']+)["\'][^>]*>.*</video>$', re.IGNORECASE | re.DOTALL)
    html_video_source_pattern = re.compile(r'^<video[^>]*>.*?<source[^>]*src=["\']([^"\']+)["\'][^>]*>.*</video>$', re.IGNORECASE | re.DOTALL)

    for i, block in enumerate(blocks):
        _ = i  # keep loop shape stable; index not needed directly
        block_stripped = block.strip()

        # Check for divider
        if block_stripped == '___DIVIDER___':
            block_index = len(clean_blocks)
            after_text = ""
            if clean_blocks:
                prev_block = clean_blocks[-1].strip()
                lines = [l for l in prev_block.split('\n') if l.strip()]
                after_text = lines[-1][:80] if lines else ""
            dividers.append({
                "block_index": block_index,
                "after_text": after_text
            })
            continue

        media_path = None
        alt_text = ""

        img_match = img_pattern.match(block_stripped)
        if img_match:
            alt_text = img_match.group(1)
            media_path = img_match.group(2)
        else:
            html_video_match = html_video_src_pattern.match(block_stripped)
            if html_video_match:
                media_path = html_video_match.group(1)
            else:
                html_video_source_match = html_video_source_pattern.match(block_stripped)
                if html_video_source_match:
                    media_path = html_video_source_match.group(1)
                else:
                    link_match = link_pattern.match(block_stripped)
                    if link_match:
                        candidate = link_match.group(2)
                        if media_type_for_path(candidate) == "video":
                            alt_text = link_match.group(1)
                            media_path = candidate

        if media_path is not None:
            media_type = media_type_for_path(media_path)
            decoded_path = urllib.parse.unquote(media_path)

            if is_remote_path(decoded_path):
                full_path = decoded_path
                exists = False
                print(
                    f"[parse_markdown] WARNING: Remote {media_type} URL not uploadable directly: '{decoded_path}'",
                    file=sys.stderr
                )
            else:
                if not os.path.isabs(decoded_path):
                    resolved_path = str(base_path / decoded_path)
                else:
                    resolved_path = decoded_path

                filename = os.path.basename(decoded_path)
                full_path, exists = find_media_file(resolved_path, filename, media_type)

            block_index = len(clean_blocks)

            after_text = ""
            if clean_blocks:
                prev_block = clean_blocks[-1].strip()
                lines = [l for l in prev_block.split('\n') if l.strip()]
                after_text = lines[-1][:80] if lines else ""

            media_items.append({
                "type": media_type,
                "path": full_path,
                "original_path": decoded_path if is_remote_path(decoded_path) else resolved_path,
                "exists": exists,
                "alt": alt_text,
                "block_index": block_index,
                "after_text": after_text
            })
        else:
            clean_blocks.append(block)

    clean_markdown = '\n\n'.join(clean_blocks)
    return media_items, dividers, clean_markdown, len(clean_blocks)


def extract_title(markdown: str) -> tuple[str, str]:
    """Extract title from first H1, H2, or first non-empty line.

    Returns:
        (title, markdown_without_title): Title string and markdown with H1 title removed.
        If title is from H1, it's removed from markdown to avoid duplication.
    """
    lines = markdown.strip().split('\n')
    title = "Untitled"
    title_line_idx = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # H1 - use as title and mark for removal
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            title_line_idx = idx
            break
        # H2 - use as title but don't remove (it's a section header)
        if stripped.startswith('## '):
            title = stripped[3:].strip()
            break
        # First non-empty, non-image line
        if not stripped.startswith('!['):
            title = stripped[:100]
            break

    # Remove H1 title line from markdown to avoid duplication
    if title_line_idx is not None:
        lines.pop(title_line_idx)
        markdown = '\n'.join(lines)

    return title, markdown


def markdown_to_html(markdown: str) -> str:
    """Convert markdown to HTML for X Articles rich text paste."""
    html = markdown

    # Process code blocks first (marked with ___CODE_BLOCK_START___ and ___CODE_BLOCK_END___)
    # Convert to blockquote format since X Articles doesn't support <pre><code>
    def convert_code_block(match):
        code_content = match.group(1)
        lines = code_content.strip().split('\n')
        # Join non-empty lines with <br> for display
        formatted = '<br>'.join(line for line in lines if line.strip())
        return f'<blockquote>{formatted}</blockquote>'

    html = re.sub(r'___CODE_BLOCK_START___(.*?)___CODE_BLOCK_END___', convert_code_block, html, flags=re.DOTALL)

    # Headers (H2 only, H1 is title)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Italic
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Blockquotes / callouts:
    # - Merge contiguous quote lines into one blockquote
    # - Drop admonition markers like [!TIP], [!NOTE], etc.
    # - Preserve multiline content with <br>
    callout_marker = re.compile(r'^\s*\[![A-Z]+\]\s*$', re.IGNORECASE)

    def convert_blockquote_group(match):
        group = match.group(0)
        raw_lines = group.splitlines()
        lines = []
        for raw in raw_lines:
            # Remove leading ">" and one optional space
            text = re.sub(r'^\s*>\s?', '', raw).rstrip()
            if callout_marker.match(text):
                continue
            lines.append(text)

        # Trim empty lines on both ends, keep internal blank lines
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return ""
        return f"<blockquote>{'<br>'.join(lines)}</blockquote>"

    html = re.sub(
        r'(?m)(?:^\s*>.*(?:\n|$))+',
        convert_blockquote_group,
        html,
    )

    # Unordered lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Ordered lists
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Wrap consecutive <li> in <ul>
    html = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\1</ul>', html)

    # Paragraphs - split by double newlines
    parts = html.split('\n\n')
    processed_parts = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Skip if already a block element
        if part.startswith(('<h2>', '<h3>', '<blockquote>', '<ul>', '<ol>')):
            processed_parts.append(part)
        else:
            # Wrap in paragraph, convert single newlines to <br>
            part = part.replace('\n', '<br>')
            processed_parts.append(f'<p>{part}</p>')

    return ''.join(processed_parts)


def parse_markdown_file(filepath: str) -> dict:
    """Parse a markdown file and return structured data."""
    path = Path(filepath)
    base_path = path.parent

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip YAML frontmatter if present
    if content.startswith('---'):
        end_marker = content.find('---', 3)
        if end_marker != -1:
            content = content[end_marker + 3:].strip()

    # Extract title first (and remove H1 from markdown)
    title, content = extract_title(content)

    # Extract media and dividers with block indices
    media_items, dividers, clean_markdown, total_blocks = extract_media_and_dividers(content, base_path)

    # Convert to HTML
    html = markdown_to_html(clean_markdown)

    cover_idx = next((idx for idx, item in enumerate(media_items) if item["type"] == "image"), None)
    if cover_idx is not None:
        cover_image = media_items[cover_idx]["path"]
        cover_exists = media_items[cover_idx]["exists"]
    else:
        cover_image = None
        cover_exists = True

    if cover_idx is None:
        content_media = media_items
    else:
        content_media = [item for idx, item in enumerate(media_items) if idx != cover_idx]

    content_images = [item for item in content_media if item["type"] == "image"]
    content_videos = [item for item in content_media if item["type"] == "video"]

    missing_media = [item for item in media_items if not item["exists"]]
    missing_images = [item for item in media_items if item["type"] == "image" and not item["exists"]]
    missing_videos = [item for item in media_items if item["type"] == "video" and not item["exists"]]
    if missing_media:
        print(f"[parse_markdown] WARNING: {len(missing_media)} media file(s) not found", file=sys.stderr)

    return {
        "title": title,
        "cover_image": cover_image,
        "cover_exists": cover_exists,
        "content_media": content_media,
        "content_images": content_images,
        "content_videos": content_videos,
        "dividers": dividers,
        "html": html,
        "total_blocks": total_blocks,
        "source_file": str(path.absolute()),
        "missing_media": len(missing_media),
        "missing_images": len(missing_images),
        "missing_videos": len(missing_videos)
    }


def main():
    parser = argparse.ArgumentParser(description='Parse Markdown for X Articles')
    parser.add_argument('file', help='Markdown file to parse')
    parser.add_argument('--output', choices=['json', 'html'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--html-only', action='store_true',
                       help='Output only HTML content')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = parse_markdown_file(args.file)

    if args.html_only:
        print(result['html'])
    elif args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['html'])


if __name__ == '__main__':
    main()
