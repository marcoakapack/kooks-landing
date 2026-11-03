#!/usr/bin/env python3
"""Sound design (100% code) + voice-over mix + subtitles → final MP4.

    python3 mux.py                # video_silent.mp4 + ambient/thunder (+ voice if audio/timings.json exists)
    python3 mux.py --burn         # also burn the subtitles into the picture

Inputs : out/video_silent.mp4, out/timeline.json (written by render.mjs), optional audio/*.mp3 + audio/timings.json
Outputs: out/ambient.wav, out/final.mp4 (or out/video_sem_voz.mp4), out/legendas.srt
"""
import json, math, pathlib, re, subprocess, sys, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "out"; AUD = ROOT / "audio"
SR = 48000
BURN = "--burn" in sys.argv
tl = json.loads((OUT / "timeline.json").read_text())
TOTAL = tl["total"]; N = int(TOTAL * SR) + SR
rng = np.random.default_rng(1)
t = np.arange(N) / SR


def lp(x, fc, n=2):
    # FFT brick-ish lowpass with smooth rolloff (fast)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / fc) ** (2 * n)); return np.fft.irfft(X, len(x))


def env_scene(ids, level, fade=1.5):
    e = np.zeros(N)
    for s in tl["scenes"]:
        if s["id"] in ids:
            a, b = int(s["start"] * SR), int((s["start"] + s["dur"]) * SR)
            e[a:b] = level
    k = int(fade * SR); c = np.concatenate([[0], np.cumsum(e)])
    i = np.arange(N); lo = np.clip(i - k // 2, 0, N); hi = np.clip(i + k // 2, 0, N)
    return (c[hi] - c[lo]) / k


print("· drone / pad")
drone = np.zeros(N)
for f, a in [(55, .5), (82.41, .32), (110, .22), (164.81, .1), (41.2, .25)]:
    lfo = .75 + .25 * np.sin(2 * np.pi * (0.05 + f / 4000) * t + f)
    drone += a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * .11 * t)) * lfo
drone *= env_scene(["hook", "storm", "dive"], 1.0) + env_scene(["facts", "age", "ice", "coffin", "outro"], .55)
pad = np.zeros(N)
for f in [220, 277.18, 329.63, 440]:
    pad += np.sin(2 * np.pi * f * t) * (.6 + .4 * np.sin(2 * np.pi * .07 * t + f))
pad *= env_scene(["outro"], .18, 4) + env_scene(["age", "facts"], .06, 3)

# realistic recorded-style layers from ElevenLabs Sound Effects (audio/sfx/*.mp3, see elevenlabs_sfx.py)
SFXD = AUD / "sfx"
def load(name):
    f = SFXD / f"{name}.mp3"
    if not f.exists(): return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, 2).astype(np.float64)
REAL = {n: load(n) for n in ["amb_cabin", "amb_storm", "amb_high", "amb_dive", "jet_flyby", "thunder_1", "thunder_2", "ice_crackle", "overspeed", "whoosh", "hit"]}
REAL = {k: v for k, v in REAL.items() if v is not None}
print("· ElevenLabs sounds:", ", ".join(REAL) or "none (synth only)")
real = np.zeros((N, 2))
def place(x, at, gain=1.0, fade_in=.05, fade_out=.3):
    a = int(at * SR); x = x.copy(); n = len(x)
    if a < 0: x = x[-a:]; a = 0; n = len(x)
    n = min(n, N - a)
    if n <= 0: return
    x = x[:n]; fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi: x[:min(fi, n)] *= np.linspace(0, 1, min(fi, n))[:, None]
    if fo: x[-min(fo, n):] *= np.linspace(1, 0, min(fo, n))[:, None]
    real[a:a + n] += x * gain
def bed_loop(x, a, b, gain, xf=1.5):
    """tile x across [a, b) with crossfades"""
    k = int(xf * SR); L = len(x); t0 = a
    while t0 < b:
        seg_len = min(L, int((b - t0) * SR) + k)
        place(x[:seg_len], t0, gain, xf, xf); t0 += (L - k) / SR
sc_by = {s["id"]: s for s in tl["scenes"]}
def S(sid, k): s = sc_by[sid]; ss_ = s.get("sentence_starts", []); return s["start"] + (ss_[k] if k < len(ss_) else s["dur"])
AMB = {"hook": [("amb_storm", .55)], "facts": [("amb_high", .5)], "storm": [("amb_storm", .7)], "ice": [("amb_cabin", .35)],
       "coffin": [("amb_high", .5)], "dive": [("amb_storm", .6)], "outro": [("amb_high", .45)]}
