# X Article Publisher Skill

> Publish Feishu/Lark documents or local Markdown to X Articles drafts, with images, videos, and a persistent logged-in X profile.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Skills](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh) [![X Articles](https://img.shields.io/badge/X-Articles-black)](https://x.com/compose/articles)

**This skill turns a Feishu document into a ready-to-review X Article draft.**

It downloads the document to Markdown, restores missing Feishu video blocks, keeps video order aligned with the original article, parses local images/videos, opens X with a persistent browser profile, and uploads everything into a draft. It never auto-publishes.

**Languages:** [中文](README_CN.md) · English

---

## What It Solves

| Problem | What this skill does |
|---|---|
| Feishu exports often miss videos | Reads Feishu dump JSON, downloads video file blocks, and writes `<video>` tags back into Markdown near the right anchor text |
| Videos can appear at the end of the article | Uses anchor-based insertion and whitespace-tolerant matching instead of appending videos to the tail |
| Repeated X login is risky | Uses a dedicated persistent browser profile, isolated from your daily Chrome profile |
| Local Markdown should also work | Skips Feishu download and directly parses local image/video paths |
| X video upload is fragile | Uploads one video at a time and waits for `Uploading media...` to finish before continuing |

---

## Install

### Option A: Full Codex Setup Recommended

This installs the skill into `~/.codex/skills/x-article-publisher`, installs Python dependencies, primes Playwright MCP, and tries to install `feishu2md` with Homebrew when available.

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

Manual clone:

```bash
git clone https://github.com/LearnPrompt/x-article-publisher-skill.git
bash x-article-publisher-skill/install.sh
```

Skip dependency installation if you only want to copy the skill files:

```bash
INSTALL_DEPS=0 bash x-article-publisher-skill/install.sh
```

### Option B: skills.sh / Claude Code Compatible Install

The repository is discoverable by the `skills` CLI:

```bash
npx skills add LearnPrompt/x-article-publisher-skill --skill x-article-publisher --global --copy --yes --full-depth
```

Important: `skills add` installs the skill files only. Runtime dependencies still need to be installed in your environment. For Codex, the full setup script above is the simplest path.

### Check Your Environment

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh
```

For local Markdown only:

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh local
```

---

## Required Accounts And Tools

| Mode | Required |
|---|---|
| Feishu URL -> X draft | X Premium Plus, Python 3.9+, Node.js/npm, `feishu2md`, Feishu app credentials (App ID / App Secret), one-time X login |
| Local Markdown -> X draft | X Premium Plus, Python 3.9+, Node.js/npm, one-time X login |

### Install feishu2md

`feishu2md` is the upstream Feishu/Lark-to-Markdown exporter used by this skill before video recovery.

macOS or Linux with Homebrew:

```bash
brew install feishu2md
```

Manual install:
- Download the binary from [Wsine/feishu2md releases](https://github.com/Wsine/feishu2md/releases).
- Put the `feishu2md` executable somewhere on your `PATH`.
- Verify it works:

```bash
feishu2md -h
```

References:
- [feishu2md GitHub README](https://github.com/Wsine/feishu2md)
- [Homebrew formula: feishu2md](https://formulae.brew.sh/formula/feishu2md)

### Configure Feishu/Lark App Credentials

Configure Feishu app credentials for Feishu URL mode:

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

What this means:
- The App ID and App Secret come from a Feishu/Lark custom app that you create in the Feishu developer console.
- They are not your Feishu login password.
- `feishu2md` uses them to call Feishu APIs and download the document, images, and files/videos that the shared document allows the app to read.
- The app needs permissions for document read and media/file download. Wiki links also need wiki read permission.

Where to create the app:
- Feishu: [open.feishu.cn/app](https://open.feishu.cn/app)
- Lark: [open.larksuite.com/app](https://open.larksuite.com/app)

Minimum permissions to add in the app's permission management page:

| Permission | Why it is needed |
|---|---|
| `docx:document:readonly` | Read Feishu Docs content and blocks |
| `docs:document.media:download` | Download images and file/video assets from Docs |
| `drive:file:readonly` | Read cloud drive files/folders referenced by the document |
| `wiki:wiki:readonly` | Required for `/wiki/` links |

Useful official/API references:
- [Get document basic info](https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/get)
- [Get document blocks](https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list)
- [Download media](https://open.feishu.cn/document/server-docs/docs/drive-v1/media/download)
- [Get wiki node info](https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/get_node)

Environment variables are also supported:

```bash
export FEISHU_APP_ID=<your_app_id>
export FEISHU_APP_SECRET=<your_app_secret>
```

After configuration, you can test `feishu2md` directly:

```bash
feishu2md dl --dump -o /tmp/feishu2md-test "https://your-domain.feishu.cn/docx/..."
```

---

## Try It

### Feishu/Lark Source

Ask your agent:

```text
Publish this Feishu doc to X draft: https://your-domain.feishu.cn/docx/...
```

Chinese prompt:

```text
把这个飞书文档发布到 X 草稿：https://your-domain.feishu.cn/docx/...
```

### Local Markdown Source

```text
Publish /path/to/article.md to X draft
```

Chinese prompt:

```text
把 /path/to/article.md 发布到 X 草稿
```

Supported local media syntax:

```markdown
![cover](./static/cover.png)

<video src="./static/demo.mp4"></video>

[video](./static/clip.mp4)
```

Relative paths are resolved from the Markdown file directory.

---

## How It Works

1. **Source routing**: Feishu URL triggers download; local Markdown skips download.
2. **Feishu recovery**: `feishu2md dl --dump` exports Markdown and JSON; `/wiki/` links use `--wiki`.
3. **Video restoration**: Feishu file blocks are downloaded from OpenAPI and inserted back near text anchors.
4. **Markdown parsing**: title, cover, HTML body, images, videos, dividers, and block positions are extracted.
5. **Persistent X browser**: X opens with `~/.codex/browser-profiles/x-articles` unless overridden.
6. **Draft assembly**: cover first, title, rich-text body, then media/dividers by descending block index.
7. **Video safety**: one video upload at a time; wait for X upload overlay to disappear.

Full framework: [docs/GUIDE.md](docs/GUIDE.md)

---

## Honest Limits

- The skill creates X Article drafts; it does not auto-publish.
- X Articles requires an account with Articles access, usually X Premium Plus.
- First use of the persistent profile may still require manual X login or security verification.
- Remote image/video URLs are detected but not treated as reliable uploadable local files. Keep media local for deterministic uploads.
- Feishu URL mode depends on a Feishu custom app with document read, media download, and wiki read permissions for `/wiki/` links.
- Large videos can take minutes to process on X; interruption may leave a partial draft.

---

## Repository Structure

```text
x-article-publisher-skill/
├── install.sh
├── README.md
├── README_CN.md
├── docs/
│   ├── GUIDE.md
│   └── GUIDE_CN.md
├── skills/x-article-publisher/
│   ├── SKILL.md
│   ├── requirements.txt
│   └── scripts/
│       ├── copy_to_clipboard.py
│       ├── doctor.sh
│       ├── open_x_articles_browser.sh
│       ├── parse_markdown.py
│       ├── prepare_article_source.py
│       └── table_to_image.py
└── .claude-plugin/plugin.json
```

---

## Credits

- Feishu Markdown baseline: [Wsine/feishu2md](https://github.com/Wsine/feishu2md)
- Skill packaging inspiration: [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)

## License

MIT. Use it, modify it, and adapt it to your publishing workflow.
