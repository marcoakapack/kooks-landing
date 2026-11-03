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

## Estrutura (≈ 3 min 45 s)

O canal é de ciência e não de notícias. O acidente é o ponto de partida e o vídeo explica a física, sem nomes nem pormenores pessoais.

Em todos os capítulos há legendas cinéticas: cada palavra aparece quando é dita, e números, perigo, gelo e física têm cores próprias. Os cortes são whip-pans, a câmara faz punch-in nas palavras-chave e os títulos aparecem letra a letra.

0. **Cold open** (de dia): o jato a FL350, o cumulonimbo à frente, a entrada na célula e o mergulho de 35,000 → 8,750 ft. Título *SIXTY SECONDS*.
1. **Flight N722BD**: a rota e a descida do mapa até ao nível da rua em Greenacres (Military Trail / 10th Ave N, ~7 km da praia). Termina com os dados de voo e a frase-ponte "it is a story about physics".
2. **Into the Storm**: cumulonimbo em raio-X (correntes ascendentes, nível de congelação, água em sobrefusão) e congelamento no bordo de ataque.
3. **Ice**: escoamento potencial num perfil de Joukowski, gelo, separação e curva CL–α.
4. **The Coffin Corner**: as "paredes" de perda e de Mach (atmosfera ISA).
5. **Overspeed**: mergulho, onda de choque, Mach tuck, carga ∝ v² e nota preliminar do NTSB.
6. **What We Don't Know**: prazos do NTSB, contorno de 20 NM e homenagem genérica às nove vítimas.

## Voz gerada no site do ElevenLabs (sem API)

Põe os MP3 em `audio/scene_00_hook.mp3` … `audio/scene_06_outro.mp3` e corre `python3 align_audio.py`. O script deteta as pausas do áudio e escreve `audio/timings.json`, com o tempo de cada palavra (erro típico ≈ 0,07 s). Depois segue a opção B em baixo.

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
