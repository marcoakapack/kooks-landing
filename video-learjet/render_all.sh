#!/usr/bin/env bash
# Render in 4 parallel chunks split at scene boundaries, then concatenate.
set -e
cd "$(dirname "$0")"
node -e "" && node render.mjs --stills 0 >/dev/null 2>&1 || true   # writes out/timeline.json
B=$(node -e "const t=require('./out/timeline.json');const s=t.scenes;console.log([0,s[3].start,s[5].start,s[7].start,t.total].map(x=>x.toFixed(4)).join(' '))")
set -- $B
node render.mjs --from $1 --to $2 --out out/part1.mp4 > out/log1.txt 2>&1 &
node render.mjs --from $2 --to $3 --out out/part2.mp4 > out/log2.txt 2>&1 &
node render.mjs --from $3 --to $4 --out out/part3.mp4 > out/log3.txt 2>&1 &
node render.mjs --from $4 --to $5 --out out/part4.mp4 > out/log4.txt 2>&1 &
wait
printf "file 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\nfile 'part4.mp4'\n" > out/parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i out/parts.txt -c copy out/video_silent.mp4
rm -f out/still_0.0.jpg
echo DONE
