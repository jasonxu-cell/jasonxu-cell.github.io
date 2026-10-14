#!/usr/bin/env python3
"""Generate the cover illustrations in assets/covers/ (640x400 SVG).

Usage:
    python3 scripts/generate_covers.py            # rewrite every cover
    python3 scripts/generate_covers.py <out-dir>  # write somewhere else to preview

Each cover is drawn from code so the set stays consistent: one shared
background (soft gradient, two glows, dot grid), one palette, and geometry
computed rather than eyeballed (e.g. the Dandelin spheres in exam.svg).
"""
import math
import random
import sys
from pathlib import Path

COVERS_DIR = Path(__file__).resolve().parent.parent / "assets" / "covers"

INK = "#2c5a69"
TEAL = "#3f8597"
SKY = "#8cc2d3"
PALE = "#d4e8ef"
BLUSH = "#df93aa"
GOLD = "#e0ac58"
MUTED = "#a9c1ca"
CARD = "#f7fafc"


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(points):
    return " ".join(f"{n(x)},{n(y)}" for x, y in points)


def poly_path(points):
    head, *rest = points
    return f"M{n(head[0])} {n(head[1])}" + "".join(f"L{n(x)} {n(y)}" for x, y in rest)


def svg(body, defs="", glow=(0.82, 0.12), glow_color="#f6d6e0", glow2=(0.08, 0.95), glow2_color="#cfe6ee"):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f8fbfc"/><stop offset="1" stop-color="#e3eef3"/></linearGradient>
<radialGradient id="glow" cx="{glow[0]}" cy="{glow[1]}" r="0.6"><stop offset="0" stop-color="{glow_color}" stop-opacity="0.9"/><stop offset="1" stop-color="{glow_color}" stop-opacity="0"/></radialGradient>
<radialGradient id="glow2" cx="{glow2[0]}" cy="{glow2[1]}" r="0.55"><stop offset="0" stop-color="{glow2_color}" stop-opacity="0.9"/><stop offset="1" stop-color="{glow2_color}" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="0.9" fill="#8fb0bc" fill-opacity="0.32"/></pattern>
{defs}
</defs>
<rect width="640" height="400" fill="url(#bg)"/>
<rect width="640" height="400" fill="url(#glow)"/>
<rect width="640" height="400" fill="url(#glow2)"/>
<rect width="640" height="400" fill="url(#dots)"/>
{body}
</svg>
"""


def sparkle(x, y, s, color, opacity=1.0):
    d = (f"M{n(x)} {n(y - s)}Q{n(x)} {n(y)} {n(x + s)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y + s)}"
         f"Q{n(x)} {n(y)} {n(x - s)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y - s)}Z")
    return f'<path d="{d}" fill="{color}" fill-opacity="{opacity}"/>'


# ---------------------------------------------------------------- geoscience
def geoscience():
    cx, cy, R = 320, 205, 150
    core, inner = 82, 36

    def surf(theta, r=R):
        t = math.radians(theta)
        return cx + r * math.sin(t), cy - r * math.cos(t)

    E = surf(0, R - 8)
    defs = f"""
<radialGradient id="mantle" cx="0.5" cy="0.5" r="0.5"><stop offset="0.5" stop-color="#f0c4af"/><stop offset="1" stop-color="#f9eae1"/></radialGradient>
<radialGradient id="outer" cx="0.5" cy="0.5" r="0.5"><stop offset="0.4" stop-color="#e88d72"/><stop offset="1" stop-color="#efae96"/></radialGradient>
<radialGradient id="inner" cx="0.38" cy="0.32" r="0.75"><stop offset="0" stop-color="#fcebbf"/><stop offset="1" stop-color="#e3a64f"/></radialGradient>
<clipPath id="earth"><circle cx="{cx}" cy="{cy}" r="{R - 4}"/></clipPath>"""

    rays, stations = [], []
    for theta, rmin in ((20, 141), (40, 128), (70, 112), (100, 88)):
        for side in (1, -1):
            th = theta * side
            P = surf(th)
            rc = 2 * rmin - R * math.cos(math.radians(theta / 2))
            Q = surf(th / 2, rc)
            if side == 1:
                rays.append(f'<path d="M{n(E[0])} {n(E[1])}Q{n(Q[0])} {n(Q[1])} {n(P[0])} {n(P[1])}" stroke="{TEAL}" stroke-width="2.2"/>')
            else:
                rays.append(f'<path d="M{n(E[0])} {n(E[1])}Q{n(Q[0])} {n(Q[1])} {n(P[0])} {n(P[1])}" stroke="{BLUSH}" stroke-width="2" stroke-dasharray="6 6"/>')
            if theta >= 40:
                stations.append((P, th))
    # Core phases (PKP) refracted through the outer core.
    for theta, c1, c2 in ((155, (338, 165), (375, 262)), (172, (327, 172), (346, 280))):
        P = surf(theta)
        rays.append(f'<path d="M{n(E[0])} {n(E[1])}C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {n(P[0])} {n(P[1])}" stroke="{GOLD}" stroke-width="2.2"/>')
        stations.append((P, theta))

    tri = "".join(
        f'<path d="M0 -10L7 2H-7Z" transform="translate({n(P[0])} {n(P[1])}) rotate({n(th)})" fill="{INK}"/>'
        for P, th in stations
    )

    def arc(t0, t1, r):
        a, b = surf(t0, r), surf(t1, r)
        large = 1 if abs(t1 - t0) > 180 else 0
        sweep = 1 if t1 > t0 else 0
        return f"M{n(a[0])} {n(a[1])}A{r} {r} 0 {large} {sweep} {n(b[0])} {n(b[1])}"

    shadow = (f'<path d="{arc(104, 142, R + 12)}" stroke="#b8cdd5" stroke-width="7" stroke-linecap="round" fill="none" opacity="0.7"/>'
              f'<path d="{arc(-104, -142, R + 12)}" stroke="#b8cdd5" stroke-width="7" stroke-linecap="round" fill="none" opacity="0.7"/>')

    def trace(x0, x1, y, onset, amp, color, flip=False):
        out = []
        for i in range(181):
            f = i / 180
            x = x0 + (x1 - x0) * f
            t = f - onset
            a = 0 if t < 0 else amp * math.exp(-t * 7) * min(1, t * 30)
            noise = 0.9 * math.sin(i * 1.7) * math.sin(i * 0.31)
            out.append((x, y - a * math.sin(t * 95) + noise))
        if flip:
            out = [(x0 + x1 - x, yy) for x, yy in out]
        return f'<path d="{poly_path(out)}" stroke="{color}" stroke-width="1.8"/>'

    traces = "".join([
        f'<path d="M482 116H612M482 194H612M482 260H612" stroke="#cbdbe1" stroke-width="1"/>',
        trace(482, 612, 116, 0.12, 9, INK),
        trace(482, 612, 194, 0.3, 11, INK),
        trace(482, 612, 260, 0.48, 13, INK),
        f'<path d="M28 116H158M28 194H158M28 260H158" stroke="#cbdbe1" stroke-width="1"/>',
        trace(28, 158, 116, 0.18, 8, BLUSH, flip=True),
        trace(28, 158, 194, 0.38, 10, BLUSH, flip=True),
        trace(28, 158, 260, 0.56, 12, BLUSH, flip=True),
    ])

    body = f"""
