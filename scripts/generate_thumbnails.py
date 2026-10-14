#!/usr/bin/env python3
"""Generate the note thumbnails in assets/covers/notes/ (400x400 SVG).

Usage:
    python3 scripts/generate_thumbnails.py            # rewrite every thumbnail
    python3 scripts/generate_thumbnails.py <out-dir>  # write somewhere else to preview

Same visual system as scripts/generate_covers.py (palette, background, glows),
drawn square with heavier strokes because the cards show them at ~190px.
Keep each subject inside y 70-330: on phones the square is cropped to a
wide strip through the middle.
"""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_covers import BLUSH, CARD, GOLD, INK, MUTED, SKY, TEAL, n, poly_path, sparkle  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
THUMBS_DIR = ROOT / "assets" / "covers" / "notes"
SLATE = "#6f8f9b"


def thumb(body, defs="", glow=(0.85, 0.12), glow_color="#f6d6e0", glow2=(0.1, 0.92), glow2_color="#cfe6ee"):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f8fbfc"/><stop offset="1" stop-color="#e3eef3"/></linearGradient>
<radialGradient id="glow" cx="{glow[0]}" cy="{glow[1]}" r="0.65"><stop offset="0" stop-color="{glow_color}" stop-opacity="0.9"/><stop offset="1" stop-color="{glow_color}" stop-opacity="0"/></radialGradient>
<radialGradient id="glow2" cx="{glow2[0]}" cy="{glow2[1]}" r="0.6"><stop offset="0" stop-color="{glow2_color}" stop-opacity="0.9"/><stop offset="1" stop-color="{glow2_color}" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="#8fb0bc" fill-opacity="0.3"/></pattern>
{defs}
</defs>
<rect width="400" height="400" fill="url(#bg)"/>
<rect width="400" height="400" fill="url(#glow)"/>
<rect width="400" height="400" fill="url(#glow2)"/>
<rect width="400" height="400" fill="url(#dots)"/>
{body}
</svg>
"""


def head(x, y, ang_deg, color, width=4.5, size=13):
    a = math.radians(ang_deg)
    l = (x - size * math.cos(a - 0.5), y - size * math.sin(a - 0.5))
    r = (x - size * math.cos(a + 0.5), y - size * math.sin(a + 0.5))
    return (f'<path d="M{n(l[0])} {n(l[1])}L{n(x)} {n(y)}L{n(r[0])} {n(r[1])}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def arrow(x1, y1, x2, y2, color, width=4.5, size=13):
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return (f'<path d="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
            + head(x2, y2, ang, color, width, size))


def axes(ox, oy, x_end, y_end, color=INK, width=3.5):
    return (f'<path d="M{ox - 14} {oy}H{x_end}M{ox} {oy + 14}V{y_end}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
            + head(x_end, oy, 0, color, width, 11) + head(ox, y_end, -90, color, width, 11))


def dot(x, y, r, fill, stroke="#ffffff", sw=3):
    return f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def grad_v(id_, top, bottom, o1=1.0, o2=1.0):
    return (f'<linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}" stop-opacity="{o1}"/>'
            f'<stop offset="1" stop-color="{bottom}" stop-opacity="{o2}"/></linearGradient>')


def glass(id_="glass"):
    return (f'<radialGradient id="{id_}" cx="0.36" cy="0.3" r="0.8"><stop offset="0" stop-color="#ffffff"/>'
            f'<stop offset="0.6" stop-color="#d6eaf0"/><stop offset="1" stop-color="{SKY}"/></radialGradient>')


# =============================================================== mathematics
def analysis():
    ox, oy = 70, 330

    def Y(x):
        return oy - (40 + 200 / (1 + math.exp(-((x - ox) - 135) / 38)))

    def solve(target):
        lo, hi = ox, 345
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if Y(mid) > target else (lo, mid)
        return (lo + hi) / 2

    a = 205
    ya, eps = Y(a), 40
    xl, xr = solve(ya + eps), solve(ya - eps)
    curve = [(x, Y(x)) for x in range(74, 345, 2)]
    body = f"""
<rect x="{ox}" y="{n(ya - eps)}" width="276" height="{2 * eps}" fill="{BLUSH}" fill-opacity="0.16"/>
<path d="M{ox} {n(ya - eps)}H346M{ox} {n(ya + eps)}H346" stroke="{BLUSH}" stroke-width="2.5" stroke-dasharray="6 7"/>
<rect x="{n(xl)}" y="62" width="{n(xr - xl)}" height="{oy - 62}" fill="{TEAL}" fill-opacity="0.13"/>
<path d="M{n(xl)} 62V{oy}M{n(xr)} 62V{oy}" stroke="{TEAL}" stroke-width="2.5" stroke-dasharray="6 7"/>
{axes(ox, oy, 352, 58)}
<path d="M{a} {n(ya)}V{oy}M{a} {n(ya)}H{ox}" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="4 7"/>
<path d="{poly_path(curve)}" fill="none" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>
{dot(a, ya, 10, GOLD)}
{sparkle(330, 86, 10, GOLD, 0.8)}
"""
    return thumb(body)


def complex_analysis():
    cx, cy, R = 200, 200, 118
    grid = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for r in (40, 80, 120, 160)) + "".join(
        f'<path d="M{cx} {cy}L{n(cx + 175 * math.cos(math.radians(a)))} {n(cy + 175 * math.sin(math.radians(a)))}"/>'
        for a in range(0, 360, 30)
    )
    heads = ""
    for t in (math.radians(45), math.radians(225)):
        px, py = cx + R * math.cos(t), cy - R * math.sin(t)
        heads += head(px, py, math.degrees(math.atan2(-math.cos(t), -math.sin(t))), TEAL, 5.5, 15)
    body = f"""
<g fill="none" stroke="#d3e2e8" stroke-width="1.6">{grid}</g>
<path d="M30 {cy}H370M{cx} 30V370" stroke="{MUTED}" stroke-width="2.5"/>
<circle cx="{cx}" cy="{cy}" r="{R}" fill="{TEAL}" fill-opacity="0.07" stroke="{TEAL}" stroke-width="5.5"/>
{heads}
<circle cx="165" cy="172" r="19" fill="{BLUSH}" fill-opacity="0.18"/>{dot(165, 172, 9, BLUSH)}
<circle cx="242" cy="234" r="19" fill="{BLUSH}" fill-opacity="0.18"/>{dot(242, 234, 9, BLUSH)}
{dot(340, 88, 8, CARD, MUTED, 3)}
{dot(cx + R, cy, 9, GOLD)}
{sparkle(72, 330, 9, SKY, 0.9)}
"""
    return thumb(body)


def math_physics():
    parts = []
    for row, (y, amp, mode, color) in enumerate(((115, 34, 1, TEAL), (200, 30, 2, BLUSH), (285, 26, 3, GOLD))):
        up = [(70 + 260 * t / 100, y - amp * math.sin(mode * math.pi * t / 100)) for t in range(101)]
        down = [(x, 2 * y - yy) for x, yy in up]
        parts.append(f'<path d="{poly_path(up)}{"".join(f"L{n(x)} {n(yy)}" for x, yy in reversed(down))}Z" fill="{color}" fill-opacity="0.13"/>')
        parts.append(f'<path d="{poly_path(down)}" fill="none" stroke="{color}" stroke-width="2.5" stroke-dasharray="5 7" stroke-opacity="0.7"/>')
        parts.append(f'<path d="{poly_path(up)}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
        parts.append(f'<path d="M70 {y - 20}V{y + 20}M330 {y - 20}V{y + 20}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>')
        for k in range(1, mode):
            parts.append(dot(70 + 260 * k / mode, y, 6.5, CARD, color, 3))
    body = "".join(parts) + sparkle(352, 66, 9, GOLD, 0.8) + sparkle(46, 340, 8, SKY, 0.9)
    return thumb(body)


def algebra():
    cx, cy, R = 200, 214, 118

    def tri(offset):
        return [(cx + R * math.cos(math.radians(a + offset)), cy + R * math.sin(math.radians(a + offset))) for a in (-90, 30, 150)]

    main, ghost = tri(0), tri(60)
    mirrors = "".join(
        f'<path d="M{n(cx + 145 * math.cos(math.radians(a)))} {n(cy + 145 * math.sin(math.radians(a)))}'
        f'L{n(cx - 85 * math.cos(math.radians(a)))} {n(cy - 85 * math.sin(math.radians(a)))}"/>'
        for a in (-90, 30, 150)
    )
    r_arc = 150
    a0, a1 = math.radians(-62), math.radians(-12)
    p0 = (cx + r_arc * math.cos(a0), cy + r_arc * math.sin(a0))
    p1 = (cx + r_arc * math.cos(a1), cy + r_arc * math.sin(a1))
    tangent = math.degrees(a1) + 90
    defs = grad_v("tri", "#e6f2f6", "#bcd8e2", 0.9, 0.9)
    body = f"""
