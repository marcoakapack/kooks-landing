# Estilo cutout: regras aplicadas

Resumo da pesquisa sobre como a série é produzida. **Confirmado** quer dizer que vem de uma fonte; **observação** quer dizer que vem de ver a série.

## Produção (confirmado)
- O piloto foi feito com cartolina e stop-motion. Depois a produção passou para o PowerAnimator e, a partir da temporada 5, para o Maya. As personagens são planos 2D dentro de software 3D. Fonte: AWN, *Dig This!* (1998).
- Animam a **24 fps** e mexem personagens e adereços **a cada 2 frames**. Fonte: Q&A oficial da South Park Studios.
- A textura de cartolina do piloto foi digitalizada e ainda é usada. A sombra fina entre peças vem de separar as camadas um pouco no espaço ("no-platen shadow"). Fontes: AWN e FAQ oficial.
- Os fantoches trocam peças em vez de deformar. Um slider escolhe a cabeça de frente ou de lado e a boca. Cada personagem tem pelo menos 4 vistas (frente, trás, esquerda, direita). Fontes: Everwonder e Game Informer (2016).
- A sincronização labial é feita à mão por um departamento próprio, com folhas de exposição. Fonte: BTL News.
- Regras de um antigo animador: **pestanejar antes de falar** e **a cabeça vira antes do corpo**. Fonte: Game Informer (2016).

## Como está no código
| Regra | Implementação |
|---|---|
| Poses a cada 2 frames, sem easing | `twos(t)`; cada mudança é uma troca seca de pose |
| Câmara suave, personagens aos solavancos | só a câmara usa o tempo contínuo |
| Andar sem pernas | os pés deslizam alternadamente; salto de cerca de 6% da cabeça só na pose de impulso; sem inclinação; 4 passos/s |
| Parar | passa logo à pose de repouso, sem assentar |
| Bocas | conjunto fixo (`closed`, `small`, `mid`, `wide`, `ee`, `oo`) marcado por sílaba em `SHEET_*` |
| 3/4 | olhos e boca deslizam para o lado da cabeça; a cabeça em si não roda |
| Quem ouve | totalmente parado, só pestaneja |
| Gestos | 1 pose intermédia, depois pose final mantida |
| Impacto | 1 pose de "puf", desenho de reação (olhos > <) com rotação rígida de cerca de 20°, tremor de câmara de 2 poses |
| Cenário | sem contornos nem sombras; só as personagens e a placa têm contorno |
| Papel | textura em *multiply* dentro de cada forma, presa a cada peça |
| Planos | geral, depois grande plano de quem fala (parallax em 3 camadas), depois geral |

## Limites
- Não há som. As falas aparecem como legendas, que a série não usa.
- Os valores numéricos (bob, ângulos, cores) vêm de observação. Nenhuma fonte os publica.