<g fill="none" stroke-linecap="round" stroke-linejoin="round">{traces}</g>
<circle cx="{cx}" cy="{cy}" r="{R + 22}" fill="#ffffff" fill-opacity="0.45"/>
{shadow}
<circle cx="{cx}" cy="{cy}" r="{R}" fill="#cfe3ea" stroke="{INK}" stroke-width="3"/>
<circle cx="{cx}" cy="{cy}" r="{R - 6}" fill="url(#mantle)"/>
<circle cx="{cx}" cy="{cy}" r="110" fill="none" stroke="#ffffff" stroke-opacity="0.6" stroke-width="1.5" stroke-dasharray="3 7"/>
<circle cx="{cx}" cy="{cy}" r="{core}" fill="url(#outer)" stroke="#d27c62" stroke-opacity="0.5" stroke-width="1.5"/>
<circle cx="{cx}" cy="{cy}" r="{inner}" fill="url(#inner)" stroke="#ffffff" stroke-opacity="0.7" stroke-width="1.5"/>
<g clip-path="url(#earth)" fill="none" stroke-linecap="round" opacity="0.95">{"".join(rays)}</g>
{tri}
<g fill="none" stroke="{GOLD}" stroke-width="2" stroke-linecap="round">
<path d="M{n(cx - 18)} {n(cy - R - 8)}A20 20 0 0 1 {n(cx + 18)} {n(cy - R - 8)}" opacity="0.9"/>
<path d="M{n(cx - 30)} {n(cy - R - 14)}A34 34 0 0 1 {n(cx + 30)} {n(cy - R - 14)}" opacity="0.5"/>
</g>
<circle cx="{n(E[0])}" cy="{n(E[1])}" r="6.5" fill="{GOLD}" stroke="#ffffff" stroke-width="2.5"/>
{sparkle(560, 52, 9, GOLD, 0.8)}{sparkle(84, 330, 7, SKY, 0.9)}
"""
    return svg(body, defs)


# ------------------------------------------------------------------- physics
def physics():
    y0, x0, x1 = 222, 130, 530
    k = 2 * math.pi / 200
    E_amp, B_amp = 82, 78

    def E(x):
        return E_amp * math.sin(k * (x - x0))

    def Bpt(x):
        z = B_amp * math.sin(k * (x - x0))
        return x - 0.55 * z, y0 + 0.5 * z

    xs = [x0 + i * 2 for i in range(int((x1 - x0) / 2) + 1)]
    e_curve = [(x, y0 - E(x)) for x in xs]
    b_curve = [Bpt(x) for x in xs]
    e_lines = "".join(f'<path d="M{n(x)} {y0}V{n(y0 - E(x))}"/>' for x in xs[::7] if abs(E(x)) > 4)
    b_lines = "".join(
        f'<path d="M{n(x)} {y0}L{n(Bpt(x)[0])} {n(Bpt(x)[1])}"/>' for x in xs[::7]
        if abs(math.sin(k * (x - x0))) > 0.06
    )
    rings = "".join(
        f'<circle cx="548" cy="92" r="{r}" stroke="{SKY}" stroke-opacity="{n(0.75 - i * 0.12)}"/>'
        for i, r in enumerate((16, 34, 52, 70, 88, 106))
    )
    # A slow carrier wave along the bottom for depth.
    carrier = [(x, 352 + 10 * math.sin(x / 38)) for x in range(0, 641, 4)]
    defs = f"""
<linearGradient id="efill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.32"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0.08"/></linearGradient>
<linearGradient id="bfill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUSH}" stop-opacity="0.32"/><stop offset="1" stop-color="{BLUSH}" stop-opacity="0.12"/></linearGradient>"""
    body = f"""
<g fill="none" stroke-width="2">{rings}</g>
<path d="{poly_path(carrier)}" fill="none" stroke="{SKY}" stroke-opacity="0.45" stroke-width="2"/>
<path d="{poly_path(carrier)}" transform="translate(0 16)" fill="none" stroke="{SKY}" stroke-opacity="0.25" stroke-width="2"/>
<path d="M{x0} {y0}{poly_path(b_curve)[0:0]}{''.join(f'L{n(x)} {n(y)}' for x, y in b_curve)}L{x1} {y0}Z" fill="url(#bfill)"/>
<g stroke="{BLUSH}" stroke-opacity="0.55" stroke-width="1.3">{b_lines}</g>
<path d="{poly_path(b_curve)}" fill="none" stroke="{BLUSH}" stroke-width="3" stroke-linecap="round"/>
<path d="M98 {y0}H566" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>
<path d="M556 {y0 - 8}L570 {y0}L556 {y0 + 8}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M{x0} {y0}{''.join(f'L{n(x)} {n(y)}' for x, y in e_curve)}L{x1} {y0}Z" fill="url(#efill)"/>
<g stroke="{TEAL}" stroke-opacity="0.55" stroke-width="1.3">{e_lines}</g>
<path d="{poly_path(e_curve)}" fill="none" stroke="{TEAL}" stroke-width="3.2" stroke-linecap="round"/>
<g fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.8">
<path d="M{x0} {y0}V{y0 - 118}M{x0 - 6} {y0 - 108}L{x0} {y0 - 118}L{x0 + 6} {y0 - 108}"/>
<path d="M{x0} {y0}L{x0 - 52} {y0 + 44}M{x0 - 50} {y0 + 32}L{x0 - 52} {y0 + 44}L{x0 - 40} {y0 + 44}"/>
</g>
<circle cx="{x0}" cy="{y0}" r="6" fill="{GOLD}" stroke="#ffffff" stroke-width="2.5"/>
{sparkle(86, 70, 8, GOLD, 0.8)}{sparkle(600, 300, 6, BLUSH, 0.8)}
"""
    return svg(body, defs, glow=(0.85, 0.2), glow2=(0.1, 0.1), glow2_color="#d5eaf1")


# ---------------------------------------------------------------------- math
def mathematics():
    O = (150, 318)

    def f(u):
        return 72 + 0.36 * u + 46 * math.sin(u / 40 + 0.5)

    def fp(u):
        return 0.36 + 46 / 40 * math.cos(u / 40 + 0.5)

    def P(u):
        return O[0] + u, O[1] - f(u)

    curve = [P(u) for u in range(0, 341, 3)]
    bars = "".join(
        f'<rect x="{n(O[0] + u)}" y="{n(O[1] - f(u + 10))}" width="20" height="{n(f(u + 10))}"/>'
        for u in range(40, 240, 20)
    )
    ut = 286
    T = P(ut)
    s = fp(ut)
    dx = 62
    tangent = f"M{n(T[0] - dx)} {n(T[1] + s * dx)}L{n(T[0] + dx)} {n(T[1] - s * dx)}"
    # Faint golden spiral behind the plot.
    b = math.log((1 + 5 ** 0.5) / 2) / (math.pi / 2)
    spiral = []
    for i in range(0, 900):
        th = i * 0.016
        r = 3 * math.exp(b * th)
        if r > 320:
            break
        spiral.append((470 + r * math.cos(-th), 150 + r * math.sin(-th)))
    grid = "".join(f'<path d="M{x} 64V334"/>' for x in range(140, 521, 20)) + \
           "".join(f'<path d="M126 {y}H510"/>' for y in range(78, 334, 20))
    under = [P(u) for u in range(40, 241, 2)]
    defs = f"""
