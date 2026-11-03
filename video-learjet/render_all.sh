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
for i in $(seq 0 $((N-1))); do
  read A B < <(node -e "const t=require('./out/timeline.json');const s=t.scenes[$i];console.log(s.start.toFixed(4),(s.start+s.dur).toFixed(4))")
  f=$PARTS/p$i.mp4
  if [ ! -s "$f.done" ]; then node render.mjs --from $A --to $B --out $f && echo ok > $f.done; fi
  echo "file '${PARTS#out/}/p$i.mp4'" >> out/parts.txt
  echo "scene $i done"
done
"$FFMPEG" -y -loglevel error -f concat -safe 0 -i out/parts.txt -c copy out/video_silent.mp4
rm -f out/still_0.0.jpg
echo RENDER_DONE
