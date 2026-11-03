#!/usr/bin/env python3
"""Generate the voice-over with ElevenLabs, one file per scene, with character timestamps.

    export ELEVENLABS_API_KEY=...            # never commit this
    export ELEVENLABS_VOICE_ID=...           # optional: a deep documentary-narrator voice
    python3 elevenlabs_tts.py
    python3 elevenlabs_tts.py --voice <VOICE_ID> --preview   # hear only the opening line with another voice
    python3 elevenlabs_tts.py --voice <VOICE_ID>             # generate everything with that voice

Writes audio/scene_XX_<id>.mp3, audio/alignment_XX.json and audio/timings.json.
Uses only the Python standard library.
"""
import base64, json, os, re, sys, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
# also read the key from .env.local / .env next to this script (both are git-ignored)
for envf in (".env.local", ".env"):
    f = ROOT / envf
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ARGV = sys.argv[1:]
VOICE_ID = ARGV[ARGV.index("--voice") + 1] if "--voice" in ARGV else os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # default: "George"; pick a documentary narrator voice
MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
FORMAT = os.environ.get("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")  # 128 kbps works on every plan; 192 needs Creator+
SETTINGS = {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True, "speed": 1.0}

if not API_KEY:
    sys.exit("Define ELEVENLABS_API_KEY no ambiente (export ELEVENLABS_API_KEY=...).")

script = json.loads((ROOT / "script.json").read_text(encoding="utf-8"))
out = ROOT / "audio"; out.mkdir(exist_ok=True)
SPLIT = re.compile(r"(?<=[.!?])\s+")


def tts(text, prev_text, next_text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps?output_format={FORMAT}"
    body = {"text": text, "model_id": MODEL_ID, "voice_settings": SETTINGS}
    if prev_text: body["previous_text"] = prev_text
    if next_text: body["next_text"] = next_text
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": API_KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs HTTP {e.code}: {e.read().decode(errors='replace')}")


if "--preview" in ARGV:
    # try a voice cheaply: only the opening scene, timings.json untouched
    sc = script["scenes"][0]
    res = tts(sc["text"], None, None)
    f = out / f"preview_{VOICE_ID}.mp3"; f.write_bytes(base64.b64decode(res["audio_base64"]))
    print(f"Amostra gravada: {f}")
    if sys.platform == "darwin": os.system(f'open "{f}"')
    sys.exit(0)

timings = {"voice_id": VOICE_ID, "model_id": MODEL_ID, "scenes": []}
scenes = script["scenes"]
for i, sc in enumerate(scenes):
    text = sc["text"]
    print(f"[{i + 1}/{len(scenes)}] {sc['id']} …", flush=True)
    res = tts(text, scenes[i - 1]["text"] if i else None, scenes[i + 1]["text"] if i + 1 < len(scenes) else None)
    mp3 = out / f"scene_{i:02d}_{sc['id']}.mp3"
    mp3.write_bytes(base64.b64decode(res["audio_base64"]))
    al = res.get("alignment") or res.get("normalized_alignment")
    (out / f"alignment_{i:02d}.json").write_text(json.dumps(al, ensure_ascii=False), encoding="utf-8")
    chars, starts, ends = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    joined = "".join(chars)
    sents = SPLIT.split(text)
    sstarts, pos = [], 0
    for s in sents:
        k = joined.find(s[:12], pos)
        if k < 0:  # fallback: proportional position
            k = min(len(starts) - 1, int(len(starts) * text.find(s) / max(1, len(text))))
        sstarts.append(round(starts[k], 3)); pos = k + 1
    # word timings for the kinetic captions (same tokenisation as index.html: text.split())
    wstarts, wends, pos = [], [], 0
    for w in text.split():
        k = joined.find(w, pos)
        if k < 0:
            k = min(len(starts) - 1, pos)
        e = min(len(ends) - 1, k + len(w) - 1)
        wstarts.append(round(starts[k], 3)); wends.append(round(ends[e], 3)); pos = k + len(w)
    dur = round(ends[-1] + 0.05, 3)
    timings["scenes"].append({"id": sc["id"], "file": mp3.name, "duration": dur, "sentence_starts": sstarts,
                              "word_starts": wstarts, "word_ends": wends})
    print(f"    {dur:.2f} s, {len(sents)} frases")

(out / "timings.json").write_text(json.dumps(timings, indent=2, ensure_ascii=False), encoding="utf-8")
print("OK → audio/timings.json. Agora: ./render_all.sh   e depois   python3 mux.py")