<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.42"/><stop offset="1" stop-color="{SKY}" stop-opacity="0.12"/></linearGradient>
<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BLUSH}" stop-opacity="0.22"/><stop offset="1" stop-color="{BLUSH}" stop-opacity="0"/></linearGradient>"""
    body = f"""
<rect x="114" y="50" width="410" height="300" rx="16" fill="#ffffff" fill-opacity="0.72" stroke="#d3e3e9"/>
<g stroke="#e2edf1" stroke-width="1">{grid}</g>
<path d="M{O[0] + 40} {O[1]}{''.join(f'L{n(x)} {n(y)}' for x, y in under)}L{O[0] + 240} {O[1]}Z" fill="url(#area)"/>
<g fill="url(#bar)" stroke="{TEAL}" stroke-opacity="0.55" stroke-width="1.2">{bars}</g>
<g fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
<path d="M{O[0] - 14} {O[1]}H500M492 {O[1] - 6}L500 {O[1]}L492 {O[1] + 6}"/>
<path d="M{O[0]} {O[1] + 14}V70M{O[0] - 6} 78L{O[0]} 70L{O[0] + 6} 78"/>
</g>
<path d="M{n(T[0])} {n(T[1])}V{O[1]}M{n(T[0])} {n(T[1])}H{O[0]}" stroke="{MUTED}" stroke-width="1.6" stroke-dasharray="4 6" fill="none"/>
<path d="{poly_path(curve)}" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>
<path d="{tangent}" stroke="{BLUSH}" stroke-width="2.8" stroke-linecap="round"/>
<circle cx="{n(T[0])}" cy="{n(T[1])}" r="7" fill="{GOLD}" stroke="#ffffff" stroke-width="2.5"/>
<circle cx="{n(P(40)[0])}" cy="{n(P(40)[1])}" r="4.5" fill="#ffffff" stroke="{TEAL}" stroke-width="2"/>
<circle cx="{n(P(240)[0])}" cy="{n(P(240)[1])}" r="4.5" fill="#ffffff" stroke="{TEAL}" stroke-width="2"/>
{sparkle(570, 330, 8, GOLD, 0.75)}{sparkle(76, 92, 7, SKY, 0.9)}
"""
    return svg(body, defs, glow=(0.9, 0.85), glow2=(0.05, 0.1))


# ------------------------------------------------------------------------ cs
def cs():
    rnd = random.Random(7)
    code = []
    for i, y in enumerate(range(104, 336, 19)):
        indent = rnd.choice((0, 0, 14, 28, 14))
        length = rnd.randint(36, 104)
        color = rnd.choice(("#cfe0e6", "#cfe0e6", "#cfe0e6", "#f1d3dc", "#d6e9ef"))
        code.append(f'<rect x="{118 + indent}" y="{y}" width="{length}" height="7" rx="3.5" fill="{color}"/>')
        if rnd.random() < 0.45:
            code.append(f'<rect x="{118 + indent + length + 8}" y="{y}" width="{rnd.randint(14, 40)}" height="7" rx="3.5" fill="#e3edf1"/>')
    nodes = {
        0: (268, 252), 1: (322, 150), 2: (356, 302), 3: (394, 212), 4: (436, 118),
        5: (458, 292), 6: (500, 204), 7: (300, 330), 8: (518, 120), 9: (246, 168),
    }
    edges = [(0, 9), (0, 1), (0, 2), (9, 1), (1, 3), (1, 4), (2, 3), (2, 5), (2, 7), (0, 7),
             (3, 6), (3, 5), (4, 6), (4, 8), (8, 6), (5, 6), (3, 4)]
    path = [(0, 1), (1, 3), (3, 6)]
    on_path = {0, 1, 3, 6}

    def line(a, b):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        return f"M{x1} {y1}L{x2} {y2}"

    plain = "".join(f'<path d="{line(a, b)}"/>' for a, b in edges if (a, b) not in path)
    hot = "".join(f'<path d="{line(a, b)}"/>' for a, b in path)
    circles = []
    for i, (x, y) in nodes.items():
        if i == 0:
            circles.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{GOLD}" stroke="#ffffff" stroke-width="3"/>')
        elif i == 6:
            circles.append(f'<circle cx="{x}" cy="{y}" r="22" fill="none" stroke="{BLUSH}" stroke-opacity="0.45" stroke-width="2"/>')
            circles.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{BLUSH}" stroke="#ffffff" stroke-width="3"/>')
        elif i in on_path:
            circles.append(f'<circle cx="{x}" cy="{y}" r="11" fill="url(#node)" stroke="#ffffff" stroke-width="3"/>')
        else:
            circles.append(f'<circle cx="{x}" cy="{y}" r="8.5" fill="{CARD}" stroke="{MUTED}" stroke-width="2.5"/>')
    defs = f"""
<linearGradient id="node" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{SKY}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>"""
    body = f"""
<rect x="96" y="48" width="448" height="304" rx="18" fill="#ffffff" fill-opacity="0.66" stroke="#d3e2e8"/>
<path d="M96 82H544" stroke="#dce8ec"/>
<circle cx="120" cy="65" r="5" fill="{BLUSH}" fill-opacity="0.8"/><circle cx="137" cy="65" r="5" fill="{GOLD}" fill-opacity="0.8"/><circle cx="154" cy="65" r="5" fill="{SKY}"/>
<rect x="400" y="60" width="120" height="10" rx="5" fill="#e3edf1"/>
{"".join(code)}
<g stroke="#b9ced6" stroke-width="2" stroke-linecap="round">{plain}</g>
<g stroke="{SKY}" stroke-opacity="0.45" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">{hot}</g>
<g stroke="{TEAL}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{hot}</g>
{"".join(circles)}
{sparkle(590, 70, 8, GOLD, 0.8)}{sparkle(56, 320, 7, BLUSH, 0.75)}
"""
    return svg(body, defs, glow=(0.95, 0.9), glow2=(0.0, 0.0))


