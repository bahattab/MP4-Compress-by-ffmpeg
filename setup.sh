#!/usr/bin/env bash
set -euo pipefail

if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  echo "FFmpeg and ffprobe are already installed. Python 3 is also required."
  exit 0
fi

case "$(uname -s)" in
  Darwin)
    if command -v brew >/dev/null 2>&1; then
      brew install ffmpeg python
    else
      echo "Install Homebrew first (https://brew.sh), then run this script again." >&2
      exit 1
    fi
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y ffmpeg python3
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y ffmpeg python3
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -S --needed ffmpeg python
    else
      echo "Install FFmpeg and Python 3 using your distribution's package manager." >&2
      exit 1
    fi
    ;;
  *)
    echo "On Windows, run setup.ps1 in PowerShell." >&2
    exit 1
    ;;
esac

echo "Setup complete. Check with: ffmpeg -version and python3 --version"