<path d="{poly_path(ghost)}Z" fill="{BLUSH}" fill-opacity="0.08" stroke="{BLUSH}" stroke-opacity="0.45" stroke-width="2.5" stroke-dasharray="6 7"/>
<g stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="5 8">{mirrors}</g>
<path d="{poly_path(main)}Z" fill="url(#tri)" stroke="{INK}" stroke-width="5.5" stroke-linejoin="round"/>
<path d="M{n(p0[0])} {n(p0[1])}A{r_arc} {r_arc} 0 0 1 {n(p1[0])} {n(p1[1])}" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
{head(p1[0], p1[1], tangent, GOLD, 5, 15)}
{dot(*main[0], 12, TEAL)}{dot(*main[1], 12, BLUSH)}{dot(*main[2], 12, GOLD)}
<circle cx="{cx}" cy="{cy}" r="5" fill="{INK}"/>
{sparkle(64, 74, 9, SKY, 0.9)}
"""
    return thumb(body, defs)


def number_theory():
    size = 15
    limit = size * size
    sieve = [False, False] + [True] * (limit - 1)
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    pos = [(0, 0)]
    x = y = 0
    step, d = 1, 0
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    while len(pos) < limit:
        for _ in range(2):
            for _ in range(step):
                x, y = x + dirs[d][0], y + dirs[d][1]
                pos.append((x, y))
                if len(pos) == limit:
                    break
            d = (d + 1) % 4
            if len(pos) == limit:
                break
        step += 1
    sp = 19
    pts_ = [(200 + px * sp, 200 + py * sp) for px, py in pos]
    marks = []
    for k, (px, py) in enumerate(pts_, start=1):
        if k == 1:
            continue
        if sieve[k]:
            marks.append(f'<circle cx="{n(px)}" cy="{n(py)}" r="6" fill="url(#prime)"/>')
        else:
            marks.append(f'<circle cx="{n(px)}" cy="{n(py)}" r="2.2" fill="{MUTED}" fill-opacity="0.7"/>')
    defs = f'<radialGradient id="prime" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="{SKY}"/><stop offset="1" stop-color="{TEAL}"/></radialGradient>'
    body = f"""
<path d="{poly_path(pts_)}" fill="none" stroke="#c9dbe1" stroke-width="1.8" stroke-linejoin="round"/>
{"".join(marks)}
{dot(200, 200, 9, GOLD)}
"""
    return thumb(body, defs)


def functional_analysis():
    cx, cy, R = 200, 200, 120

    def ball(p, steps=240):
        out = []
        for i in range(steps):
            t = 2 * math.pi * i / steps
            c, s = math.cos(t), math.sin(t)
            out.append((cx + R * math.copysign(abs(c) ** (2 / p), c), cy - R * math.copysign(abs(s) ** (2 / p), s)))
        return poly_path(out) + "Z"

    diamond = f"M{cx + R} {cy}L{cx} {cy - R}L{cx - R} {cy}L{cx} {cy + R}Z"
    body = f"""
<path d="M{cx - 160} {cy}H{cx + 160}M{cx} {cy - 160}V{cy + 160}" stroke="{MUTED}" stroke-width="2.5"/>
<rect x="{cx - R}" y="{cy - R}" width="{2 * R}" height="{2 * R}" rx="3" fill="none" stroke="{SLATE}" stroke-width="3.5" stroke-dasharray="7 8"/>
<path d="{ball(4)}" fill="{BLUSH}" fill-opacity="0.1" stroke="{BLUSH}" stroke-width="4.5"/>
<circle cx="{cx}" cy="{cy}" r="{R}" fill="{TEAL}" fill-opacity="0.08" stroke="{TEAL}" stroke-width="5"/>
<path d="{diamond}" fill="{GOLD}" fill-opacity="0.14" stroke="{INK}" stroke-width="5.5" stroke-linejoin="round"/>
{dot(cx + R, cy, 9, GOLD)}{dot(cx - R, cy, 9, GOLD)}{dot(cx, cy - R, 9, GOLD)}{dot(cx, cy + R, 9, GOLD)}
{sparkle(338, 66, 9, SKY, 0.9)}
"""
    return thumb(body)


def geometry():
    oc, R = (200, 208), 128
    A, B, C = [(oc[0] + R * math.cos(math.radians(a)), oc[1] + R * math.sin(math.radians(a))) for a in (155, 25, 252)]

    def dist(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])

    a, b, c = dist(B, C), dist(A, C), dist(A, B)
    per = a + b + c
    I = ((a * A[0] + b * B[0] + c * C[0]) / per, (a * A[1] + b * B[1] + c * C[1]) / per)
    s = per / 2
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    r = area / s

    def foot(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        t = ((I[0] - p[0]) * dx + (I[1] - p[1]) * dy) / (dx * dx + dy * dy)
        return p[0] + t * dx, p[1] + t * dy

    feet = [foot(A, B), foot(B, C), foot(C, A)]
    body = f"""
<circle cx="{oc[0]}" cy="{oc[1]}" r="{R}" fill="{TEAL}" fill-opacity="0.07" stroke="{TEAL}" stroke-width="4.5"/>
<path d="{poly_path([A, B, C])}Z" fill="#ffffff" fill-opacity="0.55" stroke="{INK}" stroke-width="5.5" stroke-linejoin="round"/>
<g stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="5 7">{"".join(f'<path d="M{n(p[0])} {n(p[1])}L{n(I[0])} {n(I[1])}"/>' for p in (A, B, C))}</g>
<circle cx="{n(I[0])}" cy="{n(I[1])}" r="{n(r)}" fill="{BLUSH}" fill-opacity="0.14" stroke="{BLUSH}" stroke-width="4.5"/>
{"".join(dot(fx, fy, 5.5, BLUSH, "#ffffff", 2) for fx, fy in feet)}
{dot(*oc, 7, TEAL)}{dot(*I, 8, GOLD)}
{"".join(dot(px, py, 7, INK, "#ffffff", 2.5) for px, py in (A, B, C))}
{sparkle(346, 336, 9, GOLD, 0.8)}
"""
    return thumb(body)


def probability():
    rnd = random.Random(5)
    mu, sigma, peak, base = 200, 48, 196, 320

    def Y(x):
        return base - peak * math.exp(-((x - mu) ** 2) / (2 * sigma ** 2))

    bars = []
    for x in range(56, 344, 18):
        h = (base - Y(x + 9)) * (1 + rnd.uniform(-0.12, 0.12))
        bars.append(f'<rect x="{x + 1}" y="{n(base - h)}" width="16" height="{n(h)}" rx="2"/>')
    curve = [(x, Y(x)) for x in range(40, 361, 2)]
    shade = [(x, Y(x)) for x in range(mu - sigma, mu + sigma + 1, 2)]
    defs = grad_v("hbar", TEAL, SKY, 0.45, 0.15)
    body = f"""
