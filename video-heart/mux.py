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


sc_by = {s["id"]: s for s in tl["scenes"]}
def S(sid, k): s = sc_by[sid]; st_ = s["sentence_starts"]; return s["start"] + (st_[k] if k < len(st_) else s["dur"])
def ST(sid): return sc_by[sid]["start"]
def END(sid): s = sc_by[sid]; return s["start"] + s["dur"]
mono = np.zeros(N)
def add(x, at, gain=1.0):
    a = int(at * SR)
    if a < 0 or a >= N: return
    n = min(len(x), N - a); mono[a:a + n] += x[:n] * gain

print("· pads")
drone = np.zeros(N)
for f, a in [(55, .5), (82.41, .3), (41.2, .3), (110, .15)]:
    drone += a * np.sin(2 * np.pi * f * t + .3 * np.sin(2 * np.pi * .09 * t)) * (.75 + .25 * np.sin(2 * np.pi * .05 * t + f))
drone *= env_scene(["hook", "window", "impact", "aed"], 1.0, 2) + env_scene(["context", "electric"], .5, 2) + env_scene(["outro"], .3, 3)
pad = np.zeros(N)
for f in [220, 277.18, 329.63, 440, 554.37]:
    pad += np.sin(2 * np.pi * f * t) * (.6 + .4 * np.sin(2 * np.pi * .07 * t + f))
pad *= env_scene(["outro"], .22, 4) + env_scene(["electric"], .06, 3)

print("· heartbeats + monitor beeps")
def thump(f0=55, L=.22):
    n = int(L * SR); tt = np.arange(n) / SR; f = f0 + 30 * np.exp(-tt / .03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / .06) * (1 - np.exp(-tt / .004))
LUB, DUB = thump(52, .25), thump(66, .2) * .6
def beep(L=.09, f=1000):
    n = int(L * SR); tt = np.arange(n) / SR; e = np.minimum(1, tt / .004) * np.minimum(1, (L - tt) / .02)
    return np.sin(2 * np.pi * f * tt) * e
BEEP = beep()
def beats(a, b, bpm=72, ph0=.55, local0=0, gain=1.0, monitor=0.0):
    """beats whose ECG phase hits QRS (.2) inside [a, b) absolute; local time = abs - local0"""
    per = 60 / bpm; k = np.ceil(((a - local0) * bpm / 60 + ph0 - .2)); 
    while True:
        tl_ = (k + .2 - ph0) / (bpm / 60); at = local0 + tl_
        if at >= b: break
        if at >= a:
            add(LUB, at, gain); add(DUB, at + .3 * per, gain)
            if monitor: add(BEEP, at, monitor)
        k += 1
h = sc_by["hook"]; c1 = S("hook", 2) - .05
beats(0, c1, local0=ST("hook"), gain=1.0, monitor=.12)
beats(c1 + 2.0, END("hook"), local0=ST("hook"), gain=.6)
e = sc_by["electric"]; ec1 = S("electric", 4) - .05
beats(ST("electric"), ST("electric") + e["sentence_starts"][1], 72, local0=ST("electric"), gain=.7)
beats(ST("electric") + e["sentence_starts"][1], ec1, 48, local0=ST("electric"), gain=.7)
w = sc_by["window"]; hitw = S("window", 3) + 1.0
beats(ST("window"), hitw, local0=ST("window"), gain=.45)
beats(ST("impact"), S("impact", 4), local0=ST("impact"), gain=.4)
o = sc_by["outro"]; beats(ST("outro"), END("outro") - 2.5, 64, local0=ST("outro"), gain=.75)
shock = S("aed", 5) + 2.6
beats(shock + .3, END("aed"), 72, ph0=.02, local0=shock + .3, gain=.9, monitor=.1)

print("· fibrillation tremor, flatline, crowd")
nz = rng.standard_normal(N)
trem = lp(nz, 180, 2) * (.6 + .4 * np.sin(2 * np.pi * 6.5 * t)) 
vfmask = np.zeros(N)
for a_, b_ in [(S("window", 5) - .05, END("window")), (S("aed", 0) - 1, shock), (S("context", 6), S("context", 7) - .05)]:
    vfmask[int(a_ * SR):int(b_ * SR)] = 1
k = int(.4 * SR); c = np.concatenate([[0], np.cumsum(vfmask)]); i = np.arange(N); vfmask = (c[np.clip(i + k // 2, 0, N)] - c[np.clip(i - k // 2, 0, N)]) / k
mono += trem * vfmask * .5
crowd = lp(nz, 900, 2) - lp(nz, 150, 2); crowd *= (.7 + .3 * np.sin(2 * np.pi * .3 * t + 1))
cm = env_scene(["context"], 1.0, 1.0); tc = S("context", 3) - .55
cm[int(tc * SR):] *= np.exp(-np.maximum(0, (np.arange(N - int(tc * SR)) / SR)) / 1.2)
mono += crowd * cm * .35
# defibrillator: charging whine then the shock
n = int(1.6 * SR); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * np.cumsum(600 + 1800 * (tt / 1.6) ** 2) / SR) * np.minimum(1, tt / .2) * .18, shock - 1.6)
SFXD = AUD / "sfx"
def load(name):
    f = SFXD / f"{name}.mp3"
    if not f.exists(): return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").astype(np.float64)
HIT = load("hit")
def hit(at, g=1.0):
    if HIT is None: return
    x = HIT / (np.abs(HIT).max() + 1e-9); add(x, at - np.argmax(np.abs(x[:int(.5 * SR)])) / SR, g)
for s in tl["scenes"][1:]: hit(s["start"] + .1, .9)
hit(shock, 1.4); hit(S("context", 3) - .55, 1.1); hit(S("hook", 2) - .05, 1.0)

bed = drone * .08 + pad * .45
bed = np.tanh(bed * 1.4) / 1.4
mix = bed + mono * .5
fade = int(2.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade); mix[:int(.3 * SR)] *= np.linspace(0, 1, int(.3 * SR))
mix = mix / (np.abs(mix).max() + 1e-9) * .6
st = np.stack([mix, np.roll(mix, int(.008 * SR))], 1)
with wave.open(str(OUT / "ambient.wav"), "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((st * 32767).astype("<i2").tobytes())
with wave.open(str(OUT / "sfx.wav"), "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(np.zeros((N, 2), "<i2").tobytes())
print("  → out/ambient.wav")

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
fc = ";".join(filters) + f";{''.join(labels)}amix=inputs={n}:normalize=0,volume=1.0,apad=whole_dur={TOTAL:.3f},asplit=2[voice][sc];" \
     "[1:a]volume=0.7[bed];[bed][sc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=300[ducked];" \
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
