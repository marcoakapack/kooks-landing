// Isometric "machine" figures in the style of Anatomy (github.com/wheresryan22/anatomy, MIT),
// built with its kit (iso-kit.mjs). Each function returns a standalone SVG string for one frame.
import * as k from './iso-kit.mjs';

const RED = '#FF4A55', GREEN = '#6CF2B0', CYAN = '#6FD8FF';
// video look: navy-tinted paper to sit on the film's background, heavier lines for 1080p
const VIDEO_CSS = `
.iso{--anatomy-paper:#0b1018;--anatomy-face:#141b26;--anatomy-top:#161e2a;
--anatomy-shade-0:#080c13;--anatomy-shade-1:#0b1119;--anatomy-shade-2:#0f151f;--anatomy-shade-3:#121a25;
--anatomy-lit-top:#22303f;--anatomy-lit-shade:#1a2532;
--anatomy-hi:#e2ebf5;--anatomy-mid:#7f8da0;--anatomy-lo:#4a5668;--anatomy-faint:#2a3342;--anatomy-lit:#ffffff;
--anatomy-halo:#000;--anatomy-halo-opacity:.9;--anatomy-dot:#e6eef8;--anatomy-weight:1.7px;
--anatomy-red:${RED};--anatomy-green:${GREEN};--anatomy-blue:${CYAN}}
.iso-dots circle{opacity:.55}
.iso-face-text{font-family:Inter,sans-serif;font-weight:700}
.glow-red .iso-fill,.glow-red .iso-top,.glow-red .iso-shade{fill:${RED}}
.glow-green .iso-fill,.glow-green .iso-top,.glow-green .iso-shade{fill:${GREEN}}
.glow-cyan .iso-fill,.glow-cyan .iso-top,.glow-cyan .iso-shade{fill:${CYAN}}
`;
const svgOf = (w, h, body) => k.figureSvg({ width: w, height: h, label: 'figure', body, standalone: 'dark' })
  .replace('</style>', VIDEO_CSS + '</style>');

const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const fillPath = (pts, P, color, op = 1) => `<path d="${k.pathOf(pts.map(p => k.iso(p, P)), true)}" fill="${color}" fill-opacity="${op.toFixed(3)}" stroke="none"/>`;

function basePlate(PLATE, P, { h = 14, foot = 6, screws = true } = {}) {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -h - foot, h, P)}"/>`];
  const byDepth = pts => [...pts].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
  for (const [x, y] of byDepth(k.corners(PLATE, 24))) {
    out.push(S(k.cylinder(x, y, 8, -h - foot, 2, P, 28), { tone: 'lo' }));
    out.push(S(k.cylinder(x, y, 6, -h - foot + 2, foot - 2, P, 28), { tone: 'mid' }));
  }
  out.push(S(k.slabOf(PLATE, -h, h, P, 8, 1.6), { tone: 'mid' }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 6), 0, P), { tone: 'lo' }));
  if (screws) {
    const sc = k.corners(PLATE, 12);
    out.push(L(sc.map(([x, y]) => k.ring(x, y, 2.6, 0, P, 16)).join(''), { tone: 'lo' }));
    out.push(k.dotsSvg(sc.map(([x, y]) => k.iso([x, y, 0], P)), { size: 1.1 }));
  }
  return out.join('');
}
function labelPlate(plan, z, P) {
  const out = [S(k.slabOf(plan, z, 1.2, P, 4), { tone: 'lo', crease: 'none' })];
  for (let i = 0; i < 3; i++) { const y = plan.y + 5 + i * (plan.d - 10) / 2; out.push(L(k.lineOnTop([plan.x + 5, y], [plan.x + plan.w * (i === 0 ? .8 : .55), y], z + 1.2, P), { tone: i ? 'faint' : 'lo', free: true })); }
  out.push(k.dotsSvg([[plan.x + 2.5, plan.y + plan.d / 2], [plan.x + plan.w - 2.5, plan.y + plan.d / 2]].map(([x, y]) => k.iso([x, y, z + 1.2], P)), { size: .9 }));
  return out.join('');
}
function ruler(strip, z, P) {
  const out = [S(k.slabOf(strip, z, .8, P, 3), { tone: 'lo', crease: 'none' })];
  const t = k.topTicks(strip.x + 5, strip.x + strip.w - 5, 5, 5, strip.y + 1, z + .8, [2.5, 4.5], P);
  out.push(L(t.minor, { tone: 'lo' }), L(t.major, { tone: 'mid' }));
  return out.join('');
}