<path d="M{mu - sigma} {base}{''.join(f'L{n(x)} {n(y)}' for x, y in shade)}L{mu + sigma} {base}Z" fill="{BLUSH}" fill-opacity="0.2"/>
<g fill="url(#hbar)" stroke="{TEAL}" stroke-opacity="0.5" stroke-width="1.5">{"".join(bars)}</g>
<path d="M{mu} {base}V{base - peak - 14}" stroke="{GOLD}" stroke-width="3.5" stroke-dasharray="6 7"/>
<path d="M{mu - sigma} {base}V{n(Y(mu - sigma))}M{mu + sigma} {base}V{n(Y(mu + sigma))}" stroke="{BLUSH}" stroke-width="3" stroke-dasharray="4 6"/>
<path d="{poly_path(curve)}" fill="none" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>
<path d="M36 {base}H364" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
{dot(mu, base - peak, 9, GOLD)}
{sparkle(330, 90, 9, SKY, 0.9)}
"""
    return thumb(body, defs)


def topology():
    cx, cy = 200, 205
    outer = f"M{cx - 152} {cy}A152 92 0 1 1 {cx + 152} {cy}A152 92 0 1 1 {cx - 152} {cy}Z"
    hole = f"M{cx - 72} {cy - 4}Q{cx} {cy + 40} {cx + 72} {cy - 4}Q{cx} {cy - 30} {cx - 72} {cy - 4}Z"
    defs = (f'<radialGradient id="torus" cx="0.45" cy="0.3" r="0.8"><stop offset="0" stop-color="#ffffff"/>'
            f'<stop offset="0.55" stop-color="#d3e8ef"/><stop offset="1" stop-color="{SKY}"/></radialGradient>')
    body = f"""
<ellipse cx="{cx}" cy="{cy + 104}" rx="150" ry="18" fill="{INK}" opacity="0.06"/>
<path d="{outer}{hole}" fill="url(#torus)" fill-rule="evenodd" stroke="{INK}" stroke-width="5"/>
<path d="M{cx - 86} {cy + 4}Q{cx} {cy + 58} {cx + 86} {cy + 4}" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>
<ellipse cx="{cx}" cy="{cy}" rx="114" ry="56" fill="none" stroke="{BLUSH}" stroke-width="5"/>
<path d="M{cx} {cy + 31}A17 30 0 0 0 {cx} {cy + 91}" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
<path d="M{cx} {cy + 31}A17 30 0 0 1 {cx} {cy + 91}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-dasharray="5 6"/>
{dot(cx + 114, cy, 8, BLUSH)}{dot(cx, cy + 91, 8, GOLD)}
{sparkle(66, 82, 9, SKY, 0.9)}{sparkle(342, 324, 8, GOLD, 0.8)}
"""
    return thumb(body, defs)


def numerical_analysis():
    axis = 280

    def h(x):
        return 0.0045 * (x - 110) ** 2 - 40

    def hp(x):
        return 0.009 * (x - 110)

    curve = [(x, axis - h(x)) for x in range(70, 344, 2)]
    xs = [330]
    for _ in range(3):
        x = xs[-1]
        xs.append(x - h(x) / hp(x))
    steps = []
    for i in range(3):
        x0, x1 = xs[i], xs[i + 1]
        steps.append(f'<path d="M{n(x0)} {n(axis - h(x0))}L{n(x1)} {axis}" stroke="{BLUSH}" stroke-width="4" stroke-linecap="round"/>')
        steps.append(f'<path d="M{n(x1)} {axis}V{n(axis - h(x1))}" stroke="{MUTED}" stroke-width="3" stroke-dasharray="4 6"/>')
    root = 110 + math.sqrt(40 / 0.0045)
    body = f"""
<path d="M{xs[0]} {axis}V{n(axis - h(xs[0]))}" stroke="{MUTED}" stroke-width="3" stroke-dasharray="4 6"/>
<path d="M44 {axis}H360" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
<path d="{poly_path(curve)}" fill="none" stroke="{INK}" stroke-width="5.5" stroke-linecap="round"/>
{"".join(steps)}
{"".join(dot(x, axis - h(x), r, GOLD) for x, r in zip(xs, (10, 8.5, 7, 6)))}
<circle cx="{n(root)}" cy="{axis}" r="12" fill="none" stroke="{TEAL}" stroke-width="4"/>
{sparkle(76, 92, 9, SKY, 0.9)}
"""
    return thumb(body)


# =================================================================== physics
def mechanics():
    p0, p1 = (60, 318), (340, 150)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    nrm = (d[1], -d[0])
    ang = math.degrees(math.atan2(dy, dx))
    base = (p0[0] + dx * 0.5, p0[1] + dy * 0.5)
    C = (base[0] + 38 * nrm[0], base[1] + 38 * nrm[1])
    arc_end = (p0[0] + 62 * math.cos(math.radians(ang)), p0[1] + 62 * math.sin(math.radians(ang)))
    ticks = "".join(f'<path d="M{x} 318L{x - 12} 332"/>' for x in range(56, 361, 18))
    defs = grad_v("slope", "#e3eff3", "#bcd6e0") + (
        f'<linearGradient id="block" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f9e2e9"/>'
        f'<stop offset="1" stop-color="{BLUSH}"/></linearGradient>')
    body = f"""
<g stroke="{MUTED}" stroke-width="2.5">{ticks}</g>
<path d="M{p0[0]} {p0[1]}L{p1[0]} {p1[1]}L{p1[0]} {p0[1]}Z" fill="url(#slope)" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
<path d="M40 318H364" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>
<path d="M{p0[0] + 62} {p0[1]}A62 62 0 0 0 {n(arc_end[0])} {n(arc_end[1])}" fill="none" stroke="{GOLD}" stroke-width="4"/>
<rect x="-38" y="-38" width="76" height="76" rx="8" transform="translate({n(C[0])} {n(C[1])}) rotate({n(ang)})" fill="url(#block)" stroke="{INK}" stroke-width="4.5"/>
{arrow(C[0], C[1], C[0], C[1] + 104, TEAL, 5)}
{arrow(C[0], C[1], C[0] + 88 * nrm[0], C[1] + 88 * nrm[1], BLUSH, 5)}
{arrow(C[0], C[1], C[0] + 72 * d[0], C[1] + 72 * d[1], GOLD, 5)}
{dot(C[0], C[1], 6, INK, "#ffffff", 2.5)}
{sparkle(84, 86, 9, SKY, 0.9)}
"""
    return thumb(body, defs)


def electromagnetism():
    cx, cy = 200, 200
    lines = []
    for k, op in ((62, 0.95), (95, 0.85), (135, 0.7), (180, 0.55)):
        top, bottom = [], []
        for i in range(1, 200):
            th = math.pi * i / 200
            r = k * math.sin(th) ** 2
            top.append((cx + r * math.cos(th), cy - r * math.sin(th)))
            bottom.append((cx + r * math.cos(th), cy + r * math.sin(th)))
        lines.append(f'<path d="{poly_path(top)}" stroke-opacity="{op}"/><path d="{poly_path(bottom)}" stroke-opacity="{op}"/>')
        # Outside the magnet the field runs from N (left) round to S (right).
        top_y = min(p[1] for p in top)
        lines.append(head(cx + 7, top_y, 0, TEAL, 4, 11))
        lines.append(head(cx + 7, 2 * cy - top_y, 0, TEAL, 4, 11))
    defs = (f'<linearGradient id="north" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6d3de"/><stop offset="1" stop-color="{BLUSH}"/></linearGradient>'
            f'<linearGradient id="south" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe6ee"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>')
    body = f"""
