$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Gyan.FFmpeg.Shared --exact --accept-package-agreements --accept-source-agreements
    } elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install ffmpeg -y
    } else {
        throw "Install FFmpeg with winget or Chocolatey, then reopen PowerShell."
    }
}

Write-Host "Setup complete. Reopen PowerShell if PATH changed, then run: python .\mp4_compress.py --help"
