# X Article Publisher 框架说明

这份文档说明 `x-article-publisher` 的运行框架，适合想理解、调试或二次改造这个 skill 的用户。

English version: [GUIDE.md](GUIDE.md)

---

## 1. 输入源框架

这个 skill 有两种输入模式。

| 输入 | 触发方式 | 第一步 | 媒体策略 |
|---|---|---|---|
| 飞书/Lark 链接 | URL 包含 `feishu.cn`、`larksuite.com`、`feishu.sg` 或 `feishu.com` | 用 `prepare_article_source.py` 下载成本地 Markdown | 从飞书 dump JSON 补回视频，再解析本地 Markdown |
| 本地 Markdown | 本地 `.md` 或 `.markdown` 路径 | 直接使用原文件 | 解析 Markdown 里的本地图片和视频路径 |

### 飞书链接模式

1. 调用 `feishu2md dl --dump -o <workdir> <url>`。
2. 如果 URL 包含 `/wiki/`，自动加 `--wiki`。
3. 找到生成的 Markdown 和 dump JSON。
4. 从 dump JSON 里提取视频 file block。
5. 通过飞书 OpenAPI 把视频下载到 `static/`。
6. 按文本锚点把 `<video src="static/...">` 插回 Markdown。
7. 返回本地 Markdown 路径。

### 本地 Markdown 模式

1. 校验文件存在，且后缀是 `.md` 或 `.markdown`。
2. 直接返回原文件路径。
3. 由 `parse_markdown.py` 按 Markdown 所在目录解析图片和视频相对路径。

支持的本地视频写法：

```markdown
<video src="./static/demo.mp4"></video>
<video><source src="./static/demo.mp4"></video>
[video](./static/demo.mp4)
```

远程 `http(s)` 媒体 URL 会被识别出来，但不会被当成稳定可上传的本地文件。

---

## 2. 环境框架

安装有两条路径。

### 完整 Codex 安装

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

这个脚本会：

1. 把 skill 安装到 `$CODEX_HOME/skills/x-article-publisher`。
2. 安装 `skills/x-article-publisher/requirements.txt` 里的 Python 依赖。
3. 如果有 `npx`，预热 `@playwright/mcp`。
4. 如果有 Homebrew，尝试 `brew install feishu2md`。
5. 打印 `doctor.sh` 环境检查命令。

### skills.sh 兼容安装

```bash
npx skills add LearnPrompt/x-article-publisher-skill --skill x-article-publisher --global --copy --yes --full-depth
```

这个方式只安装 skill 文件，不会安装运行依赖。飞书模式仍然需要 Python 依赖、Playwright MCP 和 `feishu2md`。

### 环境检查

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh local
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh feishu
```

`doctor.sh` 会检查 Python、剪贴板依赖、Playwright CLI、`feishu2md`、飞书自建应用凭据和 X 持久化 profile 路径。

---

## 3. 浏览器框架

X 通过 `open_x_articles_browser.sh` 打开。

查找顺序：

1. 优先使用 Codex Playwright wrapper：`$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh`。
2. 其次使用 PATH 里的 `playwright-cli`。
3. 最后使用 `npx --yes --package @playwright/mcp playwright-cli`。

默认 profile：

```text
~/.codex/browser-profiles/x-articles
```

可以通过环境变量覆盖：

```bash
export X_ARTICLES_PROFILE=/custom/profile/path
```

这个 profile 和用户日常 Chrome profile 隔离。它可以减少重复登录 X 的风险，同时不覆盖用户原来的浏览器登录态。

---

## 4. Markdown 解析框架

`parse_markdown.py` 会提取：

- 标题
- 封面图，也就是第一张图片
- 用于富文本粘贴的正文 HTML
- `content_media`，图片和视频的统一列表
- `content_images` 和 `content_videos`，用于兼容旧流程
- `---` 分割线
- 用于定位的 `block_index` 和 `after_text`
- 缺失媒体数量

媒体插入使用倒序 `block_index`，避免前面插入后影响后面的位置。

---

## 5. X 草稿组装框架

发布流程应该按这个顺序执行：

1. 用 `prepare_article_source.py` 解析输入源。
2. 用 `parse_markdown.py` 解析 Markdown。
3. 用持久化 profile 打开 X Articles。
4. 上传封面图。
5. 填写标题。
6. 通过剪贴板粘贴 HTML 正文。
7. 按倒序 `block_index` 插入正文图片。
8. 按倒序 `block_index` 插入正文视频。
9. 按倒序 `block_index` 插入分割线。
10. 只保存草稿，不自动发布。

---

## 6. 视频顺序框架

飞书里的内嵌视频通常是 file block，而 `feishu2md` 默认主要处理图片 token，所以需要额外的视频恢复步骤。

这个 skill 保证视频顺序的方式：

1. 读取飞书 dump JSON 里的 root block 顺序。
2. 找到每个视频附近最近的文本块。
3. 把这个文本当作锚点。
4. 先做精确匹配，再做忽略空格匹配。
5. 把视频 Markdown 插到匹配段落之后。
6. 如果锚点失败，报告错误，而不是把视频追加到文章最后。

这样可以避免所有视频都跑到 X 文章末尾。

---

## 7. X 视频上传框架

X 上传视频时会出现 `Uploading media...` 遮罩，这个遮罩会拦截后续点击。安全规则是：

1. 上传一个视频文件。
2. 等上传遮罩消失。
3. 确认没有失败提示。
4. 再继续下一个视频。

大视频可能需要几分钟。如果媒体块已经出现、没有失败提示，就继续等待。

---

## 8. 排障

### 飞书自建应用凭据缺失

飞书自建应用凭据指的是飞书开放平台/开发者后台里的 App ID 和 App Secret。`feishu2md` 和本 skill 的视频补回步骤会用它们调用飞书接口。它们不是用户的飞书登录账号密码。

执行：

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

或者设置：

```bash
export FEISHU_APP_ID=<your_app_id>
export FEISHU_APP_SECRET=<your_app_secret>
```

### X 登录过期

重新打开：

```bash
bash ~/.codex/skills/x-article-publisher/scripts/open_x_articles_browser.sh
```

手动完成一次登录，之后继续复用同一个 profile。

### 媒体文件找不到

检查解析结果：

```bash
python ~/.codex/skills/x-article-publisher/scripts/parse_markdown.py /path/to/article.md
```

重点看 `missing_media`、`missing_images` 和 `missing_videos`。

### 远程媒体 URL

远程 URL 不会自动变成本地可上传文件。请先下载，或者把媒体文件放在 Markdown 文件旁边。
