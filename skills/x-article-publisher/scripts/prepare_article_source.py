#!/usr/bin/env python3
"""
Prepare article source for X publishing.

Modes:
1) Feishu/Lark URL -> download markdown via feishu2md, fetch video file blocks, append <video> tags
2) Local markdown path -> passthrough
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
    ".avi",
    ".mkv",
    ".mpeg",
    ".mpg",
}


def is_feishu_url(source: str) -> bool:
    return bool(
        re.match(
            r"^https?://[^/]*(feishu\.cn|larksuite\.com|feishu\.sg|feishu\.com)/",
            source.strip(),
            flags=re.IGNORECASE,
        )
    )


def get_feishu2md_config_path() -> Optional[Path]:
    candidates = [
        Path.home() / "Library/Application Support/feishu2md/config.json",  # macOS
        Path.home() / ".config/feishu2md/config.json",  # Linux
        Path.home() / "AppData/Roaming/feishu2md/config.json",  # Windows
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def get_feishu_credentials() -> tuple[str, str]:
    app_id = os.environ.get("FEISHU_APP_ID", "").strip()
    app_secret = os.environ.get("FEISHU_APP_SECRET", "").strip()
    if app_id and app_secret:
        return app_id, app_secret

    cfg_path = get_feishu2md_config_path()
    if cfg_path is None:
        raise RuntimeError(
            "Feishu credentials not found. Set FEISHU_APP_ID/FEISHU_APP_SECRET "
            "or run feishu2md config first."
        )

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    app_id = (cfg.get("feishu") or {}).get("app_id", "").strip()
    app_secret = (cfg.get("feishu") or {}).get("app_secret", "").strip()
    if not app_id or not app_secret:
        raise RuntimeError(
            f"Feishu credentials missing in config: {cfg_path}. "
            "Set FEISHU_APP_ID/FEISHU_APP_SECRET or reconfigure feishu2md."
        )
    return app_id, app_secret


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("code") != 0 or not data.get("tenant_access_token"):
        raise RuntimeError(f"Failed to get tenant access token: {data}")
    return data["tenant_access_token"]


def run_feishu2md_download(source_url: str, output_dir: Path) -> None:
    cmd = ["feishu2md", "dl", "--dump", "-o", str(output_dir), source_url]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "feishu2md download failed.\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def newest_file(root: Path, suffix: str) -> Optional[Path]:
    files = [p for p in root.glob(f"*{suffix}") if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def is_video_filename(filename: str) -> bool:
    clean = filename.split("?", 1)[0].split("#", 1)[0]
    return Path(clean).suffix.lower() in VIDEO_EXTENSIONS


def extract_text_from_block(block: dict) -> str:
    """Best-effort plain text extraction for text-like blocks."""
    if not isinstance(block, dict):
        return ""

    text_keys = [
        "text",
        "heading1",
        "heading2",
        "heading3",
        "heading4",
        "heading5",
        "heading6",
        "heading7",
        "heading8",
        "heading9",
        "quote",
        "todo",
        "equation",
        "page",
    ]
    parts = []
    for key in text_keys:
        node = block.get(key)
        if not isinstance(node, dict):
            continue
        elems = node.get("elements") or []
        for elem in elems:
            text_run = (elem or {}).get("text_run") or {}
            content = text_run.get("content")
            if content:
                parts.append(content)
        if parts:
            break
    return "".join(parts).strip().replace("\n", " ")


def extract_video_file_tokens(dump_json_path: Path) -> list[dict]:
    """Fallback extractor by flat block list order (kept for compatibility)."""
    data = json.loads(dump_json_path.read_text(encoding="utf-8"))
    blocks = data.get("blocks") or []
    videos = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if int(block.get("block_type", -1)) != 23:  # file block
            continue
        file_obj = block.get("file") or {}
        token = (file_obj.get("token") or "").strip()
        name = (file_obj.get("name") or "").strip()
        if not token:
            continue
        if name and is_video_filename(name):
            videos.append({"token": token, "name": name})
    return videos


def extract_video_file_tokens_with_anchor(dump_json_path: Path) -> list[dict]:
    """Extract video file blocks in root order and attach nearby text anchor."""
    data = json.loads(dump_json_path.read_text(encoding="utf-8"))
    blocks = data.get("blocks") or []
    document = data.get("document") or {}
    root_id = document.get("document_id")
    if not root_id:
        return extract_video_file_tokens(dump_json_path)

    block_map = {b.get("block_id"): b for b in blocks if isinstance(b, dict) and b.get("block_id")}
    root_block = block_map.get(root_id) or {}
    root_children = root_block.get("children") or []

    videos = []
    for idx, bid in enumerate(root_children):
        block = block_map.get(bid) or {}
        if int(block.get("block_type", -1)) != 33:  # view block
            continue
        child_ids = block.get("children") or []
        if not child_ids:
            continue
        child_block = block_map.get(child_ids[0]) or {}
        if int(child_block.get("block_type", -1)) != 23:  # file block
            continue

        file_obj = child_block.get("file") or {}
        token = (file_obj.get("token") or "").strip()
        name = (file_obj.get("name") or "").strip()
        if not token or not name or not is_video_filename(name):
            continue

        anchor_text = ""
        # Backward search: nearest previous text-like block
        for j in range(idx - 1, -1, -1):
            prev_block = block_map.get(root_children[j]) or {}
            anchor_text = extract_text_from_block(prev_block)
            if anchor_text:
                break
        # Fallback forward search
        if not anchor_text:
            for j in range(idx + 1, len(root_children)):
                nxt_block = block_map.get(root_children[j]) or {}
                anchor_text = extract_text_from_block(nxt_block)
                if anchor_text:
                    break

        videos.append(
            {
                "token": token,
                "name": name,
                "root_index": idx,
                "anchor_text": anchor_text[:120],
            }
        )
    return videos


def parse_filename_from_headers(headers, fallback_name: str) -> str:
    filename = ""
    content_disposition = headers.get("Content-Disposition", "")
    if content_disposition:
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition, re.IGNORECASE)
        if match:
            filename = urllib.parse.unquote(match.group(1).strip())
    if not filename:
        filename = fallback_name
    return filename or "video.mp4"


def download_media_file(file_token: str, bearer_token: str, output_dir: Path, fallback_name: str) -> Path:
    url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{file_token}/download"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {bearer_token}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        real_name = parse_filename_from_headers(resp.headers, fallback_name)
        ext = Path(real_name).suffix.lower() or ".mp4"
        output_path = output_dir / f"{file_token}{ext}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.read())
    return output_path


def insert_block_after_anchor(content: str, block_markdown: str, anchor_text: str, search_start: int) -> tuple[str, int]:
    """Insert markdown block after paragraph containing anchor text; fallback append."""
    anchor = (anchor_text or "").strip()
    pos = -1
    if anchor:
        # Try progressive shorter anchors to increase hit rate on punctuation/spacing differences.
        candidates = [anchor, anchor[:60], anchor[:40], anchor[:24]]
        tried = set()
        for c in candidates:
            c = c.strip()
            if not c or c in tried:
                continue
            tried.add(c)
            pos = content.find(c, search_start)
            if pos != -1:
                break
        if pos == -1:
            for c in candidates:
                c = c.strip()
                if not c:
                    continue
                pos = content.find(c)
                if pos != -1:
                    break

    if pos == -1:
        pos = len(content)
        prefix = content.rstrip("\n")
        suffix = ""
    else:
        block_end = content.find("\n\n", pos)
        if block_end == -1:
            block_end = len(content)
        pos = block_end
        prefix = content[:pos].rstrip("\n")
        suffix = content[pos:].lstrip("\n")

    inserted = f"{prefix}\n\n{block_markdown}\n\n{suffix}"
    new_start = inserted.find(block_markdown, max(0, search_start))
    if new_start == -1:
        new_start = pos
    else:
        new_start += len(block_markdown)
    return inserted, new_start


def insert_videos_to_markdown(md_path: Path, video_items: list[dict], token_to_path: dict[str, Path]) -> int:
    if not video_items:
        return 0

    content = md_path.read_text(encoding="utf-8")
    inserted_count = 0
    cursor = 0

    for item in sorted(video_items, key=lambda x: x.get("root_index", 0)):
        token = item.get("token", "")
        path = token_to_path.get(token)
        if not path:
            continue
        rel = path.relative_to(md_path.parent).as_posix()
        block_md = f'<video src="{rel}"></video>'
        if rel in content:
            continue
        anchor_text = item.get("anchor_text", "")
        content, cursor = insert_block_after_anchor(content, block_md, anchor_text, cursor)
        inserted_count += 1

    md_path.write_text(content, encoding="utf-8")
    return inserted_count


def ensure_executable_exists(name: str) -> None:
    proc = subprocess.run(f"command -v {name}", shell=True, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Required command not found: {name}")


def prepare_from_feishu_url(source: str, output_root: Optional[Path]) -> dict:
    ensure_executable_exists("feishu2md")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workdir = output_root or Path("/tmp") / f"x_article_feishu_{ts}"
    workdir.mkdir(parents=True, exist_ok=True)

    run_feishu2md_download(source, workdir)

    md_path = newest_file(workdir, ".md")
    dump_path = newest_file(workdir, ".json")
    if md_path is None:
        raise RuntimeError(f"No markdown generated by feishu2md in: {workdir}")
    if dump_path is None:
        raise RuntimeError(f"No dump json generated by feishu2md in: {workdir}")

    video_blocks = extract_video_file_tokens_with_anchor(dump_path)
    static_dir = workdir / "static"
    downloaded_video_paths = []
    token_to_local_path = {}
    download_errors = []

    if video_blocks:
        app_id, app_secret = get_feishu_credentials()
        bearer = get_tenant_access_token(app_id, app_secret)
        for item in video_blocks:
            try:
                path = download_media_file(
                    file_token=item["token"],
                    bearer_token=bearer,
                    output_dir=static_dir,
                    fallback_name=item.get("name") or "video.mp4",
                )
                downloaded_video_paths.append(path)
                token_to_local_path[item["token"]] = path
            except urllib.error.HTTPError as e:
                download_errors.append(f"{item['token']}: HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                download_errors.append(f"{item['token']}: {e}")

    appended_count = insert_videos_to_markdown(md_path, video_blocks, token_to_local_path)

    return {
        "mode": "feishu_url",
        "source": source,
        "workdir": str(workdir),
        "markdown_path": str(md_path),
        "dump_json_path": str(dump_path),
        "video_tokens_found": len(video_blocks),
        "videos_downloaded": len(downloaded_video_paths),
        "videos_appended": appended_count,
        "video_download_errors": download_errors,
    }


def prepare_from_local_markdown(source: str) -> dict:
    md_path = Path(source).expanduser().resolve()
    if not md_path.exists():
        raise RuntimeError(f"Local markdown not found: {md_path}")
    if md_path.suffix.lower() not in {".md", ".markdown"}:
        raise RuntimeError(f"Input is not a markdown file: {md_path}")
    return {
        "mode": "local_markdown",
        "source": source,
        "workdir": str(md_path.parent),
        "markdown_path": str(md_path),
        "video_tokens_found": 0,
        "videos_downloaded": 0,
        "videos_appended": 0,
        "video_download_errors": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare article source for x-article-publisher")
    parser.add_argument("source", help="Feishu URL or local markdown path")
    parser.add_argument(
        "--output-root",
        default=None,
        help="Output directory for Feishu downloads (default: /tmp/x_article_feishu_<timestamp>)",
    )
    args = parser.parse_args()

    try:
        if is_feishu_url(args.source):
            out_root = Path(args.output_root).expanduser().resolve() if args.output_root else None
            result = prepare_from_feishu_url(args.source, out_root)
        else:
            result = prepare_from_local_markdown(args.source)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
