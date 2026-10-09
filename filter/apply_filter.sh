#!/usr/bin/env bash
# Apply the Adventure Pop look to a video: ./apply_filter.sh input.mp4 output.mp4
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
ffmpeg -i "$1" -vf "lut3d=$DIR/adventure_pop.cube:interp=tetrahedral,unsharp=lx=13:ly=13:la=0.45,unsharp=lx=5:ly=5:la=0.6,vignette=angle=PI/7" \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -c:a copy "$2"
