# X Article Publisher Skill (Feishu + Video + Persistent Login)

> 一键把飞书或本地 Markdown 发布到 X Articles 草稿，支持图片和视频，并复用已登录账号会话。

## 这个版本解决了什么

1. **可以插入视频**
- 不仅处理图片，还会在解析后按位置插入视频媒体块。
- 针对飞书文档，补齐 `feishu2md` 默认缺失的视频下载流程。

2. **可以复用已登录 X 账号（持久化 profile）**
- 提供固定浏览器 profile 启动脚本，避免每次重新登录。
- 与你主 Chrome 日常使用隔离，不会覆盖现有会话。

3. **可以把整个流程跑通**
- 输入飞书链接：自动下载到本地（含视频）→ 解析 → 上传到 X 草稿。
- 输入本地 Markdown：跳过下载，直接上传到 X 草稿。
- 默认只保存草稿，不自动发布。

## 依赖要求

- X Premium Plus（需要 Articles 功能）
- Python 3.9+
- Node.js/npm（用于 `npx @playwright/mcp` 浏览器自动化）
- Python 依赖：见 `skills/x-article-publisher/requirements.txt`
- `feishu2md`（仅飞书链接模式需要；本地 Markdown 模式不需要）
- 飞书 OpenAPI 凭据（仅飞书链接模式需要）

## 安装

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

手动安装方式：

```bash
git clone https://github.com/LearnPrompt/x-article-publisher-skill.git
bash x-article-publisher-skill/install.sh
```

如果没设置 `CODEX_HOME`，默认是 `~/.codex`。

安装脚本会做这些事：
- 安装 skill 到 `$CODEX_HOME/skills/x-article-publisher`
- 通过 `pip --user` 安装 Python 依赖
- 尝试预热 `@playwright/mcp` 的 `playwright-cli`
- 如果本机有 Homebrew 且缺少 `feishu2md`，尝试执行 `brew install feishu2md`

不想自动安装依赖时：

```bash
INSTALL_DEPS=0 bash x-article-publisher-skill/install.sh
```

安装后执行环境体检：

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh
```

飞书链接模式还需要配置凭据：

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

也可以用环境变量 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`。

## 用法

### 方式 1：飞书链接

```text
把这个飞书链接发布到 X 草稿：https://aiwarts101.feishu.cn/docx/...
```

### 方式 2：本地 Markdown

```text
把 /path/to/article.md 发布到 X 草稿
```

本地 Markdown 支持：
- 本地图片：`![alt](./static/image.png)`
- 本地视频：`<video src="./static/clip.mp4"></video>`、`<video><source src="./static/clip.mp4"></video>` 或 `[video](./static/clip.mp4)`
- 相对路径会按 Markdown 文件所在目录解析

当前边界：
- 远程图片/视频 URL 会被标记为不可直接上传；图床 URL 是否能被 X 直接消费不保证，暂不作为主流程支持。
- 飞书链接模式是主路径：先下载到本地 Markdown，再按本地媒体文件上传。

## 工作流（简版）

1. 路由输入源（飞书链接 / 本地 Markdown）
2. 解析标题、封面图、正文 HTML、图片和视频位置
3. 打开 X Articles 编辑器（持久化 profile）
4. 上传封面、填写标题、粘贴正文
5. 按位置插入图片与视频
6. 保存为草稿（不自动发布）

## 实战经验（2026-02-21）

1. **先确认登录态，再进发布流程**
- 持久化 profile 里要看到 `auth_token/ct0` 才算已登录。
- 如果 `https://x.com/compose/articles` 显示 `Page not found / X` 且有 `Log in`，说明当前 profile 仍未登录。

2. **媒体文件必须在 Playwright 允许目录内**
- 若上传时报 `File access denied ... outside allowed roots`，把下载目录放到工作区（例如 `~/Downloads`）再上传。
- 本项目默认工作目录建议统一在 `~/Downloads` 下执行。

3. **图片按位置插入要做“逆序 + 文本定位”**
- 以 `block_index` 从大到小插入，避免前插导致后续位置偏移。
- 用 `after_text` 做段落定位，定位不到时用更短关键词兜底。

4. **避免重复插图**
- 每次重跑建议新建草稿，不要在同一草稿上重复执行。
- 若中途重试，先检查已有媒体数量，再补插缺失项。

## 实战经验（2026-04-23）

1. **飞书 Wiki 链接要走 Wiki 下载模式**
- `/wiki/...` 链接会映射到底层文档，下载时需要 `feishu2md dl --dump --wiki`。
- 下载后仍然以生成的 Markdown 为准继续解析，不要直接拿 wiki token 当 docx token。

2. **视频必须按锚点写回 Markdown**
- 飞书 API 返回的视频块不一定出现在 `feishu2md` 的 Markdown 里。
- 本项目会根据视频块前后的文本锚点插入 `<video src="..."></video>`。
- 如果锚点匹配失败，不再把视频追加到文末，而是记录错误，避免视频顺序错乱。

3. **0B 视频要重试，不能直接上传**
- 飞书大视频下载可能出现 0B 文件。
- 现在会复用非空文件，并对缺失或 0B 文件重新下载。
- 只有大于 0B 的视频才会进入后续 Markdown 和 X 上传流程。

4. **X 视频上传要逐个等待**
- 视频上传会出现 `Uploading media...` 全局遮罩，会拦截后续点击。
- 每个视频上传后必须等遮罩消失，再插入下一个媒体。
- 78MB 左右的视频可能需要数分钟，看到媒体块存在但仍在上传时不要中断。

## 仓库结构

```text
x-article-publisher-skill/
├── .claude-plugin/plugin.json
├── docs/GUIDE.md
├── skills/x-article-publisher/
│   ├── SKILL.md
│   ├── requirements.txt
│   └── scripts/
│       ├── copy_to_clipboard.py
│       ├── doctor.sh
│       ├── parse_markdown.py
│       ├── prepare_article_source.py
│       ├── open_x_articles_browser.sh
│       └── table_to_image.py
├── README.md
└── README_CN.md
```

## 致谢

- 飞书下载基础能力来自 [Wsine/feishu2md](https://github.com/Wsine/feishu2md)
- 项目形态参考 [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)
