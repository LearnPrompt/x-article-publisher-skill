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

## Requirements

- X Premium Plus (Articles enabled)
- Playwright MCP
- Python 3.9+
- `feishu2md` for Feishu source mode
- macOS deps: `pip install Pillow pyobjc-framework-Cocoa`
- Windows deps: `pip install Pillow pywin32 clip-util`

## Install

```bash
git clone https://github.com/LearnPrompt/x-article-publisher-skill.git
cp -r x-article-publisher-skill/skills/x-article-publisher "$CODEX_HOME/skills/"
```

`$CODEX_HOME` is typically `~/.codex`.

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
