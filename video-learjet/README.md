# 60 segundos de queda: a física do acidente do Learjet 60 na Flórida

Vídeo explicativo para um canal de ciência e física. A animação, o motion design e o som ambiente são 100% código: Three.js em Chromium headless, renderizado frame a frame e codificado com ffmpeg. Não foram usadas IAs de imagem ou vídeo. A voz é gerada no ElevenLabs.

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

## Estrutura (≈ 4 min 14 s)

1. **A queda**: HUD de altitude 35 000 → 8 750 pés, título.
2. **O que sabemos**: mapa 3D com a rota Austin → Greenacres e as vítimas.
3. **Uma copiloto de 20 anos?**: linha temporal das licenças FAA (PPL aos 17, CPL aos 18, ATP aos 23).
4. **Dentro da trovoada**: cumulonimbo 3D com correntes ascendentes, nível de congelação e água em sobrefusão.
5. **Gelo na asa**: escoamento potencial exato num perfil de Joukowski (condição de Kutta), gelo em "cornos", separação e gráfico CL-α.
6. **O canto do caixão**: atmosfera padrão ISA calculada; velocidade de perda vs. limite Vmo/Mmo.
7. **Overspeed**: descida, 32 000 pés/min = 163 m/s = 585 km/h, onda de choque, Mach tuck, força ∝ v².
8. **O que falta saber**: prazos do NTSB, desvio de 20 NM no radar, memória das vítimas.

O guião completo está em `script.json`, já preparado para o ElevenLabs.

## Gerar a voz com o ElevenLabs (no teu computador)

```bash
cd video-learjet
export ELEVENLABS_API_KEY="a_tua_chave"      # não faças commit da chave
export ELEVENLABS_VOICE_ID="id_da_voz"       # recomendado: uma voz pt-PT da Voice Library
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
- `out/video_sem_voz.mp4`: vídeo final com som ambiente, pronto para receber a voz.
