#!/usr/bin/env python3
"""Generate realistic ambience and sound effects with ElevenLabs Sound Effects.

    python3 elevenlabs_sfx.py            # generates every sound that is still missing in audio/sfx/
    python3 elevenlabs_sfx.py --force    # regenerates all of them

Reads ELEVENLABS_API_KEY from .env.local / .env (both git-ignored). Writes audio/sfx/<name>.mp3.
mux.py uses these files automatically when they exist (otherwise it falls back to synthesized sound).
You can also make them on the website (elevenlabs.io → Sound Effects) with the same prompts and
save them under the same names in audio/sfx/.
"""
import json, os, sys, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
for envf in (".env.local", ".env"):
    f = ROOT / envf
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# name: (seconds, loop, prompt)
SOUNDS = {
    "amb_cabin":   (22, True,  "Inside a small business jet cruising at high altitude: steady deep engine hum and smooth airflow on the fuselage. Constant and even, no voices, no music."),
    "amb_storm":   (22, True,  "Inside a jet flying through a thunderstorm: heavy rain drumming on the fuselage, turbulent air buffeting, airframe creaks, distant rumbling thunder. No music."),
    "amb_high":    (22, True,  "Calm high-altitude sky ambience: a very soft, distant jet engine drone, airy and peaceful, no gusts, no music."),
    "amb_dive":    (15, False, "Jet aircraft in a steep high-speed dive: engine roar rising in pitch, rushing air growing louder and louder, airframe vibration, intense. No music."),
    "jet_flyby":   (6,  False, "A business jet flies past very close at high speed: powerful jet engine roar with doppler effect."),
    "thunder_1":   (6,  False, "Close cinematic thunder crack followed by a deep rolling rumble."),
    "thunder_2":   (8,  False, "Distant deep rolling thunder rumble with a long tail."),
    "ice_crackle": (6,  False, "Ice forming and crackling on cold metal, freezing water droplets, close and detailed, subtle."),
    "overspeed":   (6,  False, "Aircraft cockpit overspeed warning: rapid repetitive mechanical clacker alarm."),
    "whoosh":      (2,  False, "Fast cinematic whoosh transition, airy swish, clean, short."),
    "hit":         (3,  False, "Deep cinematic sub-bass impact boom with a short tail, trailer hit."),
}

if __name__ == "__main__":
    if not API_KEY:
        sys.exit("Falta ELEVENLABS_API_KEY no ficheiro .env.local")
    out = ROOT / "audio" / "sfx"; out.mkdir(parents=True, exist_ok=True)
    force = "--force" in sys.argv
    for name, (dur, loop, prompt) in SOUNDS.items():
        dst = out / f"{name}.mp3"
        if dst.exists() and not force:
            print(f"✓ {name} (já existe)"); continue
        body = {"text": prompt, "duration_seconds": dur, "prompt_influence": 0.5}
        if loop: body["loop"] = True
        def call(b):
            req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
                                         data=json.dumps(b).encode(), method="POST",
                                         headers={"xi-api-key": API_KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        try:
            try:
                data = call(body)
            except urllib.error.HTTPError as e:
                if e.code in (400, 422) and "loop" in body:   # older model without loop support
                    body.pop("loop"); data = call(body)
                else:
                    raise
        except urllib.error.HTTPError as e:
            sys.exit(f"ElevenLabs HTTP {e.code} em '{name}': {e.read().decode(errors='replace')[:300]}")
        dst.write_bytes(data)
        print(f"→ audio/sfx/{name}.mp3 ({dur} s)")
    print("Feito. Envia-me os ficheiros da pasta audio/sfx/.")
