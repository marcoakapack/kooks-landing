# Sixty Seconds: The Physics of the Florida Learjet Crash

Vídeo explicativo em inglês para um canal de YouTube de ciência e física, com realização cinematográfica: letterbox 2.39:1, 24 fps, bloom, grão de película, lens flares, relâmpagos 3D e câmaras montadas no avião. A animação, o motion design e o som ambiente são 100% código: Three.js em Chromium headless, renderizado frame a frame e codificado com ffmpeg. Não foram usadas IAs de imagem ou vídeo. A voz é gerada no ElevenLabs.

## Pesquisa (estado a 2 nov 2026)

| Facto | Fonte |
|---|---|
| Learjet 60, matrícula N722BD (2004), voo Austin (TX) → North Eleuthera (Bahamas) | Flightradar24 |
| Caiu a 1 nov 2026, ~12:49 hora local, em Greenacres (Palm Beach County); 9 mortos | CNN, NBC Miami, WPTV |
| Copiloto: Nathalia Gadelha Filgueiras, 20 anos; brevê de piloto privado aos 17, no secundário | Fox 7 Austin, CBS12, NBC Miami |
| Comandante de 55 anos | TMZ |
| ~12:47: gelo leve e transparente ("light clear icing"), turbulência moderada, desvios de ~700 pés a FL350 | NTSB, via CBS12 / WPTV |
| A tripulação pediu FL370; depois reportou overspeed e descida rápida | LiveATC, Flightradar24 |
| 35 250 → 8 750 pés em pouco mais de 1 min; razão de descida > 32 000 pés/min | FAA, Flightradar24 |
| O radar sugere que o avião entrou numa célula de trovoada em rápido crescimento | Flightradar24, AOL |
| NTSB: "alguns indícios de desintegração em voo"; ainda procuram componentes | NTSB |

A causa provável não está determinada. O vídeo apresenta hipóteses físicas compatíveis com os dados públicos e di-lo explicitamente.

## Estrutura (≈ 4 min 27 s)

0. **Cold open**: dentro da tempestade, contador de altitude 35,000 → 8,750 ft, título *SIXTY SECONDS*.
1. **Flight N722BD**: voo noturno sobre o mapa do Golfo, com luzes das cidades e células de trovoada sobre Palm Beach.
2. **The Right Seat**: jato ao pôr do sol, com as idades mínimas da FAA (17 · 18 · SIC · 23) em tipografia integrada no céu.
3. **Into the Storm**: tráfego rádio, cumulonimbo ao pôr do sol em modo raio-X (correntes ascendentes, nível de congelação, água em sobrefusão) e congelamento instantâneo no bordo de ataque.
4. **Ice**: escoamento potencial exato num perfil de Joukowski, gelo em "cornos", separação e curva CL–α.
5. **The Coffin Corner**: "paredes" de perda e de Mach que se fecham à volta do jato (atmosfera ISA calculada).
6. **Overspeed**: mergulho, 32,000 ft/min = 160 m/s = 360 mph, onda de choque na asa 3D, Mach tuck, flexão da asa (carga ∝ v²) e conclusão preliminar do NTSB.
7. **What We Don't Know**: prazos do NTSB, contorno de 20 NM em vista aérea e memória das vítimas.

## Gerar a voz com o ElevenLabs (no teu computador)

```bash
cd video-learjet
export ELEVENLABS_API_KEY="a_tua_chave"      # não faças commit da chave
export ELEVENLABS_VOICE_ID="id_da_voz"       # recomendado: voz grave de narrador documental (EN)
python3 elevenlabs_tts.py                    # → audio/scene_*.mp3 + audio/timings.json
```

Depois há duas opções:

**A. Rápida (sem voltar a renderizar):** `python3 mux.py --burn`. A voz de cada cena é colocada no seu slot e ajustada (atempo 0,8–1,25×) à duração planeada. O resultado é `out/final.mp4`, com legendas queimadas e `out/legendas.srt`.

**B. Sincronia perfeita:** volta a renderizar com os tempos reais da voz, porque cada animação está presa ao início de cada frase:

```bash
npm install                       # three.js
npm i -D playwright && npx playwright install chromium
./render_all.sh                   # → out/video_silent.mp4 (lê audio/timings.json)
python3 mux.py --burn             # → out/final.mp4
```

## Ficheiros

- `index.html`: todas as cenas (Three.js + overlay canvas 2D). Abre-se com `window.renderFrame(t)`.
- `render.mjs` / `render_all.sh`: renderização determinística frame a frame → H.264 1080p30.
- `mux.py`: design sonoro gerado por código (drone, vento, chuva, trovões sincronizados com os relâmpagos), ducking sob a voz, loudnorm −14 LUFS e legendas SRT a partir do alinhamento por carácter do ElevenLabs.
- `out/video_sem_voz_web.mp4`: vídeo final com som ambiente, comprimido (< 100 MB) para o GitHub e pronto para receber a voz. A versão de qualidade máxima (`out/video_sem_voz.mp4`, ~670 MB) gera-se localmente com `./render_all.sh && python3 mux.py`.
