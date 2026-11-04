"""Build the vertical Short (1080x1920) from out/final.mp4: four voice excerpts, big word captions."""
import json, subprocess, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
O = R / 'out' / 'short'; O.mkdir(parents=True, exist_ok=True)
tm = {s['id']: s for s in json.load(open(R / 'timings_video.json'))['scenes']}
tl = {s['id']: s['start'] + s['lead'] for s in json.load(open(R / 'out' / 'timeline.json'))['scenes']}
txt = {s['id']: s['text'].split() for s in json.load(open(R / 'script.json'))['scenes']}
# (scene, first word index, last word index) — whole sentences only
CUTS = [('context', 0, 'stopped.'), ('hook', 'And', 'milliseconds.'), ('window', 'Doctors', 'pumping.'), ('outro', 0, 'follow.')]
RED = {'heart', 'stopped.', 'collapses.', 'stop', 'milliseconds.', 'twenty', 'fibrillation.', 'quivers', 'minutes'}
segs, words, T = [], [], 0.0
for sid, a, b in CUTS:
    w = txt[sid]; ia = a if isinstance(a, int) else w.index(a); ib = w.index(b)
    o = tl[sid]; ws, we = tm[sid]['word_starts'], tm[sid]['word_ends']
    t0, t1 = o + ws[ia] - .15, o + we[ib] + .35
    for k in range(ia, ib + 1): words.append((w[k], T + o + ws[k] - t0, T + o + we[k] - t0))
    segs.append((t0, t1)); T += t1 - t0
print('duration %.1f s' % T)
# captions: chunks of up to 3 words, current word highlighted
def ts(x): x = max(0, x); return '%d:%02d:%05.2f' % (x // 3600, x % 3600 // 60, x % 60)
ev, i = [], 0
while i < len(words):
    ch = [words[i]]; i += 1
    while i < len(words) and len(ch) < 3 and not ch[-1][0].endswith(('.', ',', '?')): ch.append(words[i]); i += 1
    for j, (w, s, e) in enumerate(ch):
        end = ch[j + 1][1] if j + 1 < len(ch) else e + .15
        parts = []
        for k, (w2, _, _) in enumerate(ch):
            c = '&H5561FF&' if w2.lower().strip('.,?') in {x.strip('.,?') for x in RED} else '&HFFFFFF&'
            if k == j: c = '&HFFD86F&' if c == '&HFFFFFF&' else c
            parts.append('{\\c%s}%s' % (c, w2.upper().replace(',', '').replace('.', '')))
        ev.append(f'Dialogue: 0,{ts(s)},{ts(end)},Cap,,0,0,0,,' + ' '.join(parts))
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,92,&HFFFFFF&,&HFFFFFF&,&H000000&,&H80000000&,0,0,0,0,100,100,0,0,1,0,6,8,60,60,1290,1
Style: Top,Inter Black,150,&HFFFFFF&,&HFFFFFF&,&H000000&,&H80000000&,0,0,0,0,100,100,-2,0,1,0,8,8,40,40,300,1
Style: Sub,Inter ExtraBold,66,&H5561FF&,&HFFFFFF&,&H000000&,&H80000000&,0,0,0,0,100,100,2,0,1,0,4,8,40,40,470,1
Style: Bot,Inter ExtraBold,40,&H30FFFFFF&,&HFFFFFF&,&H000000&,&H80000000&,0,0,0,0,100,100,6,0,1,0,3,8,40,40,1610,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
static = [f'Dialogue: 1,{ts(0)},{ts(T)},Top,,0,0,0,,{{\\blur1}}ONE HIT', f'Dialogue: 1,{ts(0)},{ts(T)},Sub,,0,0,0,,20 MILLISECONDS',
          f'Dialogue: 1,{ts(0)},{ts(T)},Bot,,0,0,0,,FULL VIDEO ON THE CHANNEL']
(O / 'caps.ass').write_text(head + '\n'.join(static + ev) + '\n')
# cut + join (re-encode each piece, short audio fades)
parts = []
for k, (a, b) in enumerate(segs):
    p = O / f'seg{k}.mp4'; d = b - a
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-t', f'{d:.3f}', '-i', str(R / 'out' / 'final.mp4'),
                    '-af', f'afade=t=in:d=0.06,afade=t=out:st={d - .12:.3f}:d=0.12', '-c:v', 'libx264', '-crf', '16', '-preset', 'fast', '-c:a', 'aac', '-b:a', '192k', str(p)], check=True)
    parts.append(p)
(O / 'list.txt').write_text(''.join(f"file '{p}'\n" for p in parts))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(O / 'list.txt'), '-c', 'copy', str(O / 'joined.mp4')], check=True)
fc = ('[0:v]split[a][b];'
      '[a]crop=1440:700:240:140,scale=-2:1920,crop=1080:1920,boxblur=40:2,eq=brightness=-0.3[bg];'
      '[b]crop=1440:730:240:130,scale=1080:-2[fg];'
      f"[bg][fg]overlay=0:700,ass='{O / 'caps.ass'}':fontsdir=/usr/share/fonts/opentype/inter[v]")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(O / 'joined.mp4'), '-filter_complex', fc, '-map', '[v]', '-map', '0:a',
                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', str(R / 'out' / 'short.mp4')], check=True)
print('→ out/short.mp4')