<g fill="none" stroke="{TEAL}" stroke-width="3.5" stroke-linecap="round">{"".join(lines)}</g>
{arrow(128, cy, 44, cy, TEAL, 4)}{arrow(356, cy, 280, cy, TEAL, 4)}
<rect x="{cx - 68}" y="{cy - 22}" width="68" height="44" rx="9" fill="url(#north)" stroke="{INK}" stroke-width="4.5"/>
<rect x="{cx}" y="{cy - 22}" width="68" height="44" rx="9" fill="url(#south)" stroke="{INK}" stroke-width="4.5"/>
<path d="M{cx} {cy - 22}V{cy + 22}" stroke="{INK}" stroke-width="4.5"/>
{sparkle(340, 70, 9, GOLD, 0.8)}
"""
    return thumb(body, defs)


def thermodynamics():
    ox, oy = 62, 330

    def px(V, P):
        return ox + V * 150, oy - P * 100

    # gamma = 2 exaggerates the adiabats so the cycle reads at thumbnail size.
    g = 2.0
    hot, cold = 1.2, 0.7
    VA, VB = 0.5, 1.0
    kB = hot / VB * VB ** g
    VC = (kB / cold) ** (1 / (g - 1))
    kA = hot / VA * VA ** g
    VD = (kA / cold) ** (1 / (g - 1))

    def iso(c, v0, v1, k=40):
        return [px(v0 + (v1 - v0) * i / k, c / (v0 + (v1 - v0) * i / k)) for i in range(k + 1)]

    def adia(kk, v0, v1, k=40):
        return [px(v0 + (v1 - v0) * i / k, kk / (v0 + (v1 - v0) * i / k) ** g) for i in range(k + 1)]

    AB, BC, CD, DA = iso(hot, VA, VB), adia(kB, VB, VC), iso(cold, VC, VD), adia(kA, VD, VA)
    loop = AB + BC[1:] + CD[1:] + DA[1:]

    def mid_head(seg, color):
        i = len(seg) // 2
        (x0, y0), (x1, y1) = seg[i - 1], seg[i + 1]
        return head(seg[i][0], seg[i][1], math.degrees(math.atan2(y1 - y0, x1 - x0)), color, 4.5, 13)

    defs = (f'<linearGradient id="work" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BLUSH}" stop-opacity="0.32"/>'
            f'<stop offset="1" stop-color="{GOLD}" stop-opacity="0.2"/></linearGradient>')
    body = f"""
<path d="{poly_path(iso(hot, 0.42, 1.9))}" fill="none" stroke="{BLUSH}" stroke-width="2.5" stroke-opacity="0.45" stroke-dasharray="5 7"/>
<path d="{poly_path(iso(cold, 0.4, 1.95))}" fill="none" stroke="{TEAL}" stroke-width="2.5" stroke-opacity="0.45" stroke-dasharray="5 7"/>
{axes(ox, oy, 362, 50)}
<path d="{poly_path(loop)}Z" fill="url(#work)"/>
<path d="{poly_path(AB)}" fill="none" stroke="{BLUSH}" stroke-width="5.5" stroke-linecap="round"/>
<path d="{poly_path(CD)}" fill="none" stroke="{TEAL}" stroke-width="5.5" stroke-linecap="round"/>
<path d="{poly_path(BC)}M{poly_path(DA)[1:]}" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>
{mid_head(AB, BLUSH)}{mid_head(BC, INK)}{mid_head(CD, TEAL)}{mid_head(DA, INK)}
{"".join(dot(x, y, 7, CARD, INK, 3) for x, y in (AB[0], BC[0], CD[0], DA[0]))}
{sparkle(330, 84, 9, GOLD, 0.8)}
"""
    return thumb(body, defs)


def optics():
    T, Lv, Rv = (200, 88), (92, 290), (308, 290)

    def on(p, q, s):
        return p[0] + (q[0] - p[0]) * s, p[1] + (q[1] - p[1]) * s

    E = on(T, Lv, 0.48)
    rainbow = ["#e98a92", "#f0b07a", "#e8cf74", "#9cd09a", "#86bfd6", "#a597d6"]
    exits = [on(T, Rv, 0.5 + 0.04 * i) for i in range(6)]
    rays = "".join(
        f'<path d="M{n(x)} {n(y)}L392 {n(208 + i * 26)}" stroke="{c}" stroke-width="5.5" stroke-linecap="round"/>'
        for i, ((x, y), c) in enumerate(zip(exits, rainbow))
    )
    defs = (f'<linearGradient id="prism" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.85"/>'
            f'<stop offset="1" stop-color="#bcd8e2" stop-opacity="0.75"/></linearGradient>'
            f'<linearGradient id="inside" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff" stop-opacity="0.9"/>'
            f'<stop offset="1" stop-color="{BLUSH}" stop-opacity="0.45"/></linearGradient>')
    body = f"""
{rays}
<path d="M16 228L{n(E[0])} {n(E[1])}" stroke="{MUTED}" stroke-width="14" stroke-linecap="round"/>
<path d="M16 228L{n(E[0])} {n(E[1])}" stroke="#ffffff" stroke-width="9" stroke-linecap="round"/>
<path d="{poly_path([T, Lv, Rv])}Z" fill="url(#prism)" stroke="{INK}" stroke-width="5.5" stroke-linejoin="round"/>
<path d="{poly_path([E, exits[0], exits[-1]])}Z" fill="url(#inside)"/>
<path d="M{n(T[0] - 8)} {T[1] + 26}L{Lv[0] + 22} {Lv[1] - 14}" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.8"/>
{sparkle(66, 92, 9, GOLD, 0.8)}{sparkle(330, 74, 8, SKY, 0.9)}
"""
    return thumb(body, defs)


def quantum():
    xl, xr, bottom = 90, 310, 330
    parts = []
    for mode, color in ((1, TEAL), (2, BLUSH), (3, GOLD)):
        level = bottom - 22 * mode * mode
        wave = [(xl + (xr - xl) * t / 100, level - 26 * math.sin(mode * math.pi * t / 100)) for t in range(101)]
        parts.append(f'<path d="M{xl} {level}H{xr}" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="5 7"/>')
        parts.append(f'<path d="{poly_path(wave)}L{xr} {level}L{xl} {level}Z" fill="{color}" fill-opacity="0.16"/>')
        parts.append(f'<path d="{poly_path(wave)}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
    hatch = "".join(f'<path d="M{xl} {y}L{xl - 16} {y + 16}M{xr} {y}L{xr + 16} {y + 16}"/>' for y in range(64, 330, 18))
    body = f"""
<g stroke="{MUTED}" stroke-width="2.5">{hatch}</g>
<path d="M{xl} 58V{bottom}H{xr}V58" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
{"".join(parts)}
{sparkle(352, 336, 9, GOLD, 0.8)}{sparkle(46, 48, 8, SKY, 0.9)}
"""
    return thumb(body)


# ========================================================== computer science
def node_grad():
    return f'<linearGradient id="node" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{SKY}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>'


def data_structures():
    nodes = {0: (200, 82), 1: (118, 160), 2: (282, 160), 3: (74, 242), 4: (160, 242), 5: (240, 242),
             6: (326, 242), 7: (132, 320), 8: (190, 320)}
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6), (4, 7), (4, 8)]
    path = [(0, 1), (1, 4), (4, 8)]

    def seg(a, b):
        return f"M{nodes[a][0]} {nodes[a][1]}L{nodes[b][0]} {nodes[b][1]}"

    circles = []
    for i, (x, y) in nodes.items():
        if i == 8:
            circles.append(f'<circle cx="{x}" cy="{y}" r="30" fill="{GOLD}" fill-opacity="0.2"/>' + dot(x, y, 19, GOLD, "#ffffff", 4))
        elif i in (0, 1, 4):
            circles.append(dot(x, y, 19, "url(#node)", "#ffffff", 4))
        else:
            circles.append(dot(x, y, 17, CARD, MUTED, 4))
    body = f"""
