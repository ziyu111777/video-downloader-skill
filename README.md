# Video Downloader Skill

Agent skill for parsing pasted video share text and downloading the referenced media locally through `yt-dlp`.

## Contents

```text
video-downloader/
├── SKILL.md
├── agents/openai.yaml
└── scripts/video_download.py
```

## Requirements

- `python3`
- `yt-dlp`
- Optional clipboard command when using `--clipboard`:
  - macOS: `pbpaste`
  - Windows: PowerShell or PowerShell 7 `Get-Clipboard`
  - Linux: `wl-paste`, `xclip`, or `xsel`

Install `yt-dlp`:

```bash
# macOS
brew install yt-dlp

# Windows
winget install yt-dlp.yt-dlp

# Any platform with Python
python3 -m pip install -U yt-dlp
```

## Direct Script Use

```bash
cd video-downloader
python3 scripts/video_download.py "复制来的视频分享文案 https://example.com/video/123"
python3 scripts/video_download.py --clipboard
python3 scripts/video_download.py --info-only "https://example.com/video/123"
python3 scripts/video_download.py --cookies-from-browser chrome "https://example.com/video/123"
python3 scripts/video_download.py --dry-run "https://example.com/video/123"
```

Default output folder:

```text
~/Downloads/video-downloads
```

## Codex Install

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/video-downloader" ~/.codex/skills/video-downloader
```

## Hermes Install

Hermes v0.9.0 on macOS did not discover symlinked skill directories reliably, so copy the folder:

```bash
mkdir -p ~/.hermes/skills/media
cp -R video-downloader ~/.hermes/skills/media/video-downloader
hermes skills list --source local
```

Use it:

```bash
hermes chat --skills video-downloader --toolsets terminal
```

## OpenClaw Install

```bash
mkdir -p ~/.openclaw/skills
cp -R video-downloader ~/.openclaw/skills/video-downloader
```

## Notes

- The skill intentionally uses `yt-dlp` instead of copying private parser APIs from mini-programs.
- The core script works on macOS, Windows, and Linux when Python and `yt-dlp` are available.
- Some platforms require browser cookies. Use `--cookies-from-browser chrome` only when needed.
- DRM-protected or heavily restricted video sources may not be downloadable.
