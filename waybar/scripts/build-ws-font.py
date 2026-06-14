#!/usr/bin/env python3
"""
Build a custom workspace-indicator icon font for waybar (barred Roman numerals).

Each workspace (1-10) maps to ONE glyph: the numeral's strokes, capped by a
single continuous bar across the whole TOP and the whole BOTTOM of the numeral
(spanning all strokes, not a serif per stroke). Bar width = numeral width plus
a small overhang so a lone "I" still reads as capped.

  - true vector (crisp at any size/scale)
  - mapped by workspace ID via format-icons (multi-monitor stays clean, no
    persistent-workspaces / nth-child hacks)
  - fully editable via the geometry constants below.

Codepoints: workspace N -> chr('a' + N-1), i.e. ws1='a' ... ws10='j'.
Output: ~/.local/share/fonts/WaybarWS-Regular.ttf  (family "Waybar WS")
"""
import math
import os
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

UPM = 1000
H = 400         # stroke height, sits on baseline y=0 (shorter character;
                   # H+2*BAR_T = 900 -> 18px at 20px font -> even 9/9 gaps)
T = 120            # stroke thickness
BAR_T = 120        # thickness of the top & bottom bars
OVERHANG = 100     # how far the bars extend past the outer strokes (each side)
GAP = 70           # gap between sub-strokes in a composite numeral
SIDE = 90          # left/right side bearing (around actual ink)
Y_SHIFT = 0        # vertical offset in em (0 = centered for our metrics)

# Sub-glyph cell widths.  V/X are WIDE so the diagonals open up (more angle =
# more empty space between the arms = stays readable under the bars).
W_I = 120          # == T, so I strokes pack tightly under a shared bar
W_V = 440          # ~0.9*H: keeps the diagonal angle readable at this height
W_X = 440          # (too wide vs H -> the X flattens into an hourglass)
EDGE = 70          # inset of diagonal stroke ends from the cell edge


def stroke_quad(p1, p2, w):
    """4 corners of a rectangle/parallelogram for a stroke p1->p2 of width w."""
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L, dx / L
    hw = w / 2.0
    return [
        (x1 + px * hw, y1 + py * hw),
        (x2 + px * hw, y2 + py * hw),
        (x2 - px * hw, y2 - py * hw),
        (x1 - px * hw, y1 - py * hw),
    ]


def full_bar(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def glyph_I(x0):
    cx = x0 + W_I / 2.0
    return [stroke_quad((cx, 0), (cx, H), T)], W_I


def glyph_V(x0):
    cb = x0 + W_V / 2.0
    return [
        stroke_quad((x0 + EDGE, H), (cb, 0), T),
        stroke_quad((x0 + W_V - EDGE, H), (cb, 0), T),
    ], W_V


def glyph_X(x0):
    return [
        stroke_quad((x0 + EDGE, H), (x0 + W_X - EDGE, 0), T),
        stroke_quad((x0 + W_X - EDGE, H), (x0 + EDGE, 0), T),
    ], W_X


SUBGLYPHS = {"I": glyph_I, "V": glyph_V, "X": glyph_X}
NUMERALS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
}


def build_numeral(seq):
    quads = []
    x = 0.0
    for i, ch in enumerate(seq):
        sub, w = SUBGLYPHS[ch](x)
        quads.extend(sub)
        x += w
        if i != len(seq) - 1:
            x += GAP
    return quads


def _ccw(pts):
    area = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area > 0


def make_glyph(seq):
    quads = build_numeral(seq)
    xs = [p[0] for q in quads for p in q]
    bx0, bx1 = min(xs) - OVERHANG, max(xs) + OVERHANG
    # bars sit OUTSIDE the strokes: top bar caps the top of the strokes (y=H)
    # and extends upward; bottom bar caps the bottom (y=0) and extends downward.
    quads.append(full_bar(bx0, bx1, H, H + BAR_T))
    quads.append(full_bar(bx0, bx1, -BAR_T, 0))

    ink_w = bx1 - bx0
    pen = TTGlyphPen(None)
    for quad in quads:
        pts = [(round(px - bx0 + SIDE), round(py + Y_SHIFT)) for px, py in quad]
        if not _ccw(pts):          # normalise winding so overlaps fill solid
            pts = pts[::-1]
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    advance = round(ink_w + 2 * SIDE)
    return pen.glyph(), advance


def main():
    glyph_order = [".notdef"] + [f"ws{n}" for n in range(1, 11)]
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (600, 0)}
    cmap = {}
    for n in range(1, 11):
        name = f"ws{n}"
        g, adv = make_glyph(NUMERALS[n])
        glyphs[name] = g
        metrics[name] = (adv, SIDE)
        cmap[ord("a") + (n - 1)] = name

    # Contain the taller glyph (-BAR_T .. H+BAR_T) with a small margin, kept
    # symmetric about the glyph centre (H/2) so it stays vertically centred.
    asc = H + BAR_T + 20
    desc = BAR_T + 20

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=asc, descent=-desc)
    fb.setupNameTable({
        "familyName": "Waybar WS",
        "styleName": "Regular",
        "psName": "WaybarWS-Regular",
        "fullName": "Waybar WS Regular",
    })
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=-desc, usWinAscent=asc, usWinDescent=desc)
    fb.setupPost()

    out_dir = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "WaybarWS-Regular.ttf")
    fb.font.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
