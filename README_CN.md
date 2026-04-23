# X Article Publisher Skill

> 把飞书/Lark 文档或本地 Markdown 发布到 X Articles 草稿，支持图片、视频和持久化登录态。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Skills](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh) [![X Articles](https://img.shields.io/badge/X-Articles-black)](https://x.com/compose/articles)

**这个 skill 的目标很直接：把一篇飞书文章，变成一篇已经排好图文和视频顺序的 X Article 草稿。**

它会先把飞书下载成本地 Markdown，补回 `feishu2md` 默认漏掉的视频块，把视频插回原文附近，再打开已经登录过的 X 浏览器 profile，把标题、正文、图片、视频依次放进草稿里。默认只保存草稿，不自动发布。

**语言 / Languages:** 中文 · [English](README.md)

---

## 它解决什么问题

| 问题 | 解决方式 |
|---|---|
| 飞书导出的 Markdown 经常没有视频 | 读取飞书 dump JSON，下载 file/video block，再写回 Markdown |
| 视频容易全部堆到文章最后 | 用文本锚点和忽略空格匹配，把视频插回接近原文的位置 |
| 每次登录 X 风险高 | 使用独立持久化浏览器 profile，不复用、不污染你的日常 Chrome profile |
| 本地 Markdown 也应该能发 | 本地 `.md` 直接解析，不走飞书下载步骤 |
| X 视频上传容易卡住 | 串行上传视频，每个视频等 `Uploading media...` 消失后再继续 |

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
| 飞书链接 -> X 草稿 | X Premium Plus、Python 3.9+、Node.js/npm、`feishu2md`、飞书 OpenAPI 凭据、一次 X 登录 |
| 本地 Markdown -> X 草稿 | X Premium Plus、Python 3.9+、Node.js/npm、一次 X 登录 |

飞书链接模式需要配置凭据：

```bash
feishu2md config --appId <your_app_id> --appSecret <your_app_secret>
```

也可以用环境变量：

```bash
export FEISHU_APP_ID=<your_app_id>
export FEISHU_APP_SECRET=<your_app_secret>
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
4. **Markdown 解析**：提取标题、封面、正文 HTML、图片、视频、分割线和 block 位置。
5. **持久化 X 浏览器**：默认使用 `~/.codex/browser-profiles/x-articles`。
6. **组装草稿**：先封面、标题、正文，再按位置倒序插入图片、视频、分割线。
7. **视频安全策略**：一次只上传一个视频，等 X 的上传遮罩消失后再继续。

完整框架说明：[docs/GUIDE_CN.md](docs/GUIDE_CN.md)

---

## 诚实边界

- 这个 skill 只创建 X Article 草稿，不自动发布。
- X Articles 需要账号拥有 Articles 权限，通常需要 X Premium Plus。
- 第一次使用持久化 profile 时，仍可能需要手动完成 X 登录或安全验证。
- 远程图片/视频 URL 会被识别，但不作为稳定上传路径；要稳定上传，请把媒体文件放在本地。
- 飞书链接模式依赖飞书 OpenAPI 权限，尤其是文档读取、素材下载、Wiki 读取权限。
- 大视频在 X 上可能需要几分钟处理，中途打断可能留下半成品草稿。

---

## 仓库结构

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

## 致谢

- 飞书 Markdown 下载基础能力来自 [Wsine/feishu2md](https://github.com/Wsine/feishu2md)
- Skill 打包形态参考 [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill)
- README 组织方式参考 [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)

## 许可证

MIT。可以使用、修改，并按你的发布流程继续改造。
