#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


URL_PATTERN = re.compile(r"https?://[^\s<>'\"`，。；：！？、）)\]}】》]+", re.IGNORECASE)
TRAILING_PUNCTUATION = " \t\r\n,.;:!?，。；：！？、)]}）】》>\"'"


def expand_path(raw: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()


def read_clipboard() -> str:
    if not shutil.which("pbpaste"):
        raise RuntimeError("--clipboard is only supported when pbpaste is available")
    completed = subprocess.run(
        ["pbpaste"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to read clipboard")
    return completed.stdout


def extract_urls(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in URL_PATTERN.findall(html.unescape(text)):
        url = match.rstrip(TRAILING_PUNCTUATION)
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def find_ytdlp() -> list[str]:
    env_bin = os.environ.get("YT_DLP_BIN")
    if env_bin:
        resolved = shutil.which(env_bin) if not Path(env_bin).exists() else env_bin
        if resolved:
            return [resolved]

    binary = shutil.which("yt-dlp")
    if binary:
        return [binary]

    try:
        subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception:
        raise RuntimeError(
            "yt-dlp is not installed. Install it with `brew install yt-dlp` "
            "or `python3 -m pip install -U yt-dlp`."
        )
    return [sys.executable, "-m", "yt_dlp"]


def collect_input(args: argparse.Namespace) -> str:
    chunks: list[str] = []
    if args.url:
        chunks.append(args.url)
    if args.clipboard:
        chunks.append(read_clipboard())
    if args.share_text:
        chunks.append(" ".join(args.share_text))
    if not chunks and not sys.stdin.isatty():
        chunks.append(sys.stdin.read())
    return "\n".join(chunk for chunk in chunks if chunk)


def add_common_options(command: list[str], args: argparse.Namespace) -> None:
    command.extend(["--newline", "--no-mtime", "--trim-filenames", str(args.trim_filenames)])

    if not args.playlist:
        command.append("--no-playlist")
    if args.cookies_from_browser:
        command.extend(["--cookies-from-browser", args.cookies_from_browser])
    if args.proxy:
        command.extend(["--proxy", args.proxy])
    if args.user_agent:
        command.extend(["--user-agent", args.user_agent])
    if args.referer:
        command.extend(["--referer", args.referer])
    if args.ffmpeg_location:
        command.extend(["--ffmpeg-location", args.ffmpeg_location])
    if args.write_info_json:
        command.append("--write-info-json")
    if args.write_thumbnail:
        command.append("--write-thumbnail")
    if args.write_subs:
        command.extend(["--write-subs", "--write-auto-subs", "--sub-langs", args.sub_langs])
    for extra in args.ytdlp_arg:
        command.extend(shlex.split(extra))


def build_command(url: str, args: argparse.Namespace) -> list[str]:
    command = find_ytdlp()
    add_common_options(command, args)

    if args.info_only:
        command.extend(["--dump-single-json", "--skip-download", url])
        return command

    if args.direct_url:
        command.extend(["-f", args.format, "--get-url", url])
        return command

    out_dir = expand_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    command.extend(["-P", str(out_dir), "-o", "%(title).180B [%(id)s].%(ext)s"])

    if args.audio_only:
        command.extend(["-x", "--audio-format", args.audio_format])
    else:
        command.extend(["-f", args.format, "--merge-output-format", args.merge_output_format])

    command.append(url)
    return command


def print_info(command: list[str]) -> int:
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        return completed.returncode

    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        print(completed.stdout)
        return 0

    summary = {
        "title": data.get("title"),
        "uploader": data.get("uploader") or data.get("channel"),
        "duration": data.get("duration"),
        "extractor": data.get("extractor"),
        "webpage_url": data.get("webpage_url"),
        "availability": data.get("availability"),
        "live_status": data.get("live_status"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    return 0


def run_one(url: str, args: argparse.Namespace) -> int:
    command = build_command(url, args)
    if args.dry_run:
        print(shlex.join(command))
        return 0

    print(f"[video-downloader] URL: {url}", file=sys.stderr)
    if args.info_only:
        return print_info(command)

    return subprocess.run(command, check=False).returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a video URL from pasted share text and download it with yt-dlp.",
    )
    parser.add_argument("share_text", nargs="*", help="Pasted share text or video URL")
    parser.add_argument("--url", help="Share text or URL, useful when the text starts with '-'")
    parser.add_argument("--clipboard", action="store_true", help="Read share text from macOS clipboard")
    parser.add_argument("--out-dir", default="~/Downloads/video-downloads", help="Download folder")
    parser.add_argument("--info-only", action="store_true", help="Print parsed metadata without downloading")
    parser.add_argument("--direct-url", action="store_true", help="Print direct media URL instead of downloading")
    parser.add_argument("--all", action="store_true", help="Process all URLs found in the pasted text")
    parser.add_argument("--url-index", type=int, default=1, help="1-based URL index to use when multiple URLs exist")
    parser.add_argument("--playlist", action="store_true", help="Allow playlist downloads")
    parser.add_argument("--format", default="bv*+ba/b", help="yt-dlp format selector")
    parser.add_argument("--merge-output-format", default="mp4", help="Container for merged video downloads")
    parser.add_argument("--audio-only", action="store_true", help="Extract audio instead of downloading video")
    parser.add_argument("--audio-format", default="m4a", help="Audio format used with --audio-only")
    parser.add_argument("--cookies-from-browser", help="Browser name for authenticated downloads, for example chrome")
    parser.add_argument("--proxy", help="Proxy URL passed to yt-dlp")
    parser.add_argument("--referer", help="Referer header passed to yt-dlp")
    parser.add_argument("--user-agent", help="User-Agent header passed to yt-dlp")
    parser.add_argument("--ffmpeg-location", help="Path to ffmpeg or its containing folder")
    parser.add_argument("--write-info-json", action="store_true", help="Save yt-dlp info JSON next to the media")
    parser.add_argument("--write-thumbnail", action="store_true", help="Save thumbnail next to the media")
    parser.add_argument("--write-subs", action="store_true", help="Save subtitles when available")
    parser.add_argument("--sub-langs", default="all", help="Subtitle language selector")
    parser.add_argument("--trim-filenames", type=int, default=180, help="Maximum filename length")
    parser.add_argument(
        "--ytdlp-arg",
        action="append",
        default=[],
        help="Extra yt-dlp argument string, repeatable. Use --ytdlp-arg='--option value'.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the yt-dlp command without running it")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.info_only and args.direct_url:
        print("--info-only and --direct-url cannot be used together", file=sys.stderr)
        return 2

    try:
        text = collect_input(args)
        urls = extract_urls(text)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not urls:
        print("error: no http(s) URL found in the provided share text", file=sys.stderr)
        return 2

    selected = urls if args.all else []
    if not args.all:
        if args.url_index < 1 or args.url_index > len(urls):
            print(f"error: --url-index must be between 1 and {len(urls)}", file=sys.stderr)
            return 2
        selected = [urls[args.url_index - 1]]

    exit_code = 0
    for url in selected:
        code = run_one(url, args)
        if code != 0 and exit_code == 0:
            exit_code = code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
