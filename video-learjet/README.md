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

Em todos os capítulos há legendas cinéticas: cada palavra aparece quando é dita, e números, perigo, gelo e física têm cores próprias. Os cortes são whip-pans, a câmara faz punch-in nas palavras-chave e treme com os relâmpagos. Os títulos aparecem letra a letra.

0. **Cold open** (de dia): o jato passa a FL350 em céu limpo, o cumulonimbo surge à frente, o avião entra na célula e mergulha com o contador de altitude 35,000 → 8,750 ft. Título *SIXTY SECONDS* sobre as nuvens iluminadas pelo sol.
1. **Flight N722BD**: rota Austin → Golfo do México e descida do mapa regional até ao nível da rua em Greenacres. O local fica na Military Trail junto à 10th Ave N, a ~7 km da praia, com a I-95, a Lake Worth Lagoon e o aeroporto PBI. Mostra a cratera na estrada e o lugar da direita no cockpit.
2. **The Right Seat**: idades mínimas da FAA (17 · 18 · SIC · 23), com um ângulo de câmara por frase.
3. **Into the Storm**: tráfego rádio, cumulonimbo em raio-X filmado de quatro ângulos e congelamento instantâneo no bordo de ataque.
4. **Ice**: escoamento potencial exato num perfil de Joukowski, gelo em "cornos", separação e curva CL–α.
5. **The Coffin Corner**: "paredes" de perda e de Mach que se fecham à volta do jato (atmosfera ISA).
6. **Overspeed**: mergulho, onda de choque, Mach tuck, carga ∝ v² e conclusão preliminar do NTSB.
7. **What We Don't Know**: prazos do NTSB, contorno de 20 NM e memória das nove vítimas.

## Gerar a voz com o ElevenLabs (no teu computador)

```bash
cd video-learjet
export ELEVENLABS_API_KEY="a_tua_chave"      # não faças commit da chave
export ELEVENLABS_VOICE_ID="id_da_voz"       # recomendado: voz grave de narrador documental (EN)
python3 elevenlabs_tts.py                    # → audio/scene_*.mp3 + audio/timings.json
```

Depois há duas opções:

**A. Rápida (sem voltar a renderizar):** `python3 mux.py`. A voz de cada cena é colocada no seu slot e ajustada (atempo 0,8–1,25×) à duração planeada. O resultado é `out/final.mp4`, mais `out/legendas.srt` para o YouTube. Não uses `--burn`, porque as legendas cinéticas já fazem parte da imagem.

**B. Sincronia perfeita (recomendado):** volta a renderizar com os tempos reais da voz. Assim cada palavra das legendas cinéticas, cada corte e cada punch-in coincidem com a narração:

```bash
npm install                       # three.js
npm i -D playwright && npx playwright install chromium
./render_all.sh                   # → out/video_silent.mp4 (lê audio/timings.json)
python3 mux.py                    # → out/final.mp4
```

## Ficheiros

- `index.html`: todas as cenas (Three.js + overlay canvas 2D). Abre-se com `window.renderFrame(t)`.
- `render.mjs` / `render_all.sh`: renderização determinística frame a frame → H.264 1080p30.
- `mux.py`: design sonoro gerado por código (drone, vento, chuva, trovões sincronizados com os relâmpagos), ducking sob a voz, loudnorm −14 LUFS e legendas SRT a partir do alinhamento por carácter do ElevenLabs.
- `out/video_sem_voz_web.mp4`: vídeo final com som ambiente, comprimido (< 100 MB) para o GitHub e pronto para receber a voz. A versão de qualidade máxima (`out/video_sem_voz.mp4`, ~670 MB) gera-se localmente com `./render_all.sh && python3 mux.py`.
