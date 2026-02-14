# GUIDE

## Overview

This skill publishes Markdown content to X Articles drafts with:

- Feishu URL source mode (download + media recovery)
- Local Markdown source mode (direct publish)
- Persistent X login profile
- Image + video insertion

## Source Modes

### 1) Feishu URL mode

Input contains `feishu.cn` / `larksuite.com` / `feishu.sg` URL.

Flow:
1. `prepare_article_source.py` calls `feishu2md dl --dump`
2. Parses dump JSON for video file blocks
3. Downloads video files into local `static/`
4. Inserts video markdown near related anchor text
5. Returns normalized local markdown path

### 2) Local Markdown mode

Input is `.md` / `.markdown` local file path.

Flow:
1. Skip download
2. Parse and publish directly

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
