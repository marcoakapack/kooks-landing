#!/usr/bin/env python3
"""Build audio/timings.json from narration MP3s that were generated on the ElevenLabs website
(no character alignment available), so the kinetic captions still follow the voice.

    python3 align_audio.py        # reads audio/scene_XX_<id>.mp3, writes audio/timings.json

How: ffmpeg's silencedetect finds the pauses. The longest pauses that best fit the expected
positions become sentence boundaries (dynamic programming), shorter pauses are matched to commas,
and words inside each phrase are spaced by their length. Accurate to roughly a syllable.
"""
import json, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent
import sys
A = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "audio")
script = json.loads((ROOT / "script.json").read_text(encoding="utf-8"))


def probe(f):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                             capture_output=True, text=True).stdout)
    log = subprocess.run(["ffmpeg", "-i", str(f), "-af", "silencedetect=noise=-38dB:d=0.1", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    sil = list(zip(st, en + [d] * (len(st) - len(en))))
    return d, sil


def pick(cands, expected, lo, hi):
    """Choose len(expected) silences (in order) inside (lo, hi) that best match the expected times.
    Score favours long pauses close to their expected position. Returns list (None where unmatched)."""
    c = [s for s in cands if lo < (s[0] + s[1]) / 2 < hi]
    n, m = len(expected), len(c)
    if n == 0:
        return []
    span = max(hi - lo, 1e-3)
    NEG = -1e9
    # dp[i][j]: best score using first i expected and first j candidates
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]
    bk = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1):
        dp[0][j] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # skip candidate j
            best, how = dp[i][j - 1], ("skip",)
            # leave expected i unmatched
            if dp[i - 1][j] - 1.5 > best:
                best, how = dp[i - 1][j] - 1.5, ("none",)
            s = c[j - 1]; mid = (s[0] + s[1]) / 2; dur = s[1] - s[0]
            sc = dp[i - 1][j - 1] + 3 * min(dur, .6) - 6 * abs(mid - expected[i - 1]) / span * n
            if sc > best:
                best, how = sc, ("take", j - 1)
            dp[i][j], bk[i][j] = best, how
    # unmatched-only column 0
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] - 1.5; bk[i][0] = ("none",)
    out, i, j = [None] * n, n, m
    while i > 0:
        how = bk[i][j]
        if how[0] == "skip": j -= 1
        elif how[0] == "none": i -= 1
        else: out[i - 1] = c[how[1]]; i -= 1; j -= 1
    return out


def scene_timing(text, f):
    d, sil = probe(f)
    lead = sil[0][1] if sil and sil[0][0] < .05 else 0.0
    tail = sil[-1][0] if sil and sil[-1][1] > d - .05 else d
    inner = [s for s in sil if s[0] > lead + .05 and s[1] < tail - .05]
    sents = re.split(r"(?<=[.!?])\s+", text)
    L = len(text)
    # expected sentence boundaries by character share
    cum, exp = 0, []
    for k in sents[:-1]:
        cum += len(k) + 1; exp.append(lead + (tail - lead) * cum / L)
    bnd = pick(inner, exp, lead, tail)
    starts, ends = [lead], []
    for k, b in enumerate(bnd):
        if b is None:  # fall back to proportional
            b = (exp[k] - .05, exp[k] + .05)
        ends.append(b[0]); starts.append(b[1])
    ends.append(tail)
    words_s, words_e = [], []
    for k, sen in enumerate(sents):
        a, b = starts[k], ends[k]
        # phrases split at commas/dashes; match their pauses inside this sentence
        phr = re.split(r"(?<=[,;:—])\s+", sen)
        pc, pexp = 0, []
        for p in phr[:-1]:
            pc += len(p) + 1; pexp.append(a + (b - a) * pc / len(sen))
        pb = pick([s for s in inner if a < s[0] and s[1] < b], pexp, a, b)
        ps, pe = [a], []
        for q, s in enumerate(pb):
            if s is None: s = (pexp[q], pexp[q])
            pe.append(s[0]); ps.append(s[1])
        pe.append(b)
        for q, p in enumerate(phr):
            ws = p.split(); wts = [len(re.sub(r"[^\w]", "", w)) + 2.5 for w in ws]; tot = sum(wts)
            t = ps[q]; dur = pe[q] - ps[q]
            for w, wt in zip(ws, wts):
                words_s.append(round(t, 3)); t += dur * wt / tot; words_e.append(round(t - .02, 3))
    return {"duration": round(d, 3), "sentence_starts": [round(x, 3) for x in starts],
            "word_starts": words_s, "word_ends": words_e}


timings = {"voice_id": "website", "model_id": "website", "aligned_by": "align_audio.py", "scenes": []}
for i, sc in enumerate(script["scenes"]):
    f = A / f"scene_{i:02d}_{sc['id']}.mp3"
    tm = scene_timing(sc["text"], f)
    assert len(tm["word_starts"]) == len(sc["text"].split()), sc["id"]
    timings["scenes"].append({"id": sc["id"], "file": f.name, **tm})
    print(f"{sc['id']:7s} {tm['duration']:6.2f} s  sentences at {', '.join(f'{x:.2f}' for x in tm['sentence_starts'])}")
(A / "timings.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")
print("OK → audio/timings.json")
