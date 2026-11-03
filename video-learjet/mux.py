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

print("· wind / rain")
noise = rng.standard_normal(N)
wind = lp(noise, 380, 2) * (1 + .5 * np.sin(2 * np.pi * .13 * t)) * env_scene(["hook", "storm", "dive"], 1.0, 2)
rain = (lp(noise, 6000, 1) - lp(noise, 1500, 1)) * env_scene(["hook", "storm", "dive"], .25, 2)

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

bed = drone * .09 + pad * .5 + wind * .18 + rain * .05 + thunder * .55
bed = np.tanh(bed * 1.4) / 1.4
fade = int(2.5 * SR); bed[-fade:] *= np.linspace(1, 0, fade); bed[:int(.5 * SR)] *= np.linspace(0, 1, int(.5 * SR))
bed = bed / np.abs(bed).max() * .5
st = np.stack([bed, np.roll(bed, int(.012 * SR))], 1)
with wave.open(str(OUT / "ambient.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
print("  → out/ambient.wav")

video = OUT / "video_silent.mp4"
timings = AUD / "timings.json"
if not timings.exists():
    dst = OUT / "video_sem_voz.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(OUT / "ambient.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(dst)], check=True)
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
    # subtitles from character alignment
    al = json.loads((AUD / f"alignment_{i:02d}.json").read_text())
    chars, s0, s1 = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, ws = [], "", None
    for c, a, b in zip(chars, s0, s1):
        if c.isspace():
            if cur: words.append((cur, ws, we)); cur = ""
        else:
            if not cur: ws = a
            cur += c; we = b
    if cur: words.append((cur, ws, we))
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
     "[voice][ducked]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
vf = []
if BURN:
    style = "FontName=Inter,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=1,Outline=1.6,Shadow=0,MarginV=60"
    vf = ["-vf", f"subtitles={OUT / 'legendas.srt'}:force_style='{style}'"]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(OUT / "ambient.wav"), *inputs,
       "-filter_complex", fc, "-map", "0:v", "-map", "[aout]", *(vf or ["-c:v", "copy"]),
       *(["-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p"] if BURN else []),
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(OUT / "final.mp4")]
subprocess.run(cmd, check=True)
print("→ out/final.mp4")