<g stroke="#b9ced6" stroke-width="3.5" stroke-linecap="round">{"".join(f'<path d="{seg(a, b)}"/>' for a, b in edges if (a, b) not in path)}</g>
<g stroke="{SKY}" stroke-opacity="0.45" stroke-width="16" stroke-linecap="round">{"".join(f'<path d="{seg(a, b)}"/>' for a, b in path)}</g>
<g stroke="{TEAL}" stroke-width="6" stroke-linecap="round">{"".join(f'<path d="{seg(a, b)}"/>' for a, b in path)}</g>
{"".join(circles)}
{sparkle(344, 74, 9, GOLD, 0.8)}
"""
    return thumb(body, node_grad())


def computer_organization():
    alu = "M300 135L354 172V228L300 265V218L316 200L300 182Z"
    regs = "".join(f'<path d="M224 {y}H270"/>' for y in range(170, 246, 18))
    clock = "M40 82" + "".join(f"H{x}V{64 if i % 2 == 0 else 82}" for i, x in enumerate(range(70, 371, 30)))
    defs = grad_v("imem", "#e6f2f6", "#bcd8e2") + grad_v("reg", "#fbe8ee", "#efc3d0") + grad_v("alu", "#fbecc9", GOLD)
    body = f"""
<path d="{clock}" fill="none" stroke="{GOLD}" stroke-width="3.5" stroke-linejoin="round" stroke-opacity="0.8"/>
<path d="M354 200H376V312H64V232" fill="none" stroke="{BLUSH}" stroke-width="4" stroke-linejoin="round" stroke-dasharray="7 7"/>
{head(64, 232, -90, BLUSH, 4, 12)}
<rect x="40" y="170" width="48" height="60" rx="9" fill="{CARD}" stroke="{INK}" stroke-width="4.5"/>
<rect x="50" y="182" width="28" height="7" rx="3.5" fill="{BLUSH}" fill-opacity="0.7"/>
<rect x="116" y="128" width="74" height="144" rx="11" fill="url(#imem)" stroke="{INK}" stroke-width="4.5"/>
<g fill="#ffffff" fill-opacity="0.75">{"".join(f'<rect x="128" y="{y}" width="50" height="9" rx="4.5"/>' for y in range(146, 260, 20))}</g>
<rect x="214" y="148" width="66" height="104" rx="11" fill="url(#reg)" stroke="{INK}" stroke-width="4.5"/>
<g stroke="#ffffff" stroke-width="3" stroke-linecap="round">{regs}</g>
<path d="{alu}" fill="url(#alu)" stroke="{INK}" stroke-width="4.5" stroke-linejoin="round"/>
{arrow(88, 200, 112, 200, TEAL, 5, 11)}{arrow(190, 200, 210, 200, TEAL, 5, 11)}
{arrow(280, 176, 298, 176, TEAL, 5, 10)}{arrow(280, 224, 298, 224, TEAL, 5, 10)}
{arrow(354, 200, 380, 200, TEAL, 5, 11)}
"""
    return thumb(body, defs)


def operating_system():
    cx, cy = 200, 202
    colors = [TEAL, BLUSH, GOLD, SKY, SLATE, BLUSH]
    apps = []
    for i, a in enumerate(range(0, 360, 60)):
        t = math.radians(a)
        x, y = cx + 148 * math.cos(t), cy + 140 * math.sin(t)
        ix, iy = cx + 108 * math.cos(t), cy + 108 * math.sin(t)
        ox, oy = cx + 124 * math.cos(t), cy + 120 * math.sin(t)
        apps.append(arrow(ox, oy, ix, iy, MUTED, 3, 8))
        apps.append(f'<g transform="translate({n(x)} {n(y)})"><rect x="-27" y="-21" width="54" height="42" rx="8" fill="#ffffff" stroke="{INK}" stroke-width="3.5"/>'
                    f'<path d="M-27 -9H27" stroke="{INK}" stroke-width="2"/><rect x="-27" y="-21" width="54" height="12" rx="6" fill="{colors[i]}" fill-opacity="0.75"/>'
                    f'<path d="M-16 3H14M-16 12H4" stroke="{MUTED}" stroke-width="3" stroke-linecap="round"/></g>')
    pins = "".join(f'<path d="M{x} {cy - 36}V{cy - 46}M{x} {cy + 36}V{cy + 46}M{cx - 36} {x - cx + cy}H{cx - 46}M{cx + 36} {x - cx + cy}H{cx + 46}"/>' for x in range(cx - 20, cx + 21, 13))
    defs = (f'<linearGradient id="chipbody" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#43798a"/><stop offset="1" stop-color="#244c58"/></linearGradient>'
            f'<radialGradient id="kernel" cx="0.5" cy="0.5" r="0.5"><stop offset="0.6" stop-color="{TEAL}" stop-opacity="0.05"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0.25"/></radialGradient>')
    body = f"""
<circle cx="{cx}" cy="{cy}" r="100" fill="url(#kernel)" stroke="{TEAL}" stroke-width="4.5"/>
<circle cx="{cx}" cy="{cy}" r="70" fill="{CARD}" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="5 6"/>
<g stroke="{GOLD}" stroke-width="4" stroke-linecap="round">{pins}</g>
<rect x="{cx - 36}" y="{cy - 36}" width="72" height="72" rx="11" fill="url(#chipbody)" stroke="{INK}" stroke-width="3.5"/>
<rect x="{cx - 18}" y="{cy - 18}" width="36" height="36" rx="5" fill="{SKY}" fill-opacity="0.85"/>
{"".join(apps)}
"""
    return thumb(body, defs)


def computer_network():
    nodes = {"a": (130, 200), "b": (205, 118), "c": (205, 282), "d": (280, 200)}
    links = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d"), ("b", "c")]
    route = [("a", "b"), ("b", "d")]

    def seg(p, q):
        return f"M{nodes[p][0]} {nodes[p][1]}L{nodes[q][0]} {nodes[q][1]}"

    def packet(p, q, f):
        (x0, y0), (x1, y1) = nodes[p], nodes[q]
        x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        return (f'<g transform="translate({n(x)} {n(y)}) rotate({n(ang)})"><rect x="-17" y="-12" width="34" height="24" rx="4" fill="#fbecc9" stroke="{INK}" stroke-width="3"/>'
                f'<path d="M-17 -12L0 2L17 -12" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/></g>')

    def router(x, y, on_route):
        fill = "url(#node)" if on_route else CARD
        stroke = "#ffffff" if on_route else INK
        icon = "#ffffff" if on_route else TEAL
        return (dot(x, y, 24, fill, stroke, 4) +
                f'<g stroke="{icon}" stroke-width="3" stroke-linecap="round"><path d="M{x - 10} {y}H{x + 10}M{x} {y - 10}V{y + 10}"/></g>')

    laptop = (f'<rect x="22" y="178" width="58" height="38" rx="5" fill="#ffffff" stroke="{INK}" stroke-width="4"/>'
              f'<rect x="30" y="186" width="42" height="22" rx="2" fill="{SKY}" fill-opacity="0.6"/>'
              f'<path d="M14 222H88L82 230H20Z" fill="{CARD}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    server = "".join(
        f'<rect x="322" y="{y}" width="58" height="22" rx="5" fill="#ffffff" stroke="{INK}" stroke-width="4"/>'
        f'<circle cx="334" cy="{y + 11}" r="3.5" fill="{GOLD if i == 1 else TEAL}"/><path d="M346 {y + 11}H368" stroke="{MUTED}" stroke-width="3" stroke-linecap="round"/>'
        for i, y in enumerate((166, 192, 218))
    )
    body = f"""
