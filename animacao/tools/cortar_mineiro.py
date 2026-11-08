"""Corta o desenho original do mineiro em peças de fantoche (cutout).

Uso: python3 animacao/tools/cortar_mineiro.py <imagem-original> <pasta-saida>

Gera, todas com o mesmo tamanho e origem (coordenadas partilhadas):
  head.png, torso.png, legL.png, legR.png, arms.png, arms_empty.png,
  mouth_closed.png e rig.json (olhos, pupilas, boca, pivots).
Onde uma peça tapava outra, a textura de baixo é reconstruída (inpainting)
para não aparecerem buracos quando as peças rodam.
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SRC, OUT = sys.argv[1], sys.argv[2]
CROP = (200, 175, 780, 910)          # x0, y0, x1, y1 na imagem original
W, H = CROP[2] - CROP[0], CROP[3] - CROP[1]

img = np.asarray(Image.open(SRC).convert('RGB')).astype(float)

# ---------------------------------------------------------------- recorte
mn, mx = img.min(2), img.max(2)
white = (mn > 228) & ((mx - mn) < 14)
lab, _ = ndi.label(white)
bg_ids = {lab[0, 0]}
# zona de fundo fechada entre o braço e o cabo (encontrada por análise)
bg_ids.add(lab[670, 652])
bg = np.isin(lab, list(bg_ids))
band = ndi.binary_dilation(bg, iterations=2) & ~bg
lum = img.mean(2)
alpha = np.where(bg, 0.0, 1.0)
alpha[band] = np.clip((250 - lum[band]) / 180, 0, 1)
rgb = img.copy()
for c in range(3):
    v = (img[..., c] - (1 - alpha) * 255) / np.maximum(alpha, 1e-3)
    rgb[..., c][band] = np.clip(v[band], 0, 255)

x0, y0, x1, y1 = CROP
rgb = rgb[y0:y1, x0:x1]
alpha = alpha[y0:y1, x0:x1]
eyes_lab = lab[y0:y1, x0:x1]
def main_label(bx0, by0, bx1, by1):
    v = eyes_lab[by0:by1, bx0:bx1].ravel()
    v = v[v > 0]
    return int(np.bincount(v).argmax())


eye_ids = [main_label(305, 185, 368, 255), main_label(422, 175, 480, 245)]  # olho esq., olho dir.


def poly_mask(*polys):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon(p, fill=255)
    return np.asarray(m) > 0


solid = alpha > 0.02

# ------------------------------------------------------------ regiões
ARM_L = [(178, 440), (212, 412), (258, 418), (284, 468), (286, 520), (306, 545), (306, 616),
         (252, 620), (220, 592), (204, 540), (180, 522)]
ARM_R = [(436, 430), (462, 408), (492, 410), (514, 436), (516, 478), (548, 484), (548, 548), (462, 548),
         (446, 505), (434, 468)]
SHOVEL = [(0, 575), (200, 575), (556, 458), (580, 470), (580, 500), (206, 636), (200, 700), (0, 700)]
arms = poly_mask(ARM_L, ARM_R, SHOVEL) & solid

yy, xx = np.mgrid[0:H, 0:W]
lum_c = lum[y0:y1, x0:x1]
# interior da cabeça = zonas claras/coloridas ligadas à cara, boina, orelha e cabelo;
# depois dilata-se para apanhar o contorno e fecham-se os buracos (olhos, nariz).
inside = solid & (lum_c > 95)
ilab, _ = ndi.label(inside)
seeds = [(400, 330), (300, 60), (180, 262), (190, 200), (420, 140), (250, 300), (470, 300)]
ids = {int(ilab[y, x]) for x, y in seeds if ilab[y, x] > 0}
head_core = np.isin(ilab, list(ids)) & (yy < 395)
head = ndi.binary_fill_holes(ndi.binary_dilation(head_core, iterations=5)) & solid & ~arms
head |= ((yy < 150) | poly_mask([(140, 118), (228, 118), (228, 300), (140, 300)])) & solid & ~arms

LEG_L = [(232, 612), (338, 612), (342, 700), (312, 735), (225, 735), (228, 680)]
LEG_R = [(348, 612), (448, 600), (452, 690), (480, 698), (480, 735), (356, 735), (352, 690)]
legL_vis = poly_mask(LEG_L) & solid & ~arms
legR_vis = poly_mask(LEG_R) & solid & ~arms
torso = solid & ~arms & ~head & ~legL_vis & ~legR_vis


def inpaint(rgb_, region, radius=6, known=None):
    """Preenche `region` só a partir dos píxeis `known` (cor do vizinho mais próximo,
    suavizada, com um pouco de grão para não parecer uma mancha lisa)."""
    if known is None:
        known = ~region
    _, (iy, ix) = ndi.distance_transform_edt(~known, return_indices=True)
    ext = rgb_[iy, ix]
    blur = cv2.GaussianBlur(ext.astype(np.float32), (0, 0), radius * 0.8).astype(float)
    grain = np.random.default_rng(1).normal(0, 4, ext.shape[:2])[..., None]
    out = rgb_.copy()
    out[region] = np.clip(blur[region] + grain[region], 0, 255)
    return out


def save(name, rgb_, a):
    a = np.clip(a, 0, 1)
    out = np.where(a[..., None] > 0, np.clip(rgb_, 0, 255), 0)
    Image.fromarray(np.dstack([out, a * 255]).astype(np.uint8)).save(f'{OUT}/{name}', optimize=True)


# tronco: reconstrói o que estava por baixo da cabeça e dos braços (dentro da silhueta)
torso_hull = ndi.binary_closing(torso | legL_vis | legR_vis, iterations=25)
torso_hull &= poly_mask([(200, 360), (500, 360), (500, 640), (200, 640)])
under_head = head & poly_mask([(285, 350), (435, 350), (435, 395), (285, 395)])
under_arms = arms & ndi.binary_dilation(torso, iterations=14)
torso_fill = (torso_hull & ~torso) | under_head | under_arms
torso_fill &= ~(legL_vis | legR_vis)
torso_rgb = inpaint(rgb, torso_fill, 6, known=torso & (alpha > 0.9))
torso_a = np.where(torso, alpha, 0.0)
torso_a[torso_fill] = 1.0
# o tronco acaba na anca (as pernas ficam por baixo)
torso_a[612:, :] = 0
save('torso.png', torso_rgb, torso_a)

# pernas: prolongam-se para cima, por baixo do tronco, e reconstroem a parte tapada pela luva
for name, vis, poly in (('legL.png', legL_vis, LEG_L), ('legR.png', legR_vis, LEG_R)):
    ext = poly_mask([(p[0], p[1] - 40 if p[1] <= 612 else p[1]) for p in poly]) & ~vis
    ext &= poly_mask(poly) | (yy < 612)
    fill = (ext & (yy >= 572) & (yy < 612)) | (poly_mask(poly) & arms)
    leg_rgb = inpaint(rgb, fill, 4, known=vis & (alpha > 0.9))
    leg_a = np.where(vis, alpha, 0.0)
    leg_a[fill] = 1.0
    save(name, leg_rgb, leg_a)

# braços + pá (carregada)
save('arms.png', rgb, np.where(arms, alpha, 0.0))
# pá vazia: tira o carvão da lâmina
coal = poly_mask([(24, 600), (165, 596), (180, 640), (110, 668), (40, 655)]) & (lum[y0:y1, x0:x1] < 70) & arms
coal = ndi.binary_dilation(coal, iterations=3) & poly_mask([(18, 590), (178, 590), (188, 648), (100, 676), (30, 664)])
metal = arms & poly_mask([(18, 590), (178, 590), (188, 648), (100, 676), (30, 664)]) & ~coal & (lum_c > 75)
save('arms_empty.png', inpaint(rgb, coal, 3, known=metal), np.where(arms, alpha, 0.0))

# ------------------------------------------------- cabeça: olhos e boca
head_rgb = rgb.copy()
rig = {'size': [W, H], 'eyes': []}
for eid in eye_ids:
    em = ndi.binary_fill_holes(eyes_lab == eid)
    ys, xs = np.where(em)
    cx, cy = xs.mean(), ys.mean()
    rx, ry = (xs.max() - xs.min()) / 2, (ys.max() - ys.min()) / 2
    inner = ndi.binary_erosion(em, iterations=1)
    pup = inner & (lum[y0:y1, x0:x1] < 120)
    py, px = np.where(pup)
    pr = np.sqrt(pup.sum() / np.pi)
    head_rgb[ndi.binary_dilation(pup, iterations=1) & inner] = [250, 250, 250]
    rig['eyes'].append({'cx': float(cx), 'cy': float(cy), 'rx': float(rx + 1), 'ry': float(ry + 1),
                        'px': float(px.mean()), 'py': float(py.mean()), 'pr': float(pr)})

MOUTH = (364, 280, 436, 316)
mx0, my0, mx1, my1 = MOUTH
m_reg = np.zeros((H, W), bool)
m_reg[my0:my1, mx0:mx1] = True
mouth_line = m_reg & (lum[y0:y1, x0:x1] < 110)
mouth_sprite_a = np.where(ndi.binary_dilation(mouth_line, iterations=1), alpha, 0.0)
save('mouth_closed.png', rgb, mouth_sprite_a)
mfill = ndi.binary_dilation(mouth_line, iterations=3)
head_rgb = inpaint(head_rgb, mfill, 2, known=head & ~mfill & (lum_c > 95))
save('head.png', head_rgb, np.where(head, alpha, 0.0))

# cor de pele média da testa (para pálpebras e bocas)
skin = np.median(rgb[160:178, 385:415].reshape(-1, 3), 0)
rig['skin'] = [int(v) for v in skin]
rig['mouth'] = {'x0': mx0, 'y0': my0, 'x1': mx1, 'y1': my1,
                'cx': float(np.where(mouth_line)[1].mean()), 'cy': float(np.where(mouth_line)[0].mean())}
rig['pivots'] = {'neck': [358, 382], 'shoulders': [360, 440], 'hipL': [287, 606], 'hipR': [398, 606], 'waist': [345, 600]}
json.dump(rig, open(f'{OUT}/rig.json', 'w'), indent=1)
print(json.dumps(rig, indent=1))
