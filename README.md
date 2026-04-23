# X Article Publisher Skill (Feishu + Video + Persistent Login)

> Publish Feishu or local Markdown to X Articles drafts with full media support (images + videos) and a persistent logged-in browser profile.

## Why this fork

1. **Video support end-to-end**
- Handles both images and videos in article body.
- Adds missing Feishu video download handling on top of `feishu2md`.

2. **Persistent X login session**
- Uses a dedicated persistent browser profile.
- Avoids repeated high-risk logins.

3. **One-pass workflow**
- Feishu URL: download markdown (with videos) -> parse -> upload to X draft.
- Local markdown path: skip download -> parse -> upload to X draft.
- Draft-only by default (no auto publish).

## Field-tested updates

- Feishu Wiki URLs (`/wiki/...`) are downloaded with `feishu2md dl --dump --wiki`.
- Feishu video file blocks are inserted back into Markdown near their text anchors instead of being appended at the end.
- Missing or 0-byte video downloads are retried; empty video files are not sent to X.
- X video uploads must be serialized: upload one video, wait until `Uploading media...` disappears, then continue with the next media block.

## Requirements

- X Premium Plus (Articles enabled)
- Playwright MCP
- Python 3.9+
- `feishu2md` for Feishu source mode
- macOS deps: `pip install Pillow pyobjc-framework-Cocoa`
- Windows deps: `pip install Pillow pywin32 clip-util`

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

Manual install:

```bash
git clone https://github.com/LearnPrompt/x-article-publisher-skill.git
bash x-article-publisher-skill/install.sh
```

`$CODEX_HOME` defaults to `~/.codex` when not set.

## Usage

- Feishu source:

```text
Publish this Feishu doc to X draft: https://aiwarts101.feishu.cn/docx/...
```

- Local markdown source:

```text
Publish /path/to/article.md to X draft
```

## Repository layout

```text
x-article-publisher-skill/
├── .claude-plugin/plugin.json
├── docs/GUIDE.md
├── skills/x-article-publisher/
│   ├── SKILL.md
│   └── scripts/
│       ├── copy_to_clipboard.py
│       ├── parse_markdown.py
│       ├── prepare_article_source.py
│       ├── open_x_articles_browser.sh
│       └── table_to_image.py
├── README.md
└── README_CN.md
```

## Credits

- Feishu extraction baseline: [Wsine/feishu2md](https://github.com/Wsine/feishu2md)
- Initial skill packaging inspiration: [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)
