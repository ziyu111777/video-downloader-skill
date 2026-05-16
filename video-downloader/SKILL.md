---
name: video-downloader
description: Parse video share text and download media locally.
metadata: {"openclaw":{"requires":{"bins":["yt-dlp"],"anyBins":["python3","python"]}},"hermes":{"category":"media","tags":["video","download"],"requires_tools":["terminal"]}}
---

# Video Downloader

Use this skill when the user gives a video/share URL or pasted app share text and wants the video downloaded locally.

## Core Workflow

1. Use `scripts/video_download.py` for the actual work. Resolve it relative to this `SKILL.md`; in OpenClaw, use `{baseDir}/scripts/video_download.py`. Do not hand-roll platform-specific parsers unless `yt-dlp` cannot support the target and the user explicitly wants a custom adapter.
2. If the user pasted a full share message, pass the whole text to the script; it extracts the first URL by default.
3. Default output folder is `~/Downloads/video-downloads`. Use `--out-dir` when the user specifies another destination.
4. For unknown links or suspected large downloads, run `--info-only` first, then download after confirming the title/source looks right.
5. Use `--cookies-from-browser chrome` only when the site requires login or age/session access. Never print cookie values.
6. After downloading, verify the file exists with `ls -lh <output-folder>` or by reading the script/`yt-dlp` output.

## Commands

```bash
python3 scripts/video_download.py "复制来的分享文案 https://example.com/video/123"
python3 scripts/video_download.py --clipboard
python3 scripts/video_download.py --info-only "https://example.com/video/123"
python3 scripts/video_download.py --cookies-from-browser chrome "https://example.com/video/123"
python3 scripts/video_download.py --out-dir ~/Desktop/视频下载 "https://example.com/video/123"
python3 scripts/video_download.py --audio-only --audio-format mp3 "https://example.com/video/123"
python3 scripts/video_download.py --direct-url "https://example.com/video/123"
```

## Failure Handling

- If `yt-dlp` is missing, install or update it with Homebrew or pip, then retry.
- If parsing fails, ask the user for the original full share text or URL, not a screenshot.
- If extraction fails with login/session errors, retry with `--cookies-from-browser chrome`.
- If a site uses DRM or blocks extraction, report that limitation plainly and do not invent a working parser.