for s in tl["scenes"]:
    for name, gn in AMB.get(s["id"], []):
        if name in REAL: bed_loop(REAL[name], max(0, s["start"] - .8), s["start"] + s["dur"] + .8, gn)
if "jet_flyby" in REAL: place(REAL["jet_flyby"], .2, .9)
if "ice_crackle" in REAL and "ice" in sc_by: place(REAL["ice_crackle"], S("ice", 3) + .4, .8, .3, 1.5)
if "amb_dive" in REAL and "dive" in sc_by: place(REAL["amb_dive"], S("dive", 1), .8, 1.5, 2.0)
if "overspeed" in REAL and "dive" in sc_by: place(REAL["overspeed"], S("dive", 2), .35, .05, 1.0)
for i, st_ in enumerate(tl["strikes"]):
    th = REAL.get("thunder_1" if i % 2 == 0 else "thunder_2")
    if th is not None: place(th, st_ + .3, .8 if i % 2 == 0 else .6, .02, 1.0)

print("· thunder")
thunder = np.zeros(N)
brown = np.cumsum(rng.standard_normal(N)); brown -= lp(brown, 8, 1); brown /= np.abs(brown).max()
for st in tl["strikes"]:
    d = 0.35 + rng.random() * .6
    a = int((st + d) * SR); L = int(4.5 * SR)
    if a + L >= N: L = N - a - 1
    if L <= 0: continue
    tt = np.arange(L) / SR
    envl = (1 - np.exp(-tt / .03)) * np.exp(-tt / (1.1 + rng.random())) * (1 + .6 * np.sin(2 * np.pi * (1.3 + rng.random()) * tt) ** 2)
    crack = rng.standard_normal(L) * np.exp(-tt / .12) * .35
    thunder[a:a + L] += brown[a:a + L] * envl * 1.2 + crack
thunder = lp(thunder, 900, 2)
if "thunder_1" in REAL: thunder[:] = 0   # recorded-style thunder replaces the synth one

bed = drone * .09 + pad * .5 + thunder * .55
bed = np.tanh(bed * 1.4) / 1.4
fade = int(2.5 * SR); bed[-fade:] *= np.linspace(1, 0, fade); bed[:int(.5 * SR)] *= np.linspace(0, 1, int(.5 * SR))
bed = bed / np.abs(bed).max() * .5
st = np.stack([bed, np.roll(bed, int(.012 * SR))], 1)
if REAL:
    st = st + real * .5
    st = st / (np.abs(st).max() + 1e-9) * .6
