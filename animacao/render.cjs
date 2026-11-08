// Renderiza index.html frame a frame e junta tudo num MP4 de 5 s (24 fps).
// Uso: node animacao/render.cjs [pasta-de-frames] [pagina.html] [saida.mp4]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 24, DURATION = 5;
const dir = __dirname;
const framesDir = process.argv[2] || path.join(dir, 'frames');
const pageFile = process.argv[3] || 'index.html';
const outFile = process.argv[4] || 'animacao.mp4';

(async () => {
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(dir, pageFile) + '?render');
  await page.waitForFunction(() => window.ready && document.fonts.ready);
  await page.evaluate(() => document.fonts.ready);
  const canvas = await page.$('canvas');
  const total = FPS * DURATION;
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.renderFrame(t), i / FPS);
    await canvas.screenshot({ path: path.join(framesDir, String(i).padStart(4, '0') + '.png') });
  }
  await browser.close();
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS),
    '-i', path.join(framesDir, '%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-crf', '18', '-movflags', '+faststart', path.join(dir, outFile)], { stdio: 'inherit' });
  console.log('OK ->', path.join(dir, outFile));
})();
