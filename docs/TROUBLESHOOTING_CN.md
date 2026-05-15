# X Article Publisher 排障

这份文档记录真实发布过程中遇到过的问题。先看这里，再决定要不要改代码。

English version: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 快速判断

| 现象 | 常见原因 | 处理方式 |
|---|---|---|
| 飞书下载报 `no such host`、`WRONG_VERSION_NUMBER`、`server gave HTTP response to HTTPS client` | 本机代理/DNS 把 `open.feishu.cn` 解析到了 fake-ip | 修正代理或 DNS，让 `open.feishu.cn` 走真实 HTTPS |
| 视频全部跑到文章末尾 | 视频没有按飞书 block 附近锚点插回 Markdown | 重新运行新版 `prepare_article_source.py`，看 `video_download_errors` |
| 第 26 个左右正文媒体开始无响应 | X Articles 正文媒体达到实测上限 | 拆成多篇，或合并连续图片 |
| PNG 上传后没有生成媒体块 | X 编辑器没有接受该 PNG | 转成 JPG 后重传 |
| X 草稿页面打不开或跳到空白页 | 持久化 profile 被已有 Chrome 会话占用 | 关闭专用 profile 的 Chrome 进程后重开 |
| 视频上传后下一步点击没反应 | `Uploading media...` 遮罩还在 | 等上传状态消失后再继续 |

---

## 飞书 OpenAPI TLS 或 DNS 错误

典型错误：

```text
lookup open.feishu.cn: no such host
ssl.SSLError: WRONG_VERSION_NUMBER
http: server gave HTTP response to HTTPS client
```

先确认 DNS：

```bash
dig +short open.feishu.cn
```

如果结果是 `198.18.x.x`，通常是代理 fake-ip，不是飞书真实公网地址。需要调整本机代理/DNS，或者让命令显式走正确代理。

确认 HTTPS：

```bash
curl -I https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
```

能返回 HTTP 响应后，再重新运行：

```bash
python ~/.codex/skills/x-article-publisher/scripts/prepare_article_source.py "https://your-domain.feishu.cn/docx/..."
```

---

## X 正文媒体上限

实战中，X Articles 正文媒体达到约 `25` 个后，后续上传可能静默失败：

- 文件输入没有报错。
- 页面没有 toast。
- 正文没有新增媒体块。
- `Uploading media...` 也不会出现。

这通常不是网络问题。推荐处理：

1. 拆成两篇 X Articles。
2. 把连续截图合成长图。
3. 保留关键视频，删除弱信息量媒体。

---

## PNG 上传无响应

如果某张 PNG 上传后没有生成正文媒体块，可以先转 JPG：

```bash
python3 - <<'PY'
from PIL import Image
src = "/path/to/image.png"
dst = "/path/to/image.jpg"
Image.open(src).convert("RGB").save(dst, quality=95)
print(dst)
PY
```

然后用 JPG 重传。

---

## X 持久化 profile 被占用

典型现象：

```text
正在现有的浏览器会话中打开。
```

只关闭专用 profile，不要动日常 Chrome：

```bash
pkill -f "$HOME/.codex/browser-profiles/x-articles"
```

然后重新打开：

```bash
bash ~/.codex/skills/x-article-publisher/scripts/open_x_articles_browser.sh
```

---

## 视频上传卡住

X 上传视频时会出现 `Uploading media...`。这个状态存在时不要继续插入下一个媒体。

处理原则：

1. 一个视频完成后再上传下一个。
2. 大视频可以等几分钟。
3. 如果页面已有媒体块且没有错误提示，继续等待。
4. 如果长时间没有媒体块，也没有上传状态，重新定位锚点后再上传。

---

## 飞书视频顺序错误

新版流程会从飞书 dump JSON 中读取视频 file block，并找附近文本作为锚点。

检查下载输出：

```json
{
  "video_tokens_found": 10,
  "videos_downloaded": 10,
  "videos_appended": 10,
  "video_download_errors": []
}
```

如果 `video_download_errors` 不为空，不要继续发布。先修复锚点或手动确认视频位置。