with wave.open(str(OUT / "ambient.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
print("  → out/ambient.wav")

print("· sfx (whooshes on cuts, hits on key words)")
sfx = np.zeros(N)
nz = rng.standard_normal(int(.8 * SR)); bands = [lp(nz, f, 2) - lp(nz, f / 3, 2) for f in (700, 2200, 6500)]
def whoosh(at, gain=1.0, L=.55):
    if "whoosh" in REAL:
        x = REAL["whoosh"].mean(1); pk = int(np.argmax(np.abs(x))); a = int(at * SR) - pk
        if a < 0 or a + len(x) >= N: return
        sfx[a:a + len(x)] += x / (np.abs(x).max() + 1e-9) * gain * .8; return
    n = int(L * SR); a = int((at - L * .6) * SR)
    if a < 0 or a + n >= N: return
    u = np.linspace(0, 1, n); env = np.sin(np.pi * u) ** 2.2
    w0 = np.clip(1 - 2 * u, 0, 1); w2 = np.clip(2 * u - 1, 0, 1); w1 = 1 - w0 - w2      # sweep low → high
    sig = bands[0][:n] * (1 - u) * .8 + bands[1][:n] * np.sin(np.pi * u) + bands[2][:n] * u * .6
    sfx[a:a + n] += sig * env * gain
def hit(at, gain=1.0):
    if "hit" in REAL:
        x = REAL["hit"].mean(1); a = int(at * SR) - int(np.argmax(np.abs(x[:int(.5 * SR)])))
        if a < 0 or a + len(x) >= N: return
        sfx[a:a + len(x)] += x / (np.abs(x).max() + 1e-9) * gain; return
    n = int(1.1 * SR); a = int(at * SR)
    if a < 0 or a + n >= N: return
    tt = np.arange(n) / SR; f = 38 + 30 * np.exp(-tt / .08)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / .35)
    click = lp(rng.standard_normal(n), 2500, 1) * np.exp(-tt / .015) * .5
    sfx[a:a + n] += (body + click) * gain
cuts = sorted({c for f in (OUT / "parts").glob("*.cuts.json") for c in json.loads(f.read_text())}) if (OUT / "parts").exists() else []
last = -9
for c in cuts:
    if c - last > .35 and c > .5: whoosh(c, .9); last = c
for p in tl.get("punches", []): hit(p, .8)
for s in tl["scenes"][1:]: hit(s["start"] + .1, 1.3); whoosh(s["start"] + .05, 1.3, .8)
sfx = sfx / (np.abs(sfx).max() + 1e-9) * .5
with wave.open(str(OUT / "sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([sfx, sfx], 1) * 32767).astype("<i2").tobytes())
print(f"  → out/sfx.wav ({len(cuts)} cuts, {len(tl.get('punches', []))} hits)")

video = OUT / "video_silent.mp4"
timings = AUD / "timings.json"
if not timings.exists():
    dst = OUT / "video_sem_voz.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(OUT / "ambient.wav"), "-i", str(OUT / "sfx.wav"),
                    "-filter_complex", "[1:a][2:a]amix=inputs=2:normalize=0[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(dst)], check=True)
    print("Sem voz ainda (audio/timings.json não existe). →", dst); sys.exit(0)

tm = json.loads(timings.read_text())
inputs, filters, labels, srt_items = [], [], [], []
for i, (sv, sa) in enumerate(zip(tl["scenes"], tm["scenes"])):
    f = AUD / sa["file"]; inputs += ["-i", str(f)]
    tempo = 1.0
    if abs(sa["duration"] - sv["speech"]) > .15:  # video was not rendered with these timings → fit voice to slot
        tempo = max(.8, min(1.25, sa["duration"] / sv["speech"]))
    delay = int((sv["start"] + sv["lead"]) * 1000)
    chain = f"[{i + 2}:a]aresample=48000,aformat=channel_layouts=stereo"
    if abs(tempo - 1) > .005: chain += f",atempo={tempo:.4f}"
    chain += f",adelay={delay}|{delay}[v{i}]"; filters.append(chain); labels.append(f"[v{i}]")
    # subtitles (SRT for YouTube) from word timings
    toks = [x["text"] for x in json.loads((ROOT / "script.json").read_text())["scenes"] if x["id"] == sa["id"]][0].split()
    words = list(zip(toks, sa["word_starts"], sa["word_ends"]))
    line, ls = [], None
    for wd, a, b in words:
        if not line: ls = a
        line.append(wd)
        txt = " ".join(line)
        if len(txt) > 38 or re.search(r"[.!?:,]$", wd) and len(txt) > 18 or wd == words[-1][0]:
            off = sv["start"] + sv["lead"]
            srt_items.append((off + ls / tempo, off + b / tempo, txt)); line = []

ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x * 1000 % 1000):03d}"
srt = "\n".join(f"{k + 1}\n{ts(a)} --> {ts(b)}\n{txt}\n" for k, (a, b, txt) in enumerate(srt_items))
(OUT / "legendas.srt").write_text(srt, encoding="utf-8")
print("  → out/legendas.srt")

n = len(labels)
fc = ";".join(filters) + f";{''.join(labels)}amix=inputs={n}:normalize=0,volume=1.0,asplit=2[voice][sc];" \
     "[1:a]volume=0.55[bed];[bed][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[ducked];" \
     f"[{n + 2}:a]volume=0.5[fx];[voice][ducked][fx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
vf = []
if BURN:
    style = "FontName=Inter,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=1,Outline=1.6,Shadow=0,MarginV=60"
    vf = ["-vf", f"subtitles={OUT / 'legendas.srt'}:force_style='{style}'"]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(OUT / "ambient.wav"), *inputs, "-i", str(OUT / "sfx.wav"),
       "-filter_complex", fc, "-map", "0:v", "-map", "[aout]", *(vf or ["-c:v", "copy"]),
       *(["-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p"] if BURN else []),
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(OUT / "final.mp4")]
subprocess.run(cmd, check=True)
print("→ out/final.mp4")