<g stroke="#b9ced6" stroke-width="4" stroke-linecap="round">{"".join(f'<path d="{seg(p, q)}"/>' for p, q in links if (p, q) not in route)}
<path d="M80 200H106M304 200H322"/></g>
<g stroke="{SKY}" stroke-opacity="0.45" stroke-width="16" stroke-linecap="round">{"".join(f'<path d="{seg(p, q)}"/>' for p, q in route)}</g>
<g stroke="{TEAL}" stroke-width="6" stroke-linecap="round">{"".join(f'<path d="{seg(p, q)}"/>' for p, q in route)}<path d="M80 200H106M304 200H322"/></g>
{"".join(router(x, y, k in "abd") for k, (x, y) in nodes.items())}
{packet("a", "b", 0.5)}{packet("b", "d", 0.55)}
{laptop}{server}
{sparkle(70, 80, 9, GOLD, 0.8)}{sparkle(334, 322, 8, BLUSH, 0.8)}
"""
    return thumb(body, node_grad())


def artificial_intelligence():
    layers = [80, 163, 246, 329]
    counts = [3, 4, 4, 2]
    pos = [[(x, 200 + (i - (c - 1) / 2) * 64) for i in range(c)] for x, c in zip(layers, counts)]
    rnd = random.Random(4)
    thin, strong = [], []
    for li in range(3):
        for a in pos[li]:
            for b in pos[li + 1]:
                seg = f'<path d="M{n(a[0])} {n(a[1])}L{n(b[0])} {n(b[1])}"/>'
                r = rnd.random()
                if r < 0.22:
                    strong.append((seg, TEAL))
                elif r < 0.34:
                    strong.append((seg, BLUSH))
                else:
                    thin.append(seg)
    nodes = []
    for li, layer in enumerate(pos):
        for i, (x, y) in enumerate(layer):
            if li == 0:
                nodes.append(dot(x, y, 17, SKY, "#ffffff", 4))
            elif li == 3:
                nodes.append(dot(x, y, 19, GOLD if i == 0 else CARD, "#ffffff" if i == 0 else MUTED, 4))
            elif (li + i) % 2 == 0:
                nodes.append(dot(x, y, 17, "url(#node)", "#ffffff", 4))
            else:
                nodes.append(dot(x, y, 17, CARD, MUTED, 4))
    body = f"""
<g stroke="#c3d6dd" stroke-width="2">{"".join(thin)}</g>
{"".join(f'<g stroke="{c}" stroke-width="4" stroke-linecap="round" stroke-opacity="0.9">{s}</g>' for s, c in strong)}
<circle cx="{layers[3]}" cy="{n(pos[3][0][1])}" r="30" fill="{GOLD}" fill-opacity="0.18"/>
{"".join(nodes)}
{sparkle(330, 70, 9, BLUSH, 0.8)}
"""
    return thumb(body, node_grad())


def parallel_computing():
    lanes = [110, 170, 230, 290]
    tasks = [
        [(132, 80, TEAL), (220, 50, SKY)],
        [(132, 120, BLUSH), (260, 22, GOLD)],
        [(132, 52, GOLD), (192, 70, TEAL), (270, 12, BLUSH)],
        [(132, 140, SKY)],
    ]
    fork = "".join(f'<path d="M66 200C100 200 100 {y} 128 {y}"/>' for y in lanes)
    join = "".join(f'<path d="M290 {y}C318 {y} 318 200 334 200"/>' for y in lanes)
    blocks = "".join(
        f'<rect x="{x}" y="{y - 12}" width="{w}" height="24" rx="7" fill="{c}" fill-opacity="0.85" stroke="{INK}" stroke-width="2.5"/>'
        for y, row in zip(lanes, tasks) for x, w, c in row
    )
    body = f"""
<g fill="none" stroke="{MUTED}" stroke-width="4" stroke-linecap="round">{fork}{join}
{"".join(f'<path d="M128 {y}H290"/>' for y in lanes)}</g>
{blocks}
<path d="M290 78V322" stroke="{GOLD}" stroke-width="3.5" stroke-dasharray="6 7"/>
{dot(54, 200, 14, "url(#node)", "#ffffff", 4)}{dot(346, 200, 14, GOLD, "#ffffff", 4)}
{sparkle(74, 86, 9, SKY, 0.9)}{sparkle(340, 330, 8, BLUSH, 0.8)}
"""
    return thumb(body, node_grad())


# ================================================================ geoscience
def astronomy():
    rnd = random.Random(9)
    cx, cy = 200, 210
    stars = "".join(
        f'<circle cx="{rnd.randint(14, 386)}" cy="{rnd.randint(14, 386)}" r="{rnd.choice((1, 1.4, 1.9))}" fill="{INK}" fill-opacity="{rnd.choice((0.2, 0.3, 0.45))}"/>'
        for _ in range(40)
    )
    const = [(52, 92), (92, 70), (128, 96), (112, 136)]
    defs = (f'<linearGradient id="planet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbe9d6"/><stop offset="0.3" stop-color="#f3c9a8"/>'
            f'<stop offset="0.45" stop-color="#fbe2cf"/><stop offset="0.62" stop-color="#eeb39c"/><stop offset="0.8" stop-color="#f6d6c4"/>'
            f'<stop offset="1" stop-color="#e59f86"/></linearGradient>'
            f'<radialGradient id="shade" cx="0.35" cy="0.3" r="0.85"><stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{INK}" stop-opacity="0.35"/></radialGradient>')
    ring = f'transform="translate({cx} {cy}) rotate(-16)"'
    body = f"""
{stars}
<path d="{poly_path(const)}" fill="none" stroke="{SKY}" stroke-width="2.5"/>
{"".join(dot(x, y, 4.5, SKY, "#ffffff", 2) for x, y in const)}
<ellipse cx="0" cy="0" rx="172" ry="62" {ring} fill="none" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="3 8"/>
<ellipse cx="0" cy="0" rx="118" ry="30" {ring} fill="none" stroke="{GOLD}" stroke-opacity="0.55" stroke-width="13"/>
<ellipse cx="0" cy="0" rx="118" ry="30" {ring} fill="none" stroke="{INK}" stroke-width="2.5"/>
<circle cx="{cx}" cy="{cy}" r="62" fill="url(#planet)" stroke="{INK}" stroke-width="4.5"/>
<circle cx="{cx}" cy="{cy}" r="62" fill="url(#shade)"/>
<path d="M-118 0A118 30 0 0 0 118 0" {ring} fill="none" stroke="{GOLD}" stroke-opacity="0.75" stroke-width="13"/>
<path d="M-118 0A118 30 0 0 0 118 0" {ring} fill="none" stroke="{INK}" stroke-width="2.5"/>
{dot(cx + 165 * math.cos(math.radians(-16)) - 0, cy + 165 * math.sin(math.radians(-16)) + 0, 9, SKY, "#ffffff", 3)}
{sparkle(330, 330, 11, GOLD, 0.85)}{sparkle(340, 86, 8, BLUSH, 0.8)}
"""
    return thumb(body, defs)


def geology():
    top, bottom, left, right = 112, 322, 40, 360
    colors = ["#f4e2d7", "#e7c3b2", "#d8e9ef", "#bcd8e2", "#f2dfb0", "#e5b9a9", "#cfe3ea", "#efd0c0", "#d9e8ee"]

    def boundary(i, x, shift=0.0):
        return 118 + i * 34 - 50 * math.exp(-((x - 175) / 92) ** 2) + shift

    def bands(shift):
        out = []
        xs = list(range(left, right + 1, 4))
        for i in range(len(colors)):
            upper = [(x, boundary(i, x, shift)) for x in xs]
            lower = [(x, boundary(i + 1, x, shift)) for x in reversed(xs)]
            out.append(f'<path d="{poly_path(upper + lower)}Z" fill="{colors[i]}"/>')
            out.append(f'<path d="{poly_path(upper)}" fill="none" stroke="#ffffff" stroke-opacity="0.7" stroke-width="1.5"/>')
        return "".join(out)

    f_top, f_bot = (262, top), (306, bottom)
    defs = (f'<clipPath id="box"><rect x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" rx="10"/></clipPath>'
            f'<clipPath id="west"><path d="M{left} {top}H{f_top[0]}L{f_bot[0]} {bottom}H{left}Z"/></clipPath>'
            f'<clipPath id="east"><path d="M{f_top[0]} {top}H{right}V{bottom}H{f_bot[0]}Z"/></clipPath>')
    spiral = [(118 + 0.9 * t * math.cos(t), 262 + 0.9 * t * math.sin(t)) for t in [i * 0.2 for i in range(60)]]
    fx, fy = f_bot[0] - f_top[0], f_bot[1] - f_top[1]
    L = math.hypot(fx, fy)
    ux, uy = fx / L, fy / L
    body = f"""