/* ---------------- Fig 1 · the timing wheel ----------------
   One turn of the disc = one heartbeat. A thin red sector = the vulnerable window (3% of the turn).
   A drop-hammer over the rim strikes at a moment the disc does not choose: the lamp turns red only
   when the sector is under the hammer. */
const WW = 1000, WH = 760;
const PLATE = { x: -170, y: -150, w: 340, d: 300, r: 12 };
const DISC = [10, 15], DR = 112, DZ = 22, DH = 10, DTOP = DZ + DH;
export const HAMMER_ANGLE = -Math.PI * .75;          // rim point under the hammer (back-left, toward the post)
const HX = DISC[0] + Math.sin(HAMMER_ANGLE) * (DR - 14), HY = DISC[1] - Math.cos(HAMMER_ANGLE) * (DR - 14);
const POST = [-150, -40], POST_TOP = 190, ARM_Z = 170;
const LAMP = [125, 115];
const PW = k.fitProjection([...k.boxCorners(PLATE, -20, 0), [POST[0], POST[1], POST_TOP + 10], [HX, HY, ARM_Z + 40]], WW, WH, { pad: 40, azimuth: 40 });
export const WIN_FROM = .445, WIN_W = .03;           // window position in the beat (T-wave upslope), 3% wide

export function wheelFigure({ phase = 0, lift = 1, lamp = 0, lampColor = 'red', sector = 1, glowTurn = 0 } = {}) {
  const P = PW, out = [];
  out.push(basePlate(PLATE, P));
  out.push(ruler({ x: PLATE.x + 30, y: PLATE.y + PLATE.d - 22, w: 200, d: 10, r: 1 }, 0, P));
  out.push(labelPlate({ x: PLATE.x + PLATE.w - 92, y: PLATE.y + 16, w: 74, d: 28, r: 2 }, 0, P));
  // post + arm (behind the disc)
  out.push(S(k.cylinder(POST[0], POST[1], 16, 0, 6, P, 32, .8), { tone: 'lo' }));
  out.push(L(k.ring(POST[0], POST[1], 12, 6, P, 24), { tone: 'faint' }));
  out.push(S(k.cylinder(POST[0], POST[1], 7, 6, POST_TOP - 6, P, 28), { tone: 'mid' }));
  out.push(S(k.cylinder(POST[0], POST[1], 9, ARM_Z - 6, 18, P, 28, .6), { tone: 'mid' }));
  out.push(k.knurl(POST[0], POST[1], 9, ARM_Z - 4, ARM_Z + 10, 18, P) ? L(k.knurl(POST[0], POST[1], 9, ARM_Z - 4, ARM_Z + 10, 18, P), { tone: 'lo' }) : '');
  // disc hub + disc
  out.push(S(k.cylinder(DISC[0], DISC[1], 30, 0, DZ, P, 40, .6), { tone: 'mid' }));
  out.push(S(k.cylinder(DISC[0], DISC[1], DR, DZ, DH, P, 96, 1.2), { tone: 'hi', lit: glowTurn > 0 }));
  // rotating marks: ticks (50 per beat), the window sector, the beat index
  const rot = HAMMER_ANGLE - phase * Math.PI * 2;   // a point at beat-phase p sits at angle rot + p·2π; under the hammer when p = phase
  const t = k.radialTicks(DISC[0], DISC[1], DR - 6, 50, 5, DTOP, [6, 13], P, rot);
  out.push(L(t.minor, { tone: 'lo' }), L(t.major, { tone: 'mid' }));
  out.push(L(k.ring(DISC[0], DISC[1], DR - 24, DTOP, P, 80), { tone: 'faint' }));
  const arc = (r, a0, a1, n = 14) => Array.from({ length: n + 1 }, (_, i) => { const a = a0 + (a1 - a0) * i / n; return [DISC[0] + Math.sin(a) * r, DISC[1] - Math.cos(a) * r, DTOP + .2]; });
  const a0 = rot + WIN_FROM * Math.PI * 2, a1 = rot + (WIN_FROM + WIN_W) * Math.PI * 2;
  if (sector > 0) out.push(fillPath([...arc(DR - 3, a0, a1), ...arc(DR - 40, a1, a0)], P, RED, .9 * sector));
  // the QRS mark: a lit wedge at phase .2
  const q0 = rot + .195 * Math.PI * 2, q1 = rot + .21 * Math.PI * 2;
  out.push(fillPath([...arc(DR - 3, q0, q1, 4), ...arc(DR - 22, q1, q0, 4)], P, GREEN, .8));
  out.push(S(k.cylinder(DISC[0], DISC[1], 14, DTOP, 6, P, 32, .6), { tone: 'mid' }));
  out.push(k.dotsSvg([0, 1, 2, 3, 4, 5].map(i => { const a = rot + i * Math.PI / 3; return k.iso([DISC[0] + Math.sin(a) * 22, DISC[1] - Math.cos(a) * 22, DTOP], P); }), { size: 1.4, tone: 'mid' }));
  // arm from the post to the hammer guide
  const ARM = { x: POST[0], y: POST[1] - 9, w: 1, d: 18, r: 2 };
  const dx = HX - POST[0], dy = HY - POST[1], len = Math.hypot(dx, dy), ux = dx / len, uy = dy / len;
  const ring = [[POST[0] - uy * 9, POST[1] + ux * 9], [HX - uy * 9 + ux * 14, HY + ux * 9 + uy * 14], [HX + uy * 9 + ux * 14, HY - ux * 9 + uy * 14], [POST[0] + uy * 9, POST[1] - ux * 9]];
  out.push(S(k.extrude(ring, ARM_Z, 10, P, { bevel: .6 }), { tone: 'mid' }));
  out.push(S(k.cylinder(HX, HY, 14, ARM_Z - 4, 18, P, 32, .8), { tone: 'mid' }));
  // hammer: rod through the guide, spring, head
  const headZ = DTOP + 2 + lift * 70;
  out.push(S(k.cylinder(HX, HY, 3.5, headZ + 18, ARM_Z + 40 - headZ - 18 + 14, P, 20), { tone: 'mid' }));
  for (let i = 0, n = 7; i <= n; i++) out.push(L(k.sideArc(HX, HY, 8, headZ + 22 + (ARM_Z - 6 - headZ - 22) * i / n, P), { tone: 'mid' }));
  out.push(S(k.cylinder(HX, HY, 13, headZ, 18, P, 36, 1.2), { tone: 'hi', lit: true }));
  out.push(S(k.cylinder(HX, HY, 6, ARM_Z + 40, 6, P, 24, .5), { tone: 'mid' }));
  // lamp
  out.push(S(k.cylinder(LAMP[0], LAMP[1], 15, 0, 8, P, 32, .8), { tone: 'mid' }));
  out.push(S(k.cylinder(LAMP[0], LAMP[1], 10, 8, 14, P, 32, 1.5), { tone: 'hi', className: lamp > .05 ? `glow-${lampColor}` : undefined }));
  return svgOf(WW, WH, out.join(''));
}
export const wheelPoint = (name) => {      // screen points (in figure units) for canvas overlays
  const p = name === 'lamp' ? [LAMP[0], LAMP[1], 22] : name === 'hammer' ? [HX, HY, DTOP] : [DISC[0], DISC[1], DTOP];
  const [x, y] = k.iso(p, PW); return [x / WW, y / WH];
};
export const WHEEL_SIZE = [WW, WH];