# --------------------------------------------------------------- electronics
def electronics():
    cx, cy, half = 320, 200, 70
    pins = [cx - 50 + i * 20 for i in range(6)]
    colors = [TEAL, SKY, TEAL, BLUSH, SKY, TEAL]
    traces, vias, pinrects = [], [], []
    for i, p in enumerate(pins):
        c = colors[i]
        off = p - cx
        # top
        y1 = cy - half - 14
        dx = off * 0.95
        ye = 40 + (i % 2) * 12
        traces.append((f"M{p} {y1}V{y1 - 12}L{n(p + dx)} {n(y1 - 12 - abs(dx))}V{ye}", c))
        vias.append((p + dx, ye, c))
        # bottom
        y1 = cy + half + 14
        ye = 360 - (i % 2) * 12
        traces.append((f"M{p} {y1}V{y1 + 12}L{n(p + dx)} {n(y1 + 12 + abs(dx))}V{ye}", colors[-1 - i]))
        vias.append((p + dx, ye, colors[-1 - i]))
        # left
        q = cy + off
        x1 = cx - half - 14
        dy = off * 0.9
        xe = 92 + (i % 2) * 18
        traces.append((f"M{x1} {q}H{x1 - 14}L{n(x1 - 14 - abs(dy))} {n(q + dy)}H{xe}", colors[(i + 2) % 6]))
        vias.append((xe, q + dy, colors[(i + 2) % 6]))
        # right
        x1 = cx + half + 14
        xe = 548 - (i % 2) * 18
        traces.append((f"M{x1} {q}H{x1 + 14}L{n(x1 + 14 + abs(dy))} {n(q + dy)}H{xe}", colors[(i + 4) % 6]))
        vias.append((xe, q + dy, colors[(i + 4) % 6]))
        pinrects.append(f'<rect x="{p - 3.5}" y="{cy - half - 14}" width="7" height="14" rx="1.5"/>')
        pinrects.append(f'<rect x="{p - 3.5}" y="{cy + half}" width="7" height="14" rx="1.5"/>')
        pinrects.append(f'<rect x="{cx - half - 14}" y="{q - 3.5}" width="14" height="7" rx="1.5"/>')
        pinrects.append(f'<rect x="{cx + half}" y="{q - 3.5}" width="14" height="7" rx="1.5"/>')
    trace_svg = "".join(f'<path d="{d}" stroke="{c}"/>' for d, c in traces)
    via_svg = "".join(
        f'<circle cx="{n(x)}" cy="{n(y)}" r="5.5" fill="{CARD if k % 3 else c}" stroke="{c}" stroke-width="2.5"/>'
        for k, (x, y, c) in enumerate(vias)
    )
    die_grid = "".join(f'<path d="M{x} {cy - 36}V{cy + 36}"/>' for x in range(cx - 27, cx + 36, 9)) + \
               "".join(f'<path d="M{cx - 36} {y}H{cx + 36}"/>' for y in range(cy - 27, cy + 36, 9))

    def smd(x, y, rot, body_color):
        return (f'<g transform="translate({x} {y}) rotate({rot})">'
                f'<rect x="-16" y="-8" width="32" height="16" rx="3" fill="{body_color}" stroke="{INK}" stroke-width="1.5"/>'
                f'<rect x="-16" y="-8" width="7" height="16" rx="2" fill="#d7dfe2" stroke="{INK}" stroke-width="1.5"/>'
                f'<rect x="9" y="-8" width="7" height="16" rx="2" fill="#d7dfe2" stroke="{INK}" stroke-width="1.5"/></g>')

    defs = f"""
<linearGradient id="chipbody" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#43798a"/><stop offset="1" stop-color="#244c58"/></linearGradient>
<linearGradient id="die" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9fd0de"/><stop offset="1" stop-color="#5e9aab"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/><stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/></linearGradient>"""
    body = f"""
<g fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.9">{trace_svg}</g>
{via_svg}
{smd(150, 96, 0, "#f3d9e1")}{smd(500, 312, 0, "#d6eaf1")}{smd(140, 318, 90, "#f4e3c3")}{smd(512, 92, 90, "#d6eaf1")}
<rect x="{cx - half - 6}" y="{cy - half - 6}" width="{2 * half + 12}" height="{2 * half + 12}" rx="18" fill="{INK}" opacity="0.08"/>
<g fill="{GOLD}" stroke="#b98a3e" stroke-width="1">{"".join(pinrects)}</g>
<rect x="{cx - half}" y="{cy - half}" width="{2 * half}" height="{2 * half}" rx="14" fill="url(#chipbody)" stroke="{INK}" stroke-width="2.5"/>
<rect x="{cx - 40}" y="{cy - 40}" width="80" height="80" rx="8" fill="url(#die)" stroke="#ffffff" stroke-opacity="0.6" stroke-width="2"/>
<g stroke="#ffffff" stroke-opacity="0.35" stroke-width="1">{die_grid}</g>
<rect x="{cx - half}" y="{cy - half}" width="{2 * half}" height="{2 * half}" rx="14" fill="url(#sheen)"/>
<circle cx="{cx - half + 14}" cy="{cy - half + 14}" r="4" fill="{GOLD}"/>
{sparkle(600, 200, 7, GOLD, 0.7)}{sparkle(40, 200, 7, SKY, 0.9)}
"""
    return svg(body, defs, glow=(0.8, 0.1), glow2=(0.15, 0.95))