<g clip-path="url(#box)">
<g clip-path="url(#west)">{bands(0)}</g>
<g clip-path="url(#east)">{bands(28)}</g>
</g>
<path d="{poly_path(spiral)}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linecap="round" opacity="0.7"/>
<path d="M{f_top[0]} {top}L{f_bot[0]} {bottom}" stroke="{INK}" stroke-width="4" stroke-dasharray="9 6"/>
{arrow(f_top[0] - 14 + ux * 70, top + uy * 70, f_top[0] - 14 + ux * 30, top + uy * 30, BLUSH, 4, 10)}
{arrow(f_top[0] + 18 + ux * 110, top + uy * 110, f_top[0] + 18 + ux * 150, top + uy * 150, BLUSH, 4, 10)}
<rect x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" rx="10" fill="none" stroke="{INK}" stroke-width="4.5"/>
{sparkle(186, 74, 9, GOLD, 0.8)}
"""
    return thumb(body, defs)


def geomagnetism():
    cx, cy, R = 200, 200, 70
    tilt = math.radians(11)

    def rot(x, y):
        return cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)

    lines = []
    for k, op in ((105, 0.95), (150, 0.85), (215, 0.7), (300, 0.5)):
        th0 = math.asin(math.sqrt(R / k))
        for side in (1, -1):
            pts_ = []
            for i in range(121):
                th = th0 + (math.pi - 2 * th0) * i / 120
                r = k * math.sin(th) ** 2
                pts_.append(rot(side * r * math.sin(th), -r * math.cos(th)))
            lines.append(f'<path d="{poly_path(pts_)}" stroke-opacity="{op}"/>')
            apex = rot(side * k, 0)
            lines.append(head(apex[0], apex[1], -90 + 11, TEAL, 4, 11))
    a1, a2 = rot(0, -112), rot(0, 112)
    defs = (f'<radialGradient id="earth" cx="0.38" cy="0.32" r="0.8"><stop offset="0" stop-color="#e3f1f5"/>'
            f'<stop offset="0.6" stop-color="{SKY}"/><stop offset="1" stop-color="{TEAL}"/></radialGradient>'
            f'<clipPath id="globe"><circle cx="{cx}" cy="{cy}" r="{R}"/></clipPath>')
    body = f"""
<g fill="none" stroke="{TEAL}" stroke-width="3.5" stroke-linecap="round">{"".join(lines)}</g>
<path d="M{cx} {cy - 100}V{cy + 100}" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="4 7"/>
<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#earth)" stroke="{INK}" stroke-width="4.5"/>
<g clip-path="url(#globe)" fill="#ffffff" fill-opacity="0.38">
<path d="M150 166C170 150 196 158 204 176S190 206 172 204 140 184 150 166Z"/>
<path d="M214 214C232 204 258 212 262 232S244 262 226 256 204 228 214 214Z"/>
</g>
<path d="M{n(a1[0])} {n(a1[1])}L{n(a2[0])} {n(a2[1])}" stroke="{GOLD}" stroke-width="4" stroke-dasharray="7 6" stroke-linecap="round"/>
{dot(*a1, 7, GOLD)}{dot(*a2, 7, GOLD)}
{sparkle(66, 74, 9, BLUSH, 0.8)}
"""
    return thumb(body, defs)


def seismology():
    p_at, s_at = 138, 214

    def trace(y, seed, amp_p, amp_s):
        r = random.Random(seed)
        out = []
        for x in range(60, 341, 2):
            v = r.uniform(-1.6, 1.6)
            if x >= p_at:
                v += amp_p * math.exp(-(x - p_at) / 26) * math.sin((x - p_at) * 0.55)
            if x >= s_at:
                v += amp_s * math.exp(-(x - s_at) / 42) * math.sin((x - s_at) * 0.38)
            out.append((x, y - v))
        return poly_path(out)

    body = f"""
<rect x="38" y="82" width="324" height="236" rx="16" fill="#ffffff" fill-opacity="0.72" stroke="#d3e3e9"/>
<g stroke="#e2edf1" stroke-width="1.5">{"".join(f'<path d="M{x} 92V308"/>' for x in range(80, 341, 40))}</g>
<path d="M{p_at} 96V304" stroke="{GOLD}" stroke-width="3.5" stroke-dasharray="6 6"/>
<path d="M{s_at} 96V304" stroke="{BLUSH}" stroke-width="3.5" stroke-dasharray="6 6"/>
<path d="M{p_at} 96l12 8l-12 8Z" fill="{GOLD}"/><path d="M{s_at} 96l12 8l-12 8Z" fill="{BLUSH}"/>
<g fill="none" stroke-width="3.2" stroke-linejoin="round">
<path d="{trace(150, 1, 16, 24)}" stroke="{INK}"/>
<path d="{trace(210, 2, 10, 30)}" stroke="{TEAL}"/>
<path d="{trace(268, 3, 9, 28)}" stroke="{SLATE}"/>
</g>
{sparkle(346, 344, 9, GOLD, 0.8)}{sparkle(54, 56, 8, SKY, 0.9)}
"""
    return thumb(body)


def gravity_tides():
    ex, ey, R = 160, 200, 62
    mx, my = 336, 200
    defs = (f'<radialGradient id="earth" cx="0.38" cy="0.32" r="0.8"><stop offset="0" stop-color="#e3f1f5"/>'
            f'<stop offset="0.6" stop-color="{SKY}"/><stop offset="1" stop-color="{TEAL}"/></radialGradient>'
            f'<radialGradient id="moon" cx="0.38" cy="0.32" r="0.8"><stop offset="0" stop-color="#ffffff"/>'
            f'<stop offset="1" stop-color="#c5d3d8"/></radialGradient>'
            f'<clipPath id="globe"><circle cx="{ex}" cy="{ey}" r="{R}"/></clipPath>')
    body = f"""
