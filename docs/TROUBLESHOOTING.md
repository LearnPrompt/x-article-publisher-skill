# X Article Publisher Troubleshooting

This document records failure modes seen in real publishing runs. Check this before changing code.

Chinese version: [TROUBLESHOOTING_CN.md](TROUBLESHOOTING_CN.md)

---

## Quick Triage

| Symptom | Likely cause | Fix |
|---|---|---|
| Feishu download fails with `no such host`, `WRONG_VERSION_NUMBER`, or `server gave HTTP response to HTTPS client` | Local proxy/DNS resolves `open.feishu.cn` to a fake IP | Fix proxy/DNS so `open.feishu.cn` uses real HTTPS |
| All videos appear at the article tail | Videos were not restored near Feishu block anchors | Rerun the latest `prepare_article_source.py` and check `video_download_errors` |
| Uploads stop around the 26th body media item | Observed X Articles body-media limit | Split the article or merge consecutive images |
| PNG upload does not create a media block | X editor ignored that PNG | Convert the image to JPG and retry |
| X draft opens as blank or Playwright cannot control it | Persistent profile is already held by Chrome | Close only the dedicated profile process, then reopen |
| Clicks fail after video upload | `Uploading media...` overlay is still active | Wait until upload state disappears |

---

## Feishu OpenAPI TLS Or DNS Errors

Typical errors:

```text
lookup open.feishu.cn: no such host
ssl.SSLError: WRONG_VERSION_NUMBER
http: server gave HTTP response to HTTPS client
```

Check DNS first:

```bash
dig +short open.feishu.cn
```

If it returns `198.18.x.x`, the local proxy is likely using fake-ip DNS. Adjust proxy/DNS settings or make the command use the correct proxy path.

Check HTTPS:

```bash
curl -I https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
```

Once HTTPS returns a normal response, rerun:

```bash
python ~/.codex/skills/x-article-publisher/scripts/prepare_article_source.py "https://your-domain.feishu.cn/docx/..."
```

---

## X Body Media Limit

In field tests, X Articles may silently stop accepting body media around `25` items:

- The file input accepts the file.
- No toast appears.
- No media block is added.
- `Uploading media...` does not appear.

This is usually not a network issue. Recommended handling:

1. Split into two X Articles.
2. Merge consecutive screenshots into a long image.
3. Keep the most important videos and remove low-value media.

---

## PNG Upload Does Nothing

If a PNG upload does not create a body media block, convert it to JPG:

```bash
python3 - <<'PY'
from PIL import Image
src = "/path/to/image.png"
dst = "/path/to/image.jpg"
Image.open(src).convert("RGB").save(dst, quality=95)
print(dst)
PY
```

Then retry with the JPG.

---

## Persistent X Profile Is Busy

Typical message:

```text
正在现有的浏览器会话中打开。
```

Close only the dedicated profile, not the user's daily Chrome profile:

```bash
pkill -f "$HOME/.codex/browser-profiles/x-articles"
```

Then reopen:

```bash
bash ~/.codex/skills/x-article-publisher/scripts/open_x_articles_browser.sh
```

---

## Video Upload Appears Stuck

X shows `Uploading media...` while processing video. Do not insert the next media item while this overlay exists.

Rules:

1. Upload one video at a time.
2. Large videos may take minutes.
3. If a media block is visible and no error is shown, keep waiting.
4. If there is no media block and no upload state, re-place the cursor at the anchor and upload again.

---

## Feishu Video Ordering Is Wrong

The current flow reads video file blocks from Feishu dump JSON and uses nearby text as an anchor.

Check the download output:

```json
{
  "video_tokens_found": 10,
  "videos_downloaded": 10,
  "videos_appended": 10,
  "video_download_errors": []
}
```

If `video_download_errors` is not empty, do not publish yet. Fix the anchor or manually verify video positions first.
