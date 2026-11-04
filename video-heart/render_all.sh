#!/usr/bin/env bash
# Render sequentially in resumable chunks (one per scene), then concatenate.
# (SwiftShader already uses all cores, so running chunks in parallel is slower.)
set -e
cd "$(dirname "$0")"
PARTS=${PARTS:-out/parts}; FFMPEG=${FFMPEG:-ffmpeg}
mkdir -p $PARTS
node render.mjs --stills 0 >/dev/null 2>&1 || true          # writes out/timeline.json
N=$(node -e "console.log(require('./out/timeline.json').scenes.length)")
: > out/parts.txt
CHUNK=${CHUNK:-10}   # seconds per resumable chunk
for i in $(seq 0 $((N-1))); do
  read A B < <(node -e "const t=require('./out/timeline.json');const s=t.scenes[$i];console.log(s.start.toFixed(4),(s.start+s.dur).toFixed(4))")
  for c in $(node -e "const a=$A,b=$B,c=$CHUNK;let o=[];for(let x=a,k=0;x<b-1e-6;x+=c,k++)o.push(k+':'+x.toFixed(4)+':'+Math.min(b,x+c).toFixed(4));console.log(o.join(' '))"); do
    IFS=: read k CA CB <<< "$c"
    f=$PARTS/p${i}_$k.mp4
    if [ ! -s "$f.done" ]; then node render.mjs --from $CA --to $CB --out $f && echo ok > $f.done; fi
    echo "file '${PARTS#out/}/p${i}_$k.mp4'" >> out/parts.txt
  done
  echo "scene $i done"
done
"$FFMPEG" -y -loglevel error -f concat -safe 0 -i out/parts.txt -c copy out/video_silent.mp4
rm -f out/still_0.0.jpg
echo RENDER_DONE