# --------------------------------------------------------------------- space
def space():
    rnd = random.Random(3)
    ecx, ecy, er = 320, 690, 400
    stars = "".join(
        f'<circle cx="{rnd.randint(10, 630)}" cy="{rnd.randint(10, 250)}" r="{rnd.choice((0.9, 1.2, 1.6))}" '
        f'fill="{INK}" fill-opacity="{rnd.choice((0.2, 0.3, 0.45))}"/>' for _ in range(46)
    )
    # Orbit: a tilted ellipse around Earth's centre.
    orx, ory, rot = 470, 520, math.radians(-7)

    def orbit(t):
        x, y = orx * math.cos(t), ory * math.sin(t)
        return ecx + x * math.cos(rot) - y * math.sin(rot), ecy + x * math.sin(rot) + y * math.cos(rot)

    orbit_pts = [orbit(math.radians(a / 2)) for a in range(360, 721)]
    t_sat = math.radians(-74)
    S = orbit(t_sat)
    S2 = orbit(t_sat + 0.01)
    ang = math.degrees(math.atan2(S2[1] - S[1], S2[0] - S[0]))
    # Rocket ascent.
    r0, rc, r1 = (150, 332), (158, 236), (226, 160)
    tdir = math.degrees(math.atan2(r1[1] - rc[1], r1[0] - rc[0])) + 90
    lat = "".join(
        f'<path d="M-40 {y}Q{ecx} {y - 70} 680 {y}" />' for y in (360, 395, 440)
    )
    defs = f"""
<linearGradient id="earthfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b6d8e3"/><stop offset="0.35" stop-color="#7fb2c4"/><stop offset="1" stop-color="#4f8a9d"/></linearGradient>
<radialGradient id="atmo" cx="{ecx}" cy="{ecy}" r="{er + 60}" gradientUnits="userSpaceOnUse"><stop offset="{n(er / (er + 60))}" stop-color="{SKY}" stop-opacity="0.55"/><stop offset="1" stop-color="{SKY}" stop-opacity="0"/></radialGradient>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6ea8ba"/><stop offset="1" stop-color="#2f6474"/></linearGradient>
<linearGradient id="foil" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6d79a"/><stop offset="1" stop-color="#d79c45"/></linearGradient>
<linearGradient id="flame" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe3a3"/><stop offset="1" stop-color="{BLUSH}" stop-opacity="0"/></linearGradient>
<clipPath id="earthclip"><circle cx="{ecx}" cy="{ecy}" r="{er}"/></clipPath>"""
    panel_lines = "".join(f'<path d="M{x} -11V11"/>' for x in (-60, -50, -40, 30, 40, 50, 60)) + '<path d="M-70 0H-24M24 0H70"/>'
    sat = f"""<g transform="translate({n(S[0])} {n(S[1])}) rotate({n(ang)}) scale(1.4)">
<path d="M-24 0H-14M14 0H24" stroke="{INK}" stroke-width="2"/>
<rect x="-70" y="-11" width="46" height="22" rx="2.5" fill="url(#panel)" stroke="{INK}" stroke-width="1.8"/>
<rect x="24" y="-11" width="46" height="22" rx="2.5" fill="url(#panel)" stroke="{INK}" stroke-width="1.8"/>
<g stroke="#ffffff" stroke-opacity="0.45" stroke-width="1">{panel_lines}</g>
<rect x="-14" y="-14" width="28" height="28" rx="4" fill="url(#foil)" stroke="{INK}" stroke-width="2"/>
<path d="M0 -14V-24" stroke="{INK}" stroke-width="2"/>
<path d="M-9 -28Q0 -20 9 -28" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>
</g>"""
    rocket = f"""<g transform="translate({r1[0]} {r1[1]}) rotate({n(tdir)}) scale(1.35)">
<path d="M-5 13Q0 40 5 13Z" fill="url(#flame)"/>
<path d="M0 -24C8 -15 9 0 7 13H-7C-9 0 -8 -15 0 -24Z" fill="#ffffff" stroke="{INK}" stroke-width="2"/>
<path d="M-7 4L-14 16H-6.5M7 4L14 16H6.5" fill="{BLUSH}" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>
<circle cx="0" cy="-7" r="3.5" fill="{SKY}" stroke="{INK}" stroke-width="1.5"/>
</g>"""
    body = f"""
{stars}
{sparkle(520, 58, 9, GOLD, 0.85)}{sparkle(84, 150, 7, SKY, 0.9)}{sparkle(600, 170, 5, BLUSH, 0.8)}
<circle cx="112" cy="78" r="22" fill="#f2f6f8" stroke="#b9cdd4" stroke-width="1.5"/>
<path d="M112 56A22 22 0 0 1 112 100A15 22 0 0 0 112 56Z" fill="#dbe7ec"/>
<circle cx="{ecx}" cy="{ecy}" r="{er + 60}" fill="url(#atmo)"/>
<circle cx="{ecx}" cy="{ecy}" r="{er}" fill="url(#earthfill)" stroke="{INK}" stroke-width="2.5"/>
<g clip-path="url(#earthclip)" fill="none" stroke="#ffffff" stroke-opacity="0.3" stroke-width="1.5">{lat}
<path d="M70 330C120 305 180 312 210 330S300 352 330 336" stroke-width="10" stroke-opacity="0.18" stroke-linecap="round"/>
<path d="M400 312C440 300 500 304 540 322" stroke-width="12" stroke-opacity="0.18" stroke-linecap="round"/>
</g>
<path d="{poly_path(orbit_pts)}" fill="none" stroke="{TEAL}" stroke-width="2" stroke-dasharray="2 8" stroke-linecap="round"/>
<path d="M{r0[0]} {r0[1]}Q{rc[0]} {rc[1]} {r1[0]} {r1[1]}" fill="none" stroke="{BLUSH}" stroke-width="2.5" stroke-dasharray="5 7" stroke-linecap="round"/>
{sat}
{rocket}
"""
    return svg(body, defs, glow=(0.85, 0.15), glow2=(0.5, 1.0), glow2_color="#d7ecf3")


