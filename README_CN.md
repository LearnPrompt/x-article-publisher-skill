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
- Playwright MCP
- Python 3.9+
- `feishu2md`（用于飞书下载）
- macOS 依赖：`pip install Pillow pyobjc-framework-Cocoa`
- Windows 依赖：`pip install Pillow pywin32 clip-util`

## 安装

```bash
git clone https://github.com/LearnPrompt/x-article-publisher-skill.git
cp -r x-article-publisher-skill/skills/x-article-publisher "$CODEX_HOME/skills/"
```

如果没设置 `CODEX_HOME`，默认一般是 `~/.codex`。

## 用法

### 方式 1：飞书链接

```text
把这个飞书链接发布到 X 草稿：https://aiwarts101.feishu.cn/docx/...
```

### 方式 2：本地 Markdown

```text
把 /path/to/article.md 发布到 X 草稿
```

## 工作流（简版）

1. 路由输入源（飞书链接 / 本地 Markdown）
2. 解析标题、封面图、正文 HTML、图片和视频位置
3. 打开 X Articles 编辑器（持久化 profile）
4. 上传封面、填写标题、粘贴正文
5. 按位置插入图片与视频
6. 保存为草稿（不自动发布）

## 仓库结构

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

## 致谢

- 飞书下载基础能力来自 [Wsine/feishu2md](https://github.com/Wsine/feishu2md)
- 项目形态参考 [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)
