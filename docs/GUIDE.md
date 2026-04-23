# GUIDE

## Overview

This skill publishes Markdown content to X Articles drafts with:

- Feishu URL source mode (download + media recovery)
- Local Markdown source mode (direct publish)
- Persistent X login profile
- Image + video insertion

## Source Modes

### 1) Feishu URL mode

Input contains `feishu.cn` / `larksuite.com` / `feishu.sg` URL, including `/docx/` and `/wiki/` links.

Flow:
1. `prepare_article_source.py` calls `feishu2md dl --dump`; for `/wiki/` links it adds `--wiki`
2. Parses dump JSON for video file blocks
3. Downloads video files into local `static/`, retrying missing or 0-byte files
4. Inserts video markdown near related anchor text; anchor failures are reported instead of appended to the end
5. Returns normalized local markdown path

### 2) Local Markdown mode

Input is `.md` / `.markdown` local file path.

Flow:
1. Skip download
2. Parse local images and videos from Markdown
3. Publish directly

Supported local media syntax:
- Images: `![alt](./static/image.png)`
- Videos: `<video src="./static/clip.mp4"></video>`
- Videos: `<video><source src="./static/clip.mp4"></video>`
- Videos: `[video](./static/clip.mp4)`

Remote `http(s)` media URLs are reported as not uploadable local files. Keep the reliable path as local files next to the Markdown.

## Installation And Environment

Install:

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

The installer copies the skill, installs Python packages from `requirements.txt`, primes Playwright MCP through `npx`, and tries `brew install feishu2md` when Homebrew is present.

Skip dependency installation:

```bash
INSTALL_DEPS=0 bash install.sh
```

Check environment:

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh
```

Feishu URL mode additionally needs credentials:

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

Or set `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.

## Persistent Login

Use:

```bash
bash ~/.codex/skills/x-article-publisher/scripts/open_x_articles_browser.sh
```

Default profile path:

```text
~/.codex/browser-profiles/x-articles
```

This profile is isolated from your main Chrome profile and minimizes repeated login challenges.

## Publish Pipeline

1. Resolve source with `prepare_article_source.py`
2. Parse markdown with `parse_markdown.py`
3. Upload cover image
4. Fill title
5. Paste HTML body
6. Insert content images by `block_index` (desc)
7. Insert content videos by `block_index` (desc)
8. Save draft only

## Troubleshooting

### Videos missing from Feishu export

- Ensure `feishu2md` works (`feishu2md dl --dump ...`)
- Ensure Feishu app credentials are available:
  - env: `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
  - or `feishu2md` config file

### X login expired

- Reopen with persistent profile script
- Complete one-time login challenge manually
- Reuse same profile path afterward

### Media file not found

- Check parse output fields: `missing_media`, `missing_images`, `missing_videos`
- Confirm files exist under downloaded folder `static/`
- For local Markdown, keep media paths relative to the Markdown file directory or use absolute local paths

## Runbook Notes (2026-02-21)

### 1) Login-state gate before publishing

- Check cookies in persistent profile first.
- If `auth_token` and `ct0` are missing, stop automation and request manual login.
- Symptom of missing login: `https://x.com/compose/articles` shows `Page not found / X` with `Log in`.

### 2) Upload root restriction

- `playwright-cli upload` may reject files outside allowed roots.
- Symptom: `File access denied ... outside allowed roots`.
- Mitigation: copy Feishu download output into the active workspace (for example `~/Downloads/...`) before upload.

### 3) Media insertion reliability

- Insert media in descending `block_index` order.
- Primary locator: `after_text`.
- Fallback locator: shortened keyword extracted from `after_text` if exact match fails.

### 4) Re-run safety

- Prefer creating a fresh draft when re-running the same article.
- If reusing a draft, record inserted images and skip existing ones to avoid duplicates.

## Runbook Notes (2026-04-23)

### 1) Wiki documents

- Wiki URLs can download successfully only after adding the `feishu2md --wiki` flag.
- Use the generated Markdown and dump JSON from the underlying document token.

### 2) Video anchor correctness

- Do not append videos to the article tail when a text anchor cannot be found.
- Normalize whitespace when matching Feishu dump text to Markdown text; Feishu often omits spaces around English tokens in dump JSON while `feishu2md` inserts them in Markdown.
- Verify `parse_markdown.py` reports videos with sensible `after_text` before opening X.

### 3) X video upload serialization

- X shows an `Uploading media...` overlay for video processing.
- That overlay intercepts subsequent clicks, so only one video upload should be active at a time.
- Wait until the overlay disappears before inserting the next media block.