/* ---------------- Fig 2 · the defibrillator ----------------
   A case with a charge gauge (joules), a shock button and two pads on leads. The needle climbs while it
   charges; the shock empties it at once, and the leads light. */
const DW = 1000, DHH = 720;
const DPLATE = { x: -200, y: -140, w: 400, d: 280, r: 12 };
const CASE = { x: -150, y: -110, w: 200, d: 150, r: 18 }, CASE_H = 46;
const GAUGE = [-50, -40], GR = 40;
const BTN = [10, 10];
const PADS = [[110, -60], [110, 70]];
const PD = k.fitProjection([...k.boxCorners(DPLATE, -20, 0), [CASE.x, CASE.y, CASE_H + 30]], DW, DHH, { pad: 40, azimuth: 50 });
export function defibFigure({ charge = 0, flash = 0, ready = 0 } = {}) {
  const P = PD, out = [];
  out.push(basePlate(DPLATE, P));
  out.push(ruler({ x: DPLATE.x + 24, y: DPLATE.y + DPLATE.d - 22, w: 160, d: 10, r: 1 }, 0, P));
  // case
  out.push(`<path class="iso-halo" d="${k.haloOf(CASE, 0, CASE_H, P)}"/>`);
  out.push(S(k.slabOf(CASE, 0, CASE_H, P, 10, 2), { tone: 'mid', inner: L(k.sideSeam(CASE, CASE_H * .45, P), { tone: 'lo' }) }));
  out.push(L(k.planOutline(k.insetPlan(CASE, 8), CASE_H, P), { tone: 'lo' }));
  // handle on the back edge
  for (const x of [CASE.x + 30, CASE.x + CASE.w - 30]) out.push(S(k.cylinder(x, CASE.y + 14, 5, CASE_H, 18, P, 20), { tone: 'mid' }));
  out.push(S(k.slabOf({ x: CASE.x + 22, y: CASE.y + 8, w: CASE.w - 44, d: 12, r: 6 }, CASE_H + 18, 8, P, 6, .6), { tone: 'mid' }));
  // speaker grille + label
  out.push(k.dotsSvg(Array.from({ length: 30 }, (_, i) => k.iso([CASE.x + 30 + (i % 6) * 7, CASE.y + 92 + Math.floor(i / 6) * 7, CASE_H], P)), { size: 1.2, tone: 'lo' }));
  out.push(labelPlate({ x: CASE.x + 22, y: CASE.y + 40, w: 52, d: 26, r: 2 }, CASE_H, P));
  // gauge
  out.push(S(k.cylinder(GAUGE[0] + 30, GAUGE[1] + 30, GR, CASE_H, 4, P, 64, .8), { tone: 'mid' }));
  const gx = GAUGE[0] + 30, gy = GAUGE[1] + 30, gz = CASE_H + 4, span = Math.PI * 1.5, from = -span / 2;
  const tk = k.radialTicks(gx, gy, GR - 5, 20, 5, gz, [4, 8], P, from, span);
  out.push(L(tk.minor, { tone: 'lo' }), L(tk.major, { tone: 'hi' }));
  const arcPts = (r, a0, a1, n = 30) => Array.from({ length: n + 1 }, (_, i) => { const a = a0 + (a1 - a0) * i / n; return [gx + Math.sin(a) * r, gy - Math.cos(a) * r, gz + .2]; });
  if (charge > 0) out.push(fillPath([...arcPts(GR - 4, from, from + span * charge), ...arcPts(GR - 12, from + span * charge, from)], P, RED, .85));
  const na = from + span * charge;
  out.push(L(k.lineOnTop([gx, gy], [gx + Math.sin(na) * (GR - 8), gy - Math.cos(na) * (GR - 8)], gz + .4, P), { tone: 'lit' }));
  out.push(S(k.cylinder(gx, gy, 4, gz, 3, P, 20), { tone: 'hi', lit: true }));
  // shock button
  out.push(S(k.cylinder(BTN[0] + 10, BTN[1] + 10, 20, CASE_H, 4, P, 40, .6), { tone: 'mid' }));
  out.push(S(k.cylinder(BTN[0] + 10, BTN[1] + 10, 14, CASE_H + 4, 6 - ready * 2, P, 40, 1), { tone: 'hi', className: ready > .05 ? 'glow-red' : undefined }));
  // ports on the right side of the case
  const ports = [[CASE.x + CASE.w, CASE.y + 45], [CASE.x + CASE.w, CASE.y + 105]];
  for (const [x, y] of ports) out.push(S(k.extrude(k.circleRing(0, 0, 7, 20).map(([u, v]) => [x + 3 + u * .5, y + u * 0 + v]), CASE_H * .25 - 7, 14, P), { tone: 'mid' }));
  // pads + leads
  PADS.forEach(([px, py], i) => {
    const [ox, oy] = ports[i];
    const a = k.iso([ox + 6, oy, CASE_H * .25], P), b = k.iso([px - 30, py, 6], P), m = k.iso([(ox + px) / 2, (oy + py) / 2 + (i ? 12 : -12), 0], P);
    out.push(k.wireSvg(a, b, { via: [m], tone: flash > .1 ? 'lit' : 'mid', size: 2 }));
    out.push(`<path class="iso-halo" d="${k.haloOf({ x: px - 34, y: py - 26, w: 68, d: 52, r: 10 }, 0, 6, P)}"/>`);
    out.push(S(k.slabOf({ x: px - 34, y: py - 26, w: 68, d: 52, r: 10 }, 0, 5, P, 8, .8), { tone: 'hi', lit: flash > .1 }));
    out.push(L(k.planOutline({ x: px - 26, y: py - 18, w: 52, d: 36, r: 6 }, 5, P), { tone: flash > .1 ? 'lit' : 'lo' }));
    out.push(S(k.cylinder(px - 30, py, 5, 0, 8, P, 16), { tone: 'mid' }));
  });
  return svgOf(DW, DHH, out.join(''));
}
export const defibPoint = (name) => {
  const p = name === 'gauge' ? [GAUGE[0] + 30, GAUGE[1] + 30, CASE_H + 4] : name === 'pad0' ? [...PADS[0], 6] : name === 'pad1' ? [...PADS[1], 6] : [BTN[0] + 10, BTN[1] + 10, CASE_H + 10];
  const [x, y] = k.iso(p, PD); return [x / DW, y / DHH];
};
export const DEFIB_SIZE = [DW, DHH];
