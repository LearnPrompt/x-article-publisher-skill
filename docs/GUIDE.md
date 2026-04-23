# X Article Publisher Framework

This document explains the runtime framework behind `x-article-publisher`. It is written for users who want to understand, debug, or adapt the workflow.

Chinese version: [GUIDE_CN.md](GUIDE_CN.md)

---

## 1. Source Framework

The skill has two source modes.

| Source | Trigger | First step | Media strategy |
|---|---|---|---|
| Feishu/Lark URL | URL contains `feishu.cn`, `larksuite.com`, `feishu.sg`, or `feishu.com` | Download to local Markdown with `prepare_article_source.py` | Recover videos from Feishu dump JSON, then parse local Markdown |
| Local Markdown | Local `.md` or `.markdown` path | Use the file directly | Parse local images/videos from Markdown |

### Feishu URL Mode

1. Call `feishu2md dl --dump -o <workdir> <url>`.
2. If the URL contains `/wiki/`, add `--wiki`.
3. Find the generated Markdown and dump JSON.
4. Extract video file blocks from dump JSON.
5. Download video files from Feishu OpenAPI into `static/`.
6. Insert `<video src="static/...">` blocks near source text anchors.
7. Return the local Markdown path.

### Local Markdown Mode

1. Validate the file exists and has `.md` or `.markdown` suffix.
2. Return the original file path.
3. Let `parse_markdown.py` resolve local image/video paths relative to the Markdown directory.

Supported local video syntax:

```markdown
<video src="./static/demo.mp4"></video>
<video><source src="./static/demo.mp4"></video>
[video](./static/demo.mp4)
```

Remote `http(s)` media URLs are detected but not treated as reliable uploadable files.

---

## 2. Environment Framework

There are two installation paths.

### Full Codex Setup

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

The script:

1. Installs the skill to `$CODEX_HOME/skills/x-article-publisher`.
2. Installs Python packages from `skills/x-article-publisher/requirements.txt`.
3. Primes `@playwright/mcp` when `npx` is available.
4. Tries `brew install feishu2md` when Homebrew is available.
5. Prints the `doctor.sh` command for verification.

### skills.sh Compatible Setup

```bash
npx skills add LearnPrompt/x-article-publisher-skill --skill x-article-publisher --global --copy --yes --full-depth
```

This installs skill files only. It does not install runtime dependencies, so users still need Python packages, Playwright MCP, and `feishu2md` for Feishu mode.

### Doctor Checks

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh local
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh feishu
```

The doctor script checks Python, clipboard dependencies, Playwright CLI availability, `feishu2md`, Feishu app credentials, and the X persistent profile path.

---

## 3. Browser Framework

X is opened through `open_x_articles_browser.sh`.

Resolution order:

1. Use Codex Playwright wrapper if available: `$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh`.
2. Use `playwright-cli` from `PATH`.
3. Use `npx --yes --package @playwright/mcp playwright-cli`.

Default profile:

```text
~/.codex/browser-profiles/x-articles
```

Override with:

```bash
export X_ARTICLES_PROFILE=/custom/profile/path
```

This profile is separate from the user's daily Chrome profile. It avoids repeated X logins while not overwriting the user's existing browser session.

---

## 4. Markdown Parsing Framework

`parse_markdown.py` extracts:

- title
- cover image, defined as the first image
- body HTML for rich-text paste
- `content_media`, a unified ordered list of images and videos
- `content_images` and `content_videos` for compatibility
- dividers from `---`
- `block_index` and `after_text` for insertion positioning
- missing media counts

Media insertion uses descending `block_index` so earlier insertions do not shift later targets.

---

## 5. X Draft Assembly Framework

The publishing workflow should follow this order:

1. Resolve source with `prepare_article_source.py`.
2. Parse Markdown with `parse_markdown.py`.
3. Open X Articles with persistent profile.
4. Upload cover image.
5. Fill title.
6. Paste HTML body via clipboard.
7. Insert content images by descending `block_index`.
8. Insert content videos by descending `block_index`.
9. Insert dividers by descending `block_index`.
10. Save draft only.

Do not auto-publish.

---

## 6. Video Ordering Framework

Feishu often represents embedded videos as file blocks, while `feishu2md` focuses on image tokens. The extra recovery step is therefore required.

The skill keeps order by:

1. Reading root block order from Feishu dump JSON.
2. Finding the nearest text-like block around each video.
3. Using that text as an anchor.
4. Matching the anchor against Markdown with exact matching first, then whitespace-insensitive matching.
5. Inserting video Markdown after the matched paragraph.
6. Reporting anchor misses instead of appending videos to the article tail.

This prevents the failure mode where all videos appear at the end of the X article.

---

## 7. X Video Upload Framework

X video processing creates an `Uploading media...` overlay that can intercept further clicks. The safe rule is:

1. Upload one video file.
2. Wait until the upload overlay disappears.
3. Confirm no failure toast is visible.
4. Continue with the next video.

Large videos can take minutes. Keep waiting if the media block is visible and no failure is shown.

---

## 8. Troubleshooting

### Feishu app credentials missing

Feishu app credentials mean the App ID and App Secret of a Feishu/Lark custom app. They are used by `feishu2md` and by this skill's video recovery step to call Feishu APIs. They are not user login credentials.

Run:

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

Or set:

```bash
export FEISHU_APP_ID=<your_app_id>
export FEISHU_APP_SECRET=<your_app_secret>
```

### X login expired

Reopen with:

```bash
bash ~/.codex/skills/x-article-publisher/scripts/open_x_articles_browser.sh
```

Complete the login manually once, then reuse the same profile.

### Media file not found

Check parse output:

```bash
python ~/.codex/skills/x-article-publisher/scripts/parse_markdown.py /path/to/article.md
```

Look at `missing_media`, `missing_images`, and `missing_videos`.

### Remote media URL

Remote URLs are not converted into uploadable local files. Download them first or keep media next to the Markdown file.
