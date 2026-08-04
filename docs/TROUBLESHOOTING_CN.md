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
| 上传视频时浏览器关闭或漂移 | 视频过大或码率过高，X 处理不稳定 | 先转成 1280px 宽 H.264/AAC，再从原草稿 URL 继续 |
| 媒体数量对，但顺序不对 | 某个媒体被插到后面的锚点下 | 跑预览锚点审计，只删除错位项并重插 |
| X 正文里出现无意义的 `Tip` | 飞书高亮块标记漏进 Markdown | 重新运行 source preparation，或只删除标记行、保留正文 |
| GIF 上传看似成功但没有媒体块 | X 静默拒绝了大 GIF | 把 GIF 转成 MP4，再插回同一个锚点 |
| 相邻视频/图片顺序串了 | 相邻锚点或同锚点媒体组在插入时漂移 | 只删除这个局部媒体组，再从后往前重插 |
| Preview 或编辑器里出现 `Something went wrong. Please try again later.` | X 留下了失败上传块 | 点击旁边的 `Delete block`，清掉后再做最终审计 |

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

1. 运行 `optimize_media_blocks.py`，把正文媒体目标设为 24 个。
2. 只把相邻截图合成平衡的无裁切网格，并在 Preview 逐张检查完整性。
3. 如果仍超过安全预算，再保留关键视频并删除弱信息量媒体。

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

## GIF 上传被吞或丢动画

如果要保留动画，不要用剪贴板粘贴 GIF。剪贴板路径可能把 GIF 变成静态图。

如果文件上传接受了 GIF，但编辑器媒体数量没有增加，或者 Preview 里对应锚点后没有出现媒体，把 GIF 转成 MP4：

```bash
ffmpeg -y -i input.gif \
  -vf "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))',format=yuv420p" \
  -movflags +faststart -c:v libx264 -preset medium -crf 25 -an \
  input.gif.mp4
```

然后通过 `Insert > Media` 把 `input.gif.mp4` 插回原 GIF 的锚点。最终审计时，把它当成原 GIF 对应的一个视频类媒体块。

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

如果视频文件大或码率高，先转码再重试：

```bash
ffmpeg -y -i input.mov \
  -vf "scale='min(1280,iw)':-2" \
  -c:v libx264 -preset medium -crf 25 -pix_fmt yuv420p \
  -c:a aac -b:a 64k -movflags +faststart \
  output.x1280.mp4
```

重试时回到已有草稿 URL，不要新建草稿。

---

## 媒体数量对但顺序错

不要只看编辑器里的媒体数量。最终要在预览页检查：

- `img[alt="Image"]` 数量等于正文图片数。
- `video[aria-label="Embedded video"]` 数量等于正文视频数。
- 每个源媒体的 `after_text` 锚点后，下一个可见媒体类型正确。

如果发现某个媒体错位：

1. 在编辑器里只删除那个错位媒体块。
2. 把缺失媒体补回正确锚点。
3. 把错位媒体重新插回它自己的锚点。
4. 再跑一次预览审计。

对于相邻媒体组，不要只检查“下一个媒体”。比如 Markdown 是这样：

```markdown
段落 A
<video src="a.mp4"></video>

段落 B
<video src="b.mp4"></video>
![](b.png)
```

如果 Preview 里总数对，但局部顺序错：

1. 回到编辑器。
2. 只删除包含错位媒体的最小连续媒体组。
3. 从后往前重插：先插 `b.png`，再插 `b.mp4`，最后插 `a.mp4`。
4. 重新打开 Preview，检查两个锚点后面接下来的几个媒体块。

最终确认时不要依赖太短的模糊锚点，例如 `for example` 或 `比方说`，它们可能匹配到前文。要用靠近目标媒体的更长原句做审计。

---

## 草稿里残留失败上传块

X 有时会留下失败上传占位：

```text
Something went wrong. Please try again later.
```

看到这个文本时，不要报告草稿完成。点击旁边的 `Delete block` 按钮清掉，再重新跑 Preview 审计。

---

## 飞书高亮块出现 `Tip`

飞书高亮块有时会导出成：

```markdown
> Tip
> Important highlighted text
```

或者：

```markdown
> [!TIP]
> Important highlighted text
```

这个 skill 会删除标记，并保留高亮正文。如果 `Tip` 仍然出现，使用最新版重新运行 `prepare_article_source.py`，或者手动只删除标记行。

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
