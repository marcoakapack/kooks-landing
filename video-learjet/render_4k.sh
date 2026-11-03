#!/usr/bin/env bash
# Render the final video in 4K (3840×2160) at 60 fps on your own computer (Mac: uses the GPU),
# then add the finished sound track (out/final_audio.m4a, already in the repo).
#     bash render_4k.sh          (can be stopped and re-run: it resumes from the last finished scene)
set -e
cd "$(dirname "$0")"
if ! command -v node >/dev/null; then
  echo "Falta o Node.js. Instala a versão LTS em https://nodejs.org e volta a correr: bash render_4k.sh"; exit 1
fi
echo "== 1/4 a instalar dependências (só da primeira vez) =="
npm install --no-audit --no-fund
npx playwright install chromium
FFMPEG=$(node -p "try{require('ffmpeg-static')||''}catch(e){''}" 2>/dev/null)
[ -z "$FFMPEG" ] && FFMPEG=$(command -v ffmpeg || true)
[ -z "$FFMPEG" ] && { echo "Falta o ffmpeg (corre: brew install ffmpeg)"; exit 1; }
export FFMPEG SCALE=2 FPS=60 PARTS=out/parts4k
echo "== 2/4 a renderizar 4K 60 fps (mostra ms/frame e o tempo que falta) =="
bash render_all.sh
echo "== 3/4 a juntar o som =="
"$FFMPEG" -y -loglevel error -i out/video_silent.mp4 -i out/final_audio.m4a -map 0:v -map 1:a -c copy -shortest -movflags +faststart out/final_4k.mp4
echo "== 4/4 pronto: out/final_4k.mp4 =="
[ "$(uname)" = "Darwin" ] && open out || true
