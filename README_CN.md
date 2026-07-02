# X Article Publisher Skill

> 把飞书/Lark 文档或本地 Markdown 发布到 X Articles 草稿，支持图片、视频和持久化登录态。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Skills](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh) [![X Articles](https://img.shields.io/badge/X-Articles-black)](https://x.com/compose/articles) [![维护状态](https://img.shields.io/badge/%E7%BB%B4%E6%8A%A4-%E8%A2%AB%E5%8A%A8-lightgrey)](#维护状态)

## 维护状态

本 skill 自 2026-06 起进入**被动维护**。它实现的工作流（飞书 → 本地 Markdown → X Article 草稿）对作者自己的发布管线已经够用，没有新功能规划。

- ✅ Issue 和 PR 欢迎提，作者有空就看。
- ✅ X 网页改版或飞书导出格式变了导致跑不通，会修（作者自己还在用）。
- ❌ 新渲染目标 / 新来源平台 / 大重构 不在范围 — 需要别的形态请 fork。
- ❌ 不承诺响应时间。X UI 关键中断可能拖 1-2 周。

如果你依赖本 skill 做生产发布，请 pin 到具体 commit，更新前看 release notes。

**这个 skill 的目标很直接：把一篇飞书文章，变成一篇已经排好图文和视频顺序的 X Article 草稿。**

它会先把飞书下载成本地 Markdown，补回 `feishu2md` 默认漏掉的视频块，把视频插回原文附近，再打开已经登录过的 X 浏览器 profile，把标题、正文、图片、视频依次放进草稿里。默认只保存草稿，不自动发布。

**语言 / Languages:** 中文 · [English](README.md)

---

## 它解决什么问题

| 问题 | 解决方式 |
|---|---|
| 飞书导出的 Markdown 经常没有视频 | 读取飞书 dump JSON，下载 file/video block，再写回 Markdown |
| 视频容易全部堆到文章最后 | 用文本锚点和忽略空格匹配，把视频插回接近原文的位置 |
| 飞书高亮块前面多出无意义的 `Tip` | 规范化 callout 标记，删除 `Tip` / `[!TIP]`，但保留多行高亮内容 |
| 每次登录 X 风险高 | 使用独立持久化浏览器 profile，不复用、不污染你的日常 Chrome profile |
| 本地 Markdown 也应该能发 | 本地 `.md` 直接解析，不走飞书下载步骤 |
| X 视频上传容易卡住 | 大视频先转码，视频逐个上传，最后用预览 DOM 做锚点顺序审计 |
| 大 GIF 可能静默失败或变成静态图 | 优先走文件上传；如果 X 吞掉大 GIF，就转成 MP4，并插回原来的 GIF 锚点 |
| 相邻视频/图片组容易串位 | 在 Preview 检查局部媒体序列，错了只修受影响的小区域，不重建整篇草稿 |

## 适合谁

这个 skill 很垂直：适合用飞书/Lark 写长文、用 X Articles 做公开分发的创作者和小团队。尤其适合文章里经常有截图、演示视频、产品录屏、AI 生成视频的人。

它不追求做一个通用 CMS，也不试图覆盖所有社交平台。它只把一个高频工作流打穿：**飞书写作 -> 本地 Markdown 中间态 -> X Article 草稿**。

## 实战验证

这个项目不是只跑过样例。它已经在真实文章里验证过这些情况：

| 场景 | 结果 |
|---|---|
| 飞书 docx，`1` 个视频、`10` 张正文图 | 完整生成 X Article 草稿 |
| 飞书 docx，`10` 个视频、`4` 张正文图 | 视频和图片按原文顺序插入 |
| 飞书 docx，`8` 个视频、`6` 张正文图 | 通过视频转码和最终锚点审计，保持全部媒体顺序正确 |
| 飞书 wiki 链接 | 自动使用 `--wiki` 下载，并恢复视频顺序 |
| 飞书 docx，`34` 个正文媒体 | 触发 X Articles 约 `25` 个正文媒体的实测上限 |
| 飞书 docx，相邻段落里有视频、视频和图片 | 只删除错位的局部媒体组，再从后往前重插，恢复顺序 |
| 飞书 docx，含 `18MB` GIF | X 静默吞掉 GIF 后，转成 MP4 并插回原锚点 |
| 本地 Markdown，含本地图片和 `<video>` | 可跳过飞书下载，直接进入 X 草稿组装 |

---

## 安装

### 方式 A：完整 Codex 安装，推荐

这个方式会把 skill 安装到 `~/.codex/skills/x-article-publisher`，同时安装 Python 依赖、预热 Playwright MCP，并在有 Homebrew 时尝试安装 `feishu2md`。

```bash
curl -fsSL https://raw.githubusercontent.com/LearnPrompt/x-article-publisher-skill/main/install.sh | bash
```

手动 clone：

```bash
git clone https://github.com/LearnPrompt/x-article-publisher-skill.git
bash x-article-publisher-skill/install.sh
```

只复制 skill 文件，不自动装依赖：

```bash
INSTALL_DEPS=0 bash x-article-publisher-skill/install.sh
```

### 方式 B：skills.sh / Claude Code 兼容安装

这个仓库可以被 `skills` CLI 识别：

```bash
npx skills add LearnPrompt/x-article-publisher-skill --skill x-article-publisher --global --copy --yes --full-depth
```

注意：`skills add` 只安装 skill 文件，不会自动安装 Python、Playwright、`feishu2md` 这些运行依赖。如果你用的是 Codex，优先使用上面的完整安装脚本。

### 检查环境

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh
```

如果只测试本地 Markdown：

```bash
bash ~/.codex/skills/x-article-publisher/scripts/doctor.sh local
```

---

## 需要准备什么

| 模式 | 需要准备 |
|---|---|
| 飞书链接 -> X 草稿 | X Premium Plus、Python 3.9+、Node.js/npm、`feishu2md`、飞书自建应用凭据（App ID / App Secret）、一次 X 登录 |
| 本地 Markdown -> X 草稿 | X Premium Plus、Python 3.9+、Node.js/npm、一次 X 登录 |

### 安装 feishu2md

`feishu2md` 是这个 skill 使用的上游“飞书/Lark 转 Markdown”工具。这个 skill 会先用它把飞书文档下载成本地 Markdown，再额外补回视频。

macOS 或 Linux，如果有 Homebrew：

```bash
brew install feishu2md
```

手动安装：
- 到 [Wsine/feishu2md releases](https://github.com/Wsine/feishu2md/releases) 下载对应系统的可执行文件。
- 把 `feishu2md` 放到 `PATH` 里的目录。
- 验证是否可用：

```bash
feishu2md -h
```

参考链接：
- [feishu2md GitHub README](https://github.com/Wsine/feishu2md)
- [Homebrew formula: feishu2md](https://formulae.brew.sh/formula/feishu2md)

### 配置飞书/Lark 自建应用凭据

飞书链接模式需要配置飞书自建应用凭据：

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

这是什么意思：
- App ID 和 App Secret 来自你在飞书开放平台/开发者后台创建的“企业自建应用”。
- 它们不是你的飞书登录密码。
- `feishu2md` 用它们调用飞书接口，把文档、图片、文件/视频下载到本地。
- 这个应用需要开通文档读取、素材/文件下载权限；如果要处理 Wiki 链接，还需要 Wiki 读取权限。

在哪里创建应用：
- 飞书：[open.feishu.cn/app](https://open.feishu.cn/app)
- Lark：[open.larksuite.com/app](https://open.larksuite.com/app)

建议开通的最小权限：

| 权限 | 用途 |
|---|---|
| `docx:document:readonly` | 读取新版飞书文档正文和 block |
| `docs:document.media:download` | 下载文档里的图片、附件、视频素材 |
| `drive:file:readonly` | 读取文档引用到的云空间文件/文件夹 |
| `wiki:wiki:readonly` | 处理 `/wiki/` 链接时需要 |

相关官方/API 文档：
- [获取文档基本信息](https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/get)
- [获取文档所有块](https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list)
- [下载素材](https://open.feishu.cn/document/server-docs/docs/drive-v1/media/download)
- [获取知识空间节点信息](https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/get_node)

也可以用环境变量：

```bash
export FEISHU_APP_ID=<your_app_id>
export FEISHU_APP_SECRET=<your_app_secret>
```

配置完成后，可以先单独测试 `feishu2md`：

```bash
feishu2md dl --dump -o /tmp/feishu2md-test "https://your-domain.feishu.cn/docx/..."
```

---

## 试试看

### 飞书链接

对 agent 说：

```text
把这个飞书文档发布到 X 草稿：https://your-domain.feishu.cn/docx/...
```

英文也可以：

```text
Publish this Feishu doc to X draft: https://your-domain.feishu.cn/docx/...
```

### 本地 Markdown

```text
把 /path/to/article.md 发布到 X 草稿
```

或：

```text
Publish /path/to/article.md to X draft
```

本地 Markdown 支持这些媒体写法：

```markdown
![cover](./static/cover.png)

<video src="./static/demo.mp4"></video>

[video](./static/clip.mp4)
```

相对路径会按 Markdown 文件所在目录解析。

---

## 工作原理

1. **输入分流**：飞书链接先下载，本地 Markdown 直接进入解析。
2. **飞书下载**：调用 `feishu2md dl --dump`；`/wiki/` 链接自动加 `--wiki`。
3. **视频补回**：读取飞书 JSON 里的 file/video block，用 OpenAPI 下载视频，再按文本锚点插回 Markdown。
4. **高亮块清理**：删除飞书导出里无意义的 `Tip` / `[!TIP]` 标记，但保留高亮块里的多行正文。
5. **Markdown 解析**：提取标题、封面、正文 HTML、图片、视频、分割线和 block 位置。
6. **持久化 X 浏览器**：默认使用 `~/.codex/browser-profiles/x-articles`。
7. **组装草稿**：先封面、标题、正文，再按位置倒序插入图片、视频、分割线。
8. **视频安全策略**：必要时先把大视频转码，逐个上传，等 X 处理完成后再继续。
9. **最终审计**：在预览页检查媒体数量和“锚点 -> 下一媒体类型”，不能只看总数。

完整框架说明：[docs/GUIDE_CN.md](docs/GUIDE_CN.md)

常见问题排障：[docs/TROUBLESHOOTING_CN.md](docs/TROUBLESHOOTING_CN.md)

---

## 诚实边界

- 这个 skill 只创建 X Article 草稿，不自动发布。
- X Articles 需要账号拥有 Articles 权限，通常需要 X Premium Plus。
- 第一次使用持久化 profile 时，仍可能需要手动完成 X 登录或安全验证。
- X Articles 正文媒体数量存在实测上限：约 `25` 个正文媒体后，编辑器可能静默拒绝继续上传。这个数字来自实战观察，不是 X 官方公开文档。
- 远程图片/视频 URL 会被识别，但不作为稳定上传路径；要稳定上传，请把媒体文件放在本地。
- 飞书链接模式依赖一个飞书自建应用，并且这个应用要开通文档读取、素材下载、Wiki 读取等权限。
- 大视频在 X 上可能需要几分钟处理，中途打断可能留下半成品草稿。
- 个别 PNG 可能在 X 编辑器里无响应；实战中转成 JPG 后可继续上传。
- 大 GIF 可能被文件选择器接受但不生成媒体块，或者通过剪贴板粘贴后丢动画；遇到这类 GIF，转成 MP4 后插回原锚点更稳。
- 过大或码率过高的视频可能让浏览器会话不稳定；实战中先转成 `1280px` 宽的 H.264/AAC 更稳。
- X 编辑器中途的媒体计数可能漂移，最终要以预览页 DOM 里的 `Image`、`Embedded video` 和锚点顺序为准。
- 多个媒体共用同一个锚点，或视频/图片锚点相邻时，不能只检查“下一媒体类型”；要检查该锚点附近接下来的几个媒体块，错了只修局部媒体组。

---

## 仓库结构

```text
x-article-publisher-skill/
├── install.sh
├── README.md
├── README_CN.md
├── scripts/
│   └── clean-local-artifacts.sh
├── docs/
│   ├── GUIDE.md
│   ├── GUIDE_CN.md
│   ├── TROUBLESHOOTING.md
│   └── TROUBLESHOOTING_CN.md
├── skills/x-article-publisher/
│   ├── SKILL.md
│   ├── requirements.txt
│   └── scripts/
│       ├── copy_to_clipboard.py
│       ├── doctor.sh
│       ├── open_x_articles_browser.sh
│       ├── optimize_media_blocks.py
│       ├── parse_markdown.py
│       ├── prepare_article_source.py
│       └── table_to_image.py
└── .claude-plugin/plugin.json
```

本地试发后清理：

```bash
bash scripts/clean-local-artifacts.sh
```

它会删除被忽略的运行残留，例如 `.playwright-cli/`、`tmp_*_publish/`、`x_article_runs/`、`.DS_Store` 和 Python `__pycache__/` 目录，不会删除已跟踪的源码文件。

---

## 致谢

- 飞书 Markdown 下载基础能力来自 [Wsine/feishu2md](https://github.com/Wsine/feishu2md)
- Skill 打包形态参考 [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)

## 许可证

MIT。可以使用、修改，并按你的发布流程继续改造。