<ellipse cx="{ex}" cy="{ey}" rx="104" ry="76" fill="{SKY}" fill-opacity="0.3" stroke="{TEAL}" stroke-width="3.5" stroke-dasharray="7 6"/>
<path d="M{ex} {ey}H{mx}" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="4 7"/>
<circle cx="{ex}" cy="{ey}" r="{R}" fill="url(#earth)" stroke="{INK}" stroke-width="4.5"/>
<g clip-path="url(#globe)" fill="#ffffff" fill-opacity="0.38">
<path d="M118 172C136 158 160 166 166 184S150 212 134 208 108 188 118 172Z"/>
<path d="M170 216C188 206 210 214 214 232S196 258 180 252 162 228 170 216Z"/>
</g>
{arrow(ex + R + 6, ey, ex + R + 46, ey, BLUSH, 5)}
{arrow(ex - R - 6, ey, ex - R - 46, ey, BLUSH, 5)}
{arrow(ex, ey - R - 36, ex, ey - R - 8, BLUSH, 4.5, 11)}
{arrow(ex, ey + R + 36, ex, ey + R + 8, BLUSH, 4.5, 11)}
<circle cx="{mx}" cy="{my}" r="26" fill="url(#moon)" stroke="{INK}" stroke-width="4"/>
<circle cx="{mx - 8}" cy="{my - 6}" r="5" fill="#b9c8ce"/><circle cx="{mx + 9}" cy="{my + 8}" r="3.5" fill="#b9c8ce"/>
{arrow(mx - 32, my - 40, ex + 70, ey - 52, GOLD, 4, 11)}
{sparkle(330, 90, 9, GOLD, 0.8)}{sparkle(60, 330, 8, SKY, 0.9)}
"""
    return thumb(body, defs)


# ==================================================== electronic engineering
def signals():
    def s(x):
        w = (x - 56) / 288 * 4 * math.pi
        return 26 * math.sin(w) + 13 * math.sin(3 * w) + 7 * math.sin(5 * w)

    wave = [(x, 140 - s(x)) for x in range(56, 345, 2)]
    stems = "".join(
        f'<path d="M{x} 316V{316 - h}" stroke="{c}" stroke-width="6" stroke-linecap="round"/>{dot(x, 316 - h, 9, c)}'
        for x, h, c in ((120, 74, TEAL), (200, 38, BLUSH), (280, 21, GOLD))
    )
    body = f"""
<rect x="38" y="78" width="324" height="124" rx="16" fill="#ffffff" fill-opacity="0.72" stroke="#d3e3e9"/>
<path d="M52 140H348" stroke="#d3e3e9" stroke-width="2"/>
<path d="{poly_path(wave)}" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
{arrow(200, 210, 200, 240, GOLD, 5, 11)}
<path d="M60 316H340" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
{stems}
{sparkle(346, 52, 8, SKY, 0.9)}
"""
    return thumb(body)


def zigzag(x0, x1, y, teeth=6, amp=11):
    step = (x1 - x0) / (teeth * 2)
    pts_ = [(x0, y)] + [(x0 + step * (2 * i + 1), y + (amp if i % 2 else -amp)) for i in range(teeth * 2 - 1)] + [(x1, y)]
    return poly_path(pts_)


def analog_circuits():
    tri = [(165, 125), (165, 275), (295, 200)]
    sine_in = [(40 + t, 118 - 9 * math.sin(t / 60 * 2 * math.pi)) for t in range(0, 61, 2)]
    sine_out = [(304 + t, 262 + 16 * math.sin(t / 66 * 2 * math.pi)) for t in range(0, 67, 2)]
    defs = grad_v("amp", "#eef6f9", "#c3dce5")
    body = f"""
<g fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
<path d="M34 160H64"/><path d="{zigzag(64, 124, 160)}"/><path d="M124 160H165"/>
<path d="M165 240H134V292"/><path d="M116 292H152M123 302H145M131 312H137"/>
<path d="M145 160V88H196"/><path d="{zigzag(196, 266, 88)}"/><path d="M266 88H322V200"/>
<path d="M295 200H366"/>
</g>
<path d="{poly_path(tri)}Z" fill="url(#amp)" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
<path d="M176 160H192M176 240H192M184 232V248" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>
{dot(145, 160, 6.5, INK, "#ffffff", 2)}{dot(322, 200, 6.5, INK, "#ffffff", 2)}{dot(34, 160, 7, CARD, INK, 3)}{dot(366, 200, 7, CARD, INK, 3)}
<path d="{poly_path(sine_in)}" fill="none" stroke="{BLUSH}" stroke-width="4" stroke-linecap="round"/>
<path d="{poly_path(sine_out)}" fill="none" stroke="{TEAL}" stroke-width="4.5" stroke-linecap="round"/>
{sparkle(330, 330, 9, GOLD, 0.8)}
"""
    return thumb(body, defs)


def digital_circuits():
    def and_gate(x, y):
        return f"M{x} {y}H{x + 36}A35 35 0 0 1 {x + 36} {y + 70}H{x}Z"

    def or_gate(x, y):
        return f"M{x} {y}Q{x + 26} {y + 35} {x} {y + 70}Q{x + 52} {y + 70} {x + 86} {y + 35}Q{x + 52} {y} {x} {y}Z"

    clock = "M40 344" + "".join(f"H{x}V{326 if i % 2 == 0 else 344}" for i, x in enumerate(range(72, 361, 32)))
    defs = grad_v("gate", "#ffffff", "#cfe3ea")
    body = f"""
<g fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
<path d="M44 122H92M44 158H92M44 242H104M44 278H104"/>
<path d="M163 140H206V182H236M180 260H214V218H236"/>
<path d="M307 200H332"/>
</g>
<path d="{and_gate(92, 105)}" fill="url(#gate)" stroke="{INK}" stroke-width="4.5"/>
<path d="{or_gate(94, 225)}" fill="url(#gate)" stroke="{INK}" stroke-width="4.5"/>
<path d="{and_gate(236, 165)}" fill="url(#gate)" stroke="{INK}" stroke-width="4.5"/>
{dot(44, 122, 7.5, GOLD, "#ffffff", 2.5)}{dot(44, 158, 7.5, GOLD, "#ffffff", 2.5)}{dot(44, 242, 7.5, CARD, INK, 3)}{dot(44, 278, 7.5, GOLD, "#ffffff", 2.5)}
<circle cx="348" cy="200" r="26" fill="{GOLD}" fill-opacity="0.22"/>{dot(348, 200, 14, GOLD, "#ffffff", 4)}
<path d="{clock}" fill="none" stroke="{TEAL}" stroke-width="3.5" stroke-linejoin="round" stroke-opacity="0.85"/>
{sparkle(340, 76, 9, BLUSH, 0.8)}
"""
    return thumb(body, defs)


THUMBS = {
    "math/mathematical-analysis.svg": analysis,
    "math/complex-analysis.svg": complex_analysis,
    "math/equations-of-mathematical-physics.svg": math_physics,
    "math/algebra.svg": algebra,
    "math/number-theory.svg": number_theory,
    "math/functional-analysis.svg": functional_analysis,
    "math/geometry.svg": geometry,
    "math/probability-and-statistics.svg": probability,
    "math/topology.svg": topology,
    "math/numerical-analysis.svg": numerical_analysis,
    "physics/mechanics.svg": mechanics,
    "physics/electromagnetism.svg": electromagnetism,
    "physics/thermodynamics.svg": thermodynamics,
    "physics/optics.svg": optics,
    "physics/quantum-physics.svg": quantum,
    "cs/data-structures.svg": data_structures,
    "cs/computer-organization.svg": computer_organization,
    "cs/operating-system.svg": operating_system,
    "cs/computer-network.svg": computer_network,
    "cs/artificial-intelligence.svg": artificial_intelligence,
    "cs/parallel-computing.svg": parallel_computing,
    "geoscience/astronomy.svg": astronomy,
    "geoscience/geology.svg": geology,
    "geoscience/geomagnetism.svg": geomagnetism,
    "geoscience/seismology.svg": seismology,
    "geoscience/gravity-and-tides.svg": gravity_tides,
    "electronic_engineering/signals-and-systems.svg": signals,
    "electronic_engineering/analog-circuits.svg": analog_circuits,
    "electronic_engineering/digital-circuits.svg": digital_circuits,
}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else THUMBS_DIR
    for name, make in THUMBS.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(make())
    print(f"{len(THUMBS)} thumbnails written to {out}")


if __name__ == "__main__":
    main()
