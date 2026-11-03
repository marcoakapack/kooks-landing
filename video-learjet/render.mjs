// Render index.html frame-by-frame with headless Chromium and encode with ffmpeg.
// Usage: node render.mjs [--out out/video_silent.mp4] [--fps 30] [--from 0] [--to END] [--stills t1,t2,...]
// If audio/timings.json exists (written by elevenlabs_tts.py), the animation is timed to the real voice-over.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const FPS = +arg('fps', process.env.FPS || 24);
const OUT = path.resolve(ROOT, arg('out', 'out/video_silent.mp4'));
const STILLS = arg('stills', null);
const SCALE = +arg('scale', process.env.SCALE || 1);   // 2 → 3840×2160 (4K)

const MIME = { '.otf': 'font/otf', '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0);
const port = server.address().port;

// Linux servers have no GPU: use SwiftShader. On a Mac/PC, use the real GPU (much faster).
const GPU_ARGS = process.platform === 'linux' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] : ['--ignore-gpu-blocklist', '--enable-gpu'];
// macOS: full Chromium build (new headless) so WebGL runs on the Metal GPU
const browser = await chromium.launch(process.platform === 'darwin' ? { channel: 'chromium', args: GPU_ARGS } : { args: GPU_ARGS });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: SCALE });
page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
page.on('pageerror', e => console.error('[pageerror]', e.message));
await page.goto(`http://localhost:${port}/index.html`);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });

const timingsPath = fs.existsSync(path.join(ROOT, 'timings_video.json')) ? path.join(ROOT, 'timings_video.json') : path.join(ROOT, 'audio', 'timings.json');
let timeline;
if (fs.existsSync(timingsPath)) {
  const tm = JSON.parse(fs.readFileSync(timingsPath, 'utf8'));
  timeline = await page.evaluate(tm => window.setupTimeline(tm), tm);
  console.log('Timed to real voice-over (audio/timings.json)');
} else timeline = await page.evaluate(() => window.TIMELINE);
fs.mkdirSync(path.join(ROOT, 'out'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'out', 'timeline.json'), JSON.stringify(timeline, null, 2));
console.log(`Total: ${timeline.total.toFixed(2)} s`);

if (STILLS) {
  for (const s of STILLS.split(',')) {
    const t = +s;
    // warm up incremental sims for ~1 s before the still
    for (let k = 10; k >= 1; k--) await page.evaluate(t => window.renderFrame(t), Math.max(0, t - k / FPS));
    await page.evaluate(t => window.renderFrame(t), t);
    await page.screenshot({ path: path.join(ROOT, 'out', `still_${t.toFixed(1)}.jpg`), type: 'jpeg', quality: 85 });
    console.log('still', t);
  }
  await browser.close(); server.close(); process.exit(0);
}

if (process.argv.includes('--cutsonly')) {   // only collect cut times for the sound design (no frames written)
  for (let t = 0; t < timeline.total; t += 1 / FPS) await page.evaluate(t => window.renderFrame(t), t);
  fs.mkdirSync(path.join(ROOT, 'out', 'parts'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'out', 'parts', 'all.cuts.json'), JSON.stringify(await page.evaluate(() => [...window.CUTS_ABS].sort((a, b) => a - b))));
  console.log('cuts written'); await browser.close(); server.close(); process.exit(0);
}
const F0 = Math.round(+arg('from', 0) * FPS), F1 = Math.min(Math.round(+arg('to', timeline.total) * FPS), Math.floor(timeline.total * FPS));
const N = F1 - F0, from = F0 / FPS;
let FFMPEG = 'ffmpeg'; try { FFMPEG = createRequire(import.meta.url)('ffmpeg-static') || 'ffmpeg'; } catch {}
if (process.env.FFMPEG) FFMPEG = process.env.FFMPEG;
const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', SCALE > 1 ? '17' : '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
const t0 = Date.now();
for (let i = 0; i < N; i++) {
  const t = from + i / FPS;
  await page.evaluate(t => window.renderFrame(t), t);
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 150 === 0) { const el = (Date.now() - t0) / 1000; console.log(`frame ${i}/${N}  ${(el / (i + 1) * 1000).toFixed(0)} ms/frame  ETA ${((N - i) * el / (i + 1) / 60).toFixed(1)} min`); }
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
// cut times seen in this chunk → sound design (whooshes) in mux.py
fs.writeFileSync(OUT + '.cuts.json', JSON.stringify(await page.evaluate(() => [...window.CUTS_ABS].sort((a, b) => a - b))));
await browser.close(); server.close();
console.log('Wrote', OUT);