# ---------------------------------------------------------------------- exam
def exam():
    A = (320, 30)
    base_y, half_w = 360, 128
    tan_a = half_w / (base_y - A[1])
    alpha = math.atan(tan_a)

    def side_x(y, s):
        return A[0] + s * (y - A[1]) * tan_a

    P1 = (side_x(135, -1), 135)
    P2 = (side_x(180, 1), 180)
    ux, uy = P2[0] - P1[0], P2[1] - P1[1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux

    def signed(yc):
        return nx * (A[0] - P1[0]) + ny * (yc - P1[1])

    # Spheres tangent to both cone sides and the plane: (yc - Ay) sin(alpha) = |signed(yc)|.
    spheres = []
    for sign in (1, -1):
        # (yc - Ay) sin a = sign * (nx*(Ax-P1x) + ny*(yc - P1y))  ->  linear in yc
        a = math.sin(alpha) - sign * ny
        bconst = A[1] * math.sin(alpha) + sign * (nx * (A[0] - P1[0]) - ny * P1[1])
        yc = bconst / a
        r = (yc - A[1]) * math.sin(alpha)
        spheres.append((yc, r))
    spheres.sort()
    feet = []
    for yc, r in spheres:
        d = signed(yc)
        feet.append((A[0] - d * nx, yc - d * ny))
    M = ((P1[0] + P2[0]) / 2, (P1[1] + P2[1]) / 2)
    rx, ry = L / 2, L / 2 * 0.34
    rot = math.degrees(math.atan2(uy, ux))
    t = math.radians(118)
    Q = (M[0] + rx * math.cos(t) * ux + ry * math.sin(t) * nx,
         M[1] + rx * math.cos(t) * uy + ry * math.sin(t) * ny)
    # Cutting plane: a rectangle around the ellipse, skewed for perspective.
    pa, pb, skew = rx + 50, ry + 26, 18

    def frame(a, b):
        return (M[0] + a * ux + b * nx, M[1] + a * uy + b * ny)

    plane = [frame(-pa + skew, -pb), frame(pa + skew, -pb), frame(pa - skew, pb), frame(-pa - skew, pb)]

    def ring(yc, r, color):
        # Circle where the sphere touches the cone.
        yt = yc - r * math.sin(alpha)
        w = (yt - A[1]) * tan_a
        return f'<ellipse cx="{A[0]}" cy="{n(yt)}" rx="{n(w)}" ry="{n(w * 0.2)}" fill="none" stroke="{color}" stroke-width="1.6" stroke-dasharray="4 5"/>'

    sph = []
    for idx, (yc, r) in enumerate(spheres):
        sph.append(f'<circle cx="{A[0]}" cy="{n(yc)}" r="{n(r)}" fill="url(#sphere)" stroke="{TEAL}" stroke-width="2"/>')
        sph.append(ring(yc, r, BLUSH if idx == 0 else TEAL))
    defs = f"""
<linearGradient id="cone" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#cfe4ec" stop-opacity="0.85"/><stop offset="0.45" stop-color="#eef6f9" stop-opacity="0.75"/><stop offset="1" stop-color="#b3d1dc" stop-opacity="0.85"/></linearGradient>
<radialGradient id="sphere" cx="0.36" cy="0.3" r="0.75"><stop offset="0" stop-color="#ffffff" stop-opacity="0.95"/><stop offset="0.6" stop-color="#cfe5ec" stop-opacity="0.8"/><stop offset="1" stop-color="{SKY}" stop-opacity="0.85"/></radialGradient>
<linearGradient id="plane" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fbe7ed" stop-opacity="0.75"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.55"/></linearGradient>"""
    bl, br = (A[0] - half_w, base_y), (A[0] + half_w, base_y)
    body = f"""
<ellipse cx="{A[0]}" cy="{base_y + 4}" rx="{half_w + 80}" ry="22" fill="{INK}" opacity="0.05"/>
<path d="M{bl[0]} {base_y}A{half_w} 26 0 0 1 {br[0]} {base_y}" fill="none" stroke="{MUTED}" stroke-width="1.8" stroke-dasharray="5 6"/>
<path d="M{A[0]} {A[1]}L{bl[0]} {base_y}A{half_w} 26 0 0 0 {br[0]} {base_y}Z" fill="url(#cone)"/>
{sph[2]}{sph[3]}
<path d="{poly_path(plane)}Z" fill="url(#plane)" stroke="#c6a3b1" stroke-width="1.6" stroke-linejoin="round"/>
<path d="M{A[0]} {A[1] + 4}V{base_y + 26}" stroke="{MUTED}" stroke-width="1.6" stroke-dasharray="3 7"/>
<ellipse cx="{n(M[0])}" cy="{n(M[1])}" rx="{n(rx)}" ry="{n(ry)}" transform="rotate({n(rot)} {n(M[0])} {n(M[1])})" fill="#ffffff" fill-opacity="0.35" stroke="{INK}" stroke-width="3"/>
{sph[0]}{sph[1]}
<path d="M{n(Q[0])} {n(Q[1])}L{n(feet[0][0])} {n(feet[0][1])}M{n(Q[0])} {n(Q[1])}L{n(feet[1][0])} {n(feet[1][1])}" stroke="{BLUSH}" stroke-width="2.4" stroke-linecap="round"/>
<path d="M{A[0]} {A[1]}L{bl[0]} {base_y}M{A[0]} {A[1]}L{br[0]} {base_y}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
<path d="M{bl[0]} {base_y}A{half_w} 26 0 0 0 {br[0]} {base_y}" fill="none" stroke="{INK}" stroke-width="3"/>
<circle cx="{n(feet[0][0])}" cy="{n(feet[0][1])}" r="5.5" fill="{GOLD}" stroke="#ffffff" stroke-width="2"/>
<circle cx="{n(feet[1][0])}" cy="{n(feet[1][1])}" r="5.5" fill="{GOLD}" stroke="#ffffff" stroke-width="2"/>
<circle cx="{n(Q[0])}" cy="{n(Q[1])}" r="5" fill="#ffffff" stroke="{BLUSH}" stroke-width="2.5"/>
<circle cx="{A[0]}" cy="{A[1]}" r="4" fill="{INK}"/>
{sparkle(540, 80, 9, GOLD, 0.8)}{sparkle(98, 110, 7, SKY, 0.9)}{sparkle(560, 310, 6, BLUSH, 0.7)}
"""
    return svg(body, defs, glow=(0.85, 0.2), glow2=(0.1, 0.9))


# ----------------------------------------------------------------- languages
def languages():
    rnd = random.Random(11)
    bars = []
    for y in range(58, 350, 18):
        x = 40 + rnd.choice((0, 0, 18, 36))
        while x < 600:
            w = rnd.randint(18, 90)
            if x + w > 600:
                break
            bars.append(f'<rect x="{x}" y="{y}" width="{w}" height="6" rx="3"/>')
            x += w + rnd.randint(8, 30)
            if rnd.random() < 0.35:
                break
    SLATE = "#6f8f9b"
    lanes = [
        (TEAL, "M40 205H600", [(70, True), (180, False), (330, False), (420, False), (548, False)]),
        (SKY, "M130 205C170 205 170 135 210 135H600", [(250, False), (370, False), (460, False), (556, False)]),
        (GOLD, "M290 135C325 135 325 74 360 74H600", [(410, False), (500, True), (572, False)]),
        (BLUSH, "M226 205C262 205 262 280 298 280H422C458 280 458 205 494 205", [(340, False), (390, False)]),
        (SLATE, "M372 205C408 205 408 326 444 326H600", [(486, False), (566, False)]),
    ]
    ys = {TEAL: 205, SKY: 135, GOLD: 74, BLUSH: 280, SLATE: 326}
    paths = "".join(f'<path d="{d}" stroke="{c}"/>' for c, d, _ in lanes)
    nodes = []
    for c, _, ns in lanes:
        for x, big in ns:
            if big:
                nodes.append(f'<circle cx="{x}" cy="{ys[c]}" r="10" fill="{c}" stroke="#ffffff" stroke-width="3.5"/>')
            else:
                nodes.append(f'<circle cx="{x}" cy="{ys[c]}" r="6.5" fill="{CARD}" stroke="{c}" stroke-width="3"/>')
    nodes.append(f'<circle cx="494" cy="205" r="10" fill="{BLUSH}" stroke="#ffffff" stroke-width="3.5"/>')
    defs = """
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.1" stop-color="#fff"/><stop offset="0.86" stop-color="#fff"/><stop offset="0.97" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="lanes"><rect width="640" height="400" fill="url(#fade)"/></mask>"""
    brace_l = "M112 66C88 66 84 78 84 100V170C84 190 76 200 60 200C76 200 84 210 84 230V300C84 322 88 334 112 334"
    brace_r = "M528 66C552 66 556 78 556 100V170C556 190 564 200 580 200C564 200 556 210 556 230V300C556 322 552 334 528 334"
    body = f"""
<g fill="#cadde4" fill-opacity="0.55">{"".join(bars)}</g>
<path d="{brace_l}M{brace_r[1:]}" fill="none" stroke="#b7ced6" stroke-width="5" stroke-linecap="round" opacity="0.7"/>
<g mask="url(#lanes)">
<g fill="none" stroke-width="12" stroke-linecap="round" opacity="0.12">{paths}</g>
<g fill="none" stroke-width="4" stroke-linecap="round">{paths}</g>
{"".join(nodes)}
</g>
{sparkle(300, 330, 7, GOLD, 0.8)}{sparkle(620, 40, 7, SKY, 0.9)}
"""
    return svg(body, defs, glow=(0.12, 0.1), glow2=(0.92, 0.95), glow2_color="#f3dbe3")


# ---------------------------------------------------------------- archimedes
def archimedes():
    cx, cy, R = 212, 204, 116

    def polygon(k, radius, phase=-90):
        return [(cx + radius * math.cos(math.radians(phase + 360 * i / k)),
                 cy + radius * math.sin(math.radians(phase + 360 * i / k))) for i in range(k)]

    k = 6
    inner = polygon(k, R)
    outer = polygon(k, R / math.cos(math.pi / k), -90 + 180 / k)
    finer = polygon(2 * k, R)
    # Convergence chart: perimeter bounds n sin(pi/n) and n tan(pi/n) closing on pi.
    # Log-scaled n axis (4 to 128) so the squeeze stays visible across the chart.
    x0, x1, y_lo, y_hi = 398, 590, 296, 112
    ns = [4 * 2 ** (j / 8) for j in range(41)]

    def X(i):
        return x0 + (x1 - x0) * i / (len(ns) - 1)

    def Y(v):
        return y_lo - (v - 2.78) / (4.06 - 2.78) * (y_lo - y_hi)

    lower = [(X(i), Y(m * math.sin(math.pi / m))) for i, m in enumerate(ns)]
    upper = [(X(i), Y(m * math.tan(math.pi / m))) for i, m in enumerate(ns)]
    marks = [0, 8, 16, 24, 32]
    defs = f"""
<linearGradient id="inner" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.2"/><stop offset="1" stop-color="{SKY}" stop-opacity="0.12"/></linearGradient>
<linearGradient id="gap" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BLUSH}" stop-opacity="0.22"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0.12"/></linearGradient>"""
    body = f"""
<circle cx="{cx}" cy="{cy}" r="{n(R / math.cos(math.pi / k) + 22)}" fill="#ffffff" fill-opacity="0.45"/>
<path d="M{cx - 160} {cy}H{cx + 160}M{cx} {cy - 160}V{cy + 160}" stroke="#d3e2e8" stroke-width="1.5"/>
<path d="{poly_path(outer)}Z" fill="{BLUSH}" fill-opacity="0.1" stroke="{BLUSH}" stroke-width="3" stroke-linejoin="round"/>
<path d="{poly_path(finer)}Z" fill="none" stroke="{SKY}" stroke-width="2" stroke-dasharray="5 6" stroke-linejoin="round"/>
<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{INK}" stroke-width="3"/>
<path d="{poly_path(inner)}Z" fill="url(#inner)" stroke="{TEAL}" stroke-width="3" stroke-linejoin="round"/>
<path d="M{cx} {cy}L{n(inner[1][0])} {n(inner[1][1])}M{cx} {cy}L{n(outer[0][0])} {n(outer[0][1])}" stroke="{MUTED}" stroke-width="2" stroke-dasharray="4 6"/>
{"".join(f'<circle cx="{n(x)}" cy="{n(y)}" r="4.5" fill="#ffffff" stroke="{TEAL}" stroke-width="2.2"/>' for x, y in inner)}
<circle cx="{cx}" cy="{cy}" r="5" fill="{INK}"/>
<circle cx="{n(inner[1][0])}" cy="{n(inner[1][1])}" r="6.5" fill="{GOLD}" stroke="#ffffff" stroke-width="2.5"/>
<rect x="374" y="86" width="238" height="236" rx="16" fill="#ffffff" fill-opacity="0.72" stroke="#d3e3e9"/>
<g stroke="#e2edf1" stroke-width="1">{"".join(f'<path d="M{x} 100V306"/>' for x in range(398, 591, 24))}</g>
<path d="{poly_path(upper)}{"".join(f"L{n(x)} {n(y)}" for x, y in reversed(lower))}Z" fill="url(#gap)"/>
<path d="M392 {n(Y(math.pi))}H596" stroke="{GOLD}" stroke-width="2.2" stroke-dasharray="6 6"/>
<path d="{poly_path(upper)}" fill="none" stroke="{BLUSH}" stroke-width="3.2" stroke-linecap="round"/>
<path d="{poly_path(lower)}" fill="none" stroke="{TEAL}" stroke-width="3.2" stroke-linecap="round"/>
{"".join(f'<circle cx="{n(upper[i][0])}" cy="{n(upper[i][1])}" r="4.5" fill="#ffffff" stroke="{BLUSH}" stroke-width="2.2"/><circle cx="{n(lower[i][0])}" cy="{n(lower[i][1])}" r="4.5" fill="#ffffff" stroke="{TEAL}" stroke-width="2.2"/>' for i in marks)}
<path d="M392 306H598M392 306V96" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>
{sparkle(64, 64, 8, GOLD, 0.8)}{sparkle(600, 352, 7, SKY, 0.9)}
"""
    return svg(body, defs, glow=(0.9, 0.1), glow2=(0.05, 0.95))


# ------------------------------------------------------ mathematics notebook
def mathematics_notebook():
    # App window: example sidebar, input cells, a 2D plot, a 3D surface, a slider.
    sidebar = "".join(
        f'<rect x="108" y="{y}" width="{w}" height="8" rx="4" fill="{c}"/>'
        for y, w, c in ((104, 70, "#cfe0e6"), (124, 84, "#cfe0e6"), (144, 58, "#f1d3dc"),
                        (164, 76, "#cfe0e6"), (184, 64, "#d6e9ef"), (204, 80, "#cfe0e6"), (224, 52, "#f3e3c3"))
    )

    def cell(y, widths):
        x, bars = 252, []
        for w, c in widths:
            bars.append(f'<rect x="{x}" y="{y + 11}" width="{w}" height="8" rx="4" fill="{c}"/>')
            x += w + 8
        return (f'<rect x="226" y="{y}" width="302" height="30" rx="8" fill="#ffffff" stroke="#d3e2e8"/>'
                f'<rect x="232" y="{y + 9}" width="12" height="12" rx="3" fill="{TEAL}" fill-opacity="0.75"/>'
                + "".join(bars) + f'<path d="M534 {y + 2}V{y + 28}" stroke="{SKY}" stroke-width="2.5" stroke-linecap="round"/>')

    px0, py0, pw, ph = 230, 176, 140, 96
    plot_a = [(px0 + 8 + t, py0 + ph / 2 - 30 * math.sin(t / 22)) for t in range(0, pw - 15, 2)]
    plot_b = [(px0 + 8 + t, py0 + ph / 2 - 18 * math.cos(t / 15)) for t in range(0, pw - 15, 2)]
    scx, scy = 454, 226

    def iso(x, y):
        z = math.sin(x * 1.3) * math.cos(y * 1.3)
        return scx + (x - y) * 15, scy + (x + y) * 6.5 - z * 16

    grid = [i * 0.25 - 2 for i in range(17)]
    surface = "".join(f'<path d="{poly_path([iso(a, b) for b in grid])}"/>' for a in grid[::2]) + \
              "".join(f'<path d="{poly_path([iso(a, b) for a in grid])}"/>' for b in grid[::2])
    body = f"""
<rect x="90" y="46" width="460" height="308" rx="18" fill="#ffffff" fill-opacity="0.74" stroke="#d3e2e8"/>
<path d="M90 80H550" stroke="#dce8ec"/>
<circle cx="112" cy="63" r="5" fill="{BLUSH}" fill-opacity="0.8"/><circle cx="129" cy="63" r="5" fill="{GOLD}" fill-opacity="0.8"/><circle cx="146" cy="63" r="5" fill="{SKY}"/>
<rect x="250" y="58" width="140" height="10" rx="5" fill="#e3edf1"/>
<rect x="470" y="56" width="62" height="14" rx="7" fill="{TEAL}" fill-opacity="0.85"/>
<path d="M210 80V354" stroke="#dce8ec"/>
<rect x="98" y="92" width="104" height="246" rx="10" fill="#f1f7f9"/>
{sidebar}
<rect x="104" y="140" width="98" height="16" rx="6" fill="{BLUSH}" fill-opacity="0.18"/>
{cell(96, ((88, "#cfe0e6"), (46, "#f1d3dc"), (60, "#cfe0e6")))}
{cell(134, ((54, "#cfe0e6"), (110, "#d6e9ef")))}
<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" rx="10" fill="#ffffff" stroke="#d3e2e8"/>
<path d="M{px0 + 8} {py0 + ph / 2}H{px0 + pw - 8}M{px0 + pw / 2} {py0 + 8}V{py0 + ph - 8}" stroke="#d3e2e8" stroke-width="1.5"/>
<path d="{poly_path(plot_b)}" fill="none" stroke="{BLUSH}" stroke-width="2.6" stroke-linecap="round"/>
<path d="{poly_path(plot_a)}" fill="none" stroke="{TEAL}" stroke-width="3" stroke-linecap="round"/>
<rect x="384" y="{py0}" width="140" height="{ph}" rx="10" fill="#ffffff" stroke="#d3e2e8"/>
<g fill="none" stroke="{TEAL}" stroke-width="1.4" stroke-opacity="0.75" stroke-linejoin="round">{surface}</g>
<rect x="226" y="290" width="302" height="46" rx="10" fill="#ffffff" stroke="#d3e2e8"/>
<path d="M246 313H508" stroke="#d3e2e8" stroke-width="5" stroke-linecap="round"/>
<path d="M246 313H404" stroke="{TEAL}" stroke-width="5" stroke-linecap="round"/>
<circle cx="404" cy="313" r="9" fill="{GOLD}" stroke="#ffffff" stroke-width="3"/>
{sparkle(592, 72, 9, GOLD, 0.8)}{sparkle(50, 330, 8, SKY, 0.9)}{sparkle(600, 320, 6, BLUSH, 0.8)}
"""
    return svg(body, glow=(0.88, 0.12), glow2=(0.06, 0.9))


COVERS = {
    "mathematics-notebook.svg": mathematics_notebook,
    "archimedes.svg": archimedes,
    "geoscience.svg": geoscience,
    "physics.svg": physics,
    "math.svg": mathematics,
    "cs.svg": cs,
    "electronics.svg": electronics,
    "space.svg": space,
    "exam.svg": exam,
    "languages.svg": languages,
}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else COVERS_DIR
    for name, make in COVERS.items():
        (out / name).write_text(make())
        print(name, len((out / name).read_text()), "bytes")


if __name__ == "__main__":
    main()
