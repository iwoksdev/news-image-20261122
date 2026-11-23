#!/usr/bin/env python3
"""High-resolution pixel scenes for the Nov 22 broadsheet (v3).

The user loved the chunky pixel lead but judged the 12 card scenes far too
coarse (96x27 grids). So each card scene is drawn SEPARATELY here, at twice
its slot size, and render.py pastes it back with a single NEAREST step to
the exact slot — the artwork lands at full slot resolution (1x1 pixels).
Only the drawings are pixel art: page typography, the main world map, the
index and the stat strip stay smooth.

Coordinate system: every scene is drawn in LOGICAL slot pixels (a grid card
is 192x54, a side card 344x47 or 344x45) and rendered onto a canvas scaled
by S=2, so one logical pixel is a crisp 2x2 block in the PNG and exactly
one pixel in the slot after the NEAREST downscale. All text uses bitmap
glyphs defined here (my own letterforms); no Pillow fonts anywhere.
Deterministic: no randomness, no timestamps, no network.
"""
import json
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 2  # draw scale: logical slot px -> PNG px

# ---------------------------------------------------------------- palette
INK = (30, 30, 34)
INK_SOFT = (90, 86, 78)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
CREAM = (238, 232, 214)
GOLD = (201, 168, 106)
GOLD_LT = (255, 217, 122)
DARK = (20, 20, 31)

# F7: 7x10 bitmap glyphs, my own letterforms (chips and scene labels).
F7 = {
    "A": ("0111110", "1000001", "1000001", "1000001", "1111111",
          "1000001", "1000001", "1000001", "1000001", "1000001"),
    "C": ("0111110", "1000001", "1000000", "1000000", "1000000",
          "1000000", "1000000", "1000000", "1000001", "0111110"),
    "D": ("1111100", "1000010", "1000001", "1000001", "1000001",
          "1000001", "1000001", "1000001", "1000010", "1111100"),
    "E": ("1111111", "1000000", "1000000", "1000000", "1111100",
          "1000000", "1000000", "1000000", "1000000", "1111111"),
    "F": ("1111111", "1000000", "1000000", "1000000", "1111100",
          "1000000", "1000000", "1000000", "1000000", "1000000"),
    "G": ("0111110", "1000001", "1000000", "1000000", "1000000",
          "1001111", "1000001", "1000001", "1000001", "0111110"),
    "H": ("1000001", "1000001", "1000001", "1000001", "1111111",
          "1000001", "1000001", "1000001", "1000001", "1000001"),
    "I": ("0111110", "0001000", "0001000", "0001000", "0001000",
          "0001000", "0001000", "0001000", "0001000", "0111110"),
    "K": ("1000001", "1000010", "1000100", "1001000", "1110000",
          "1001000", "1000100", "1000010", "1000001", "1000001"),
    "L": ("1000000", "1000000", "1000000", "1000000", "1000000",
          "1000000", "1000000", "1000000", "1000000", "1111111"),
    "M": ("1000001", "1100011", "1010101", "1010101", "1001001",
          "1000001", "1000001", "1000001", "1000001", "1000001"),
}
F7.update({
    "N": ("1000001", "1100001", "1010001", "1001001", "1000101",
          "1000011", "1000001", "1000001", "1000001", "1000001"),
    "O": ("0111110", "1000001", "1000001", "1000001", "1000001",
          "1000001", "1000001", "1000001", "1000001", "0111110"),
    "P": ("1111110", "1000001", "1000001", "1000001", "1111110",
          "1000000", "1000000", "1000000", "1000000", "1000000"),
    "R": ("1111110", "1000001", "1000001", "1000001", "1111110",
          "1001000", "1000100", "1000010", "1000001", "1000001"),
    "S": ("0111110", "1000001", "1000000", "1000000", "0111110",
          "0000001", "0000001", "0000001", "1000001", "0111110"),
    "T": ("1111111", "0001000", "0001000", "0001000", "0001000",
          "0001000", "0001000", "0001000", "0001000", "0001000"),
    "U": ("1000001", "1000001", "1000001", "1000001", "1000001",
          "1000001", "1000001", "1000001", "1000001", "0111110"),
    "V": ("1000001", "1000001", "1000001", "1000001", "1000001",
          "1000001", "1000001", "0100010", "0100010", "0011100"),
    "Y": ("1000001", "1000001", "1000001", "0100010", "0011100",
          "0001000", "0001000", "0001000", "0001000", "0001000"),
    "Z": ("1111111", "0000001", "0000010", "0000100", "0001000",
          "0010000", "0100000", "1000000", "1000000", "1111111"),
    "0": ("0111110", "1000001", "1000011", "1000101", "1001001",
          "1010001", "1100001", "1000001", "1000001", "0111110"),
    "1": ("0001000", "0011000", "0101000", "0001000", "0001000",
          "0001000", "0001000", "0001000", "0001000", "0111110"),
    "2": ("0111110", "1000001", "0000001", "0000010", "0000100",
          "0001000", "0010000", "0100000", "1000000", "1111111"),
    "3": ("1111110", "0000001", "0000001", "0000001", "0111110",
          "0000001", "0000001", "0000001", "0000001", "1111110"),
    "4": ("0000010", "0000110", "0001010", "0010010", "0100010",
          "1111111", "0000010", "0000010", "0000010", "0000010"),
    "5": ("1111111", "1000000", "1000000", "1111110", "0000001",
          "0000001", "0000001", "0000001", "1000001", "0111110"),
    "6": ("0111110", "1000001", "1000000", "1000000", "1111110",
          "1000001", "1000001", "1000001", "1000001", "0111110"),
    "7": ("1111111", "0000001", "0000010", "0000010", "0000100",
          "0001000", "0001000", "0010000", "0010000", "0010000"),
    "8": ("0111110", "1000001", "1000001", "1000001", "0111110",
          "1000001", "1000001", "1000001", "1000001", "0111110"),
    "9": ("0111110", "1000001", "1000001", "1000001", "1000001",
          "0111111", "0000001", "0000001", "1000001", "0111110"),
    ".": ("0000000", "0000000", "0000000", "0000000", "0000000",
          "0000000", "0000000", "0000000", "0011000", "0011000"),
    "%": ("1100011", "1100010", "0000100", "0001000", "0001000",
          "0010000", "0100000", "1000011", "1000011", "0000000"),
    "/": ("0000001", "0000010", "0000010", "0000100", "0001000",
          "0010000", "0100000", "0100000", "1000000", "1000000"),
    "–": ("0000000", "0000000", "0000000", "0000000", "1111111",
          "0000000", "0000000", "0000000", "0000000", "0000000"),
    " ": ("0000000", "0000000", "0000000", "0000000", "0000000",
          "0000000", "0000000", "0000000", "0000000", "0000000"),
})

# F5: 5x7 bitmap glyphs, my own letterforms (tiny labels: hull name, GAZA).
F5 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "00100", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
F5.update({
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "01010", "01010", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "10011", "10011"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "–": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
})

# ---------------------------------------------------------------- helpers
# All drawing takes LOGICAL slot pixels; every primitive scales by S=2.
def cv(w, h, bg):
    """Blank scene canvas at 2x the slot size."""
    im = Image.new("RGB", (w * S, h * S), bg)
    return im, ImageDraw.Draw(im)


def R(g, x, y, w, h, c, o=None):
    g.rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1],
                fill=c, outline=o)


def P(g, x, y, c):
    g.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=c)


def LN(g, pts, c, w=1):
    g.line([(x * S, y * S) for x, y in pts], fill=c, width=max(1, w * S))


def EL(g, x0, y0, x1, y1, c, o=None):
    g.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], fill=c, outline=o)


def PG(g, pts, c, o=None):
    g.polygon([(x * S, y * S) for x, y in pts], fill=c, outline=o)


def TXT(g, x, y, s, font, c):
    """Draw bitmap text; one glyph pixel = one logical pixel (2x2 in PNG).
    Returns the width in logical px."""
    cx = x
    for ch in s:
        gl = font.get(ch, font[" "])
        for ry, row in enumerate(gl):
            for rx, bit in enumerate(row):
                if bit == "1":
                    P(g, cx + rx, y + ry, c)
        cx += len(gl[0]) + 1
    return cx - x - 1


def TXT_W(s, font):
    return sum(len(font.get(ch, font[" "])[0]) + 1 for ch in s) - 1


def TXT_C(g, cx, y, s, font, c):
    return TXT(g, cx - TXT_W(s, font) // 2, y, s, font, c)


def CHIP(g, x, y, s, fill):
    """Pixel chip, 13 logical px tall, F5 text (same small glyphs as the
    lead's NO DEAL chip) — the F7 chips crowded the small scenes."""
    tw = TXT_W(s, F5)
    R(g, x, y, tw + 8, 13, fill)
    TXT(g, x + 4, y + 3, s, F5, WHITE)
    return tw + 8


def CHIP2(g, x, y, l1, l2, fill):
    """Two-line pixel chip, 24 logical px tall, F5 text; the line break
    replaces the separator."""
    w = max(TXT_W(l1, F5), TXT_W(l2, F5)) + 8
    R(g, x, y, w, 24, fill)
    TXT(g, x + 4, y + 3, l1, F5, WHITE)
    TXT(g, x + 4, y + 14, l2, F5, WHITE)
    return w


def glow(g, x0, y0, x1, y1, c, mod=11):
    """Sparse deterministic glow dots (~1 in 11 logical pixels)."""
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            if (xx * 5 + yy * 11) % mod == 0:
                P(g, xx, yy, c)


with open(os.path.join(HERE, "map.json")) as fh:
    POLYS = json.load(fh)["polys"]


def region_map(w, h, lon0, lon1, lat0, lat1, sea, land):
    """One region of the Natural Earth landmass, rasterised at 2x onto its
    own canvas (my own projection; PIL fills the polygons)."""
    im = Image.new("RGB", (w * S, h * S), sea)
    dd = ImageDraw.Draw(im)
    for ring in POLYS:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        if max(xs) < lon0 or min(xs) > lon1 or max(ys) < lat0 or min(ys) > lat1:
            continue
        pts = [((lon - lon0) / (lon1 - lon0) * w * S,
                (lat1 - lat) / (lat1 - lat0) * h * S) for lon, lat in ring]
        if len(pts) >= 3:
            dd.polygon(pts, fill=land)
    return im

# ---------------------------------------------------------------- scenes
# Logical slot sizes: side cards 344x47 (drones) and 344x45 (bahrain);
# grid cards 192x54. Each scene is drawn at 2x and downscaled by render.py.
def scene_drones():
    """Night over Ukraine: two BIG drones over a burning block. Slot 344x47."""
    im, g = cv(344, 47, (13, 27, 46))
    # sparse stars
    for sx, sy in [(14, 6), (30, 3), (48, 8), (150, 6), (196, 7), (262, 2),
                   (282, 8), (310, 4), (330, 7), (180, 12)]:
        P(g, sx, sy, (220, 225, 235))
    # crescent moon, top right
    EL(g, 322, 4, 334, 16, (232, 228, 205))
    EL(g, 326, 4, 334, 16, (13, 27, 46))
    # BIG drone A (left): body, arms, 4 rotor discs, lights, camera
    R(g, 78, 14, 36, 8, (200, 205, 215))
    LN(g, [(80, 16), (64, 6)], (180, 185, 195), w=2)
    LN(g, [(112, 16), (128, 6)], (180, 185, 195), w=2)
    LN(g, [(80, 20), (64, 30)], (180, 185, 195), w=2)
    LN(g, [(112, 20), (128, 30)], (180, 185, 195), w=2)
    for rx, ry in [(56, 2), (122, 2), (56, 26), (122, 26)]:
        EL(g, rx, ry, rx + 16, ry + 6, (140, 145, 155), o=(90, 95, 105))
    P(g, 74, 18, (255, 60, 50))
    P(g, 116, 18, (80, 220, 120))
    R(g, 92, 22, 8, 4, (40, 44, 52))
    # BIG drone B (right, slightly higher)
    R(g, 222, 9, 32, 7, (200, 205, 215))
    LN(g, [(224, 11), (210, 3)], (180, 185, 195), w=2)
    LN(g, [(252, 11), (266, 3)], (180, 185, 195), w=2)
    LN(g, [(224, 14), (210, 22)], (180, 185, 195), w=2)
    LN(g, [(252, 14), (266, 22)], (180, 185, 195), w=2)
    for rx, ry in [(203, 0), (259, 0), (203, 19), (259, 19)]:
        EL(g, rx, ry, rx + 14, ry + 5, (140, 145, 155), o=(90, 95, 105))
    P(g, 218, 12, (255, 60, 50))
    P(g, 256, 12, (80, 220, 120))
    # interception burst near drone B
    bx, by = 292, 14
    for ox, oy in [(0, -7), (0, 7), (-7, 0), (7, 0), (-5, -5), (5, -5),
                   (-5, 5), (5, 5)]:
        P(g, bx + ox, by + oy, (255, 205, 90))
    R(g, bx - 2, by - 2, 5, 5, (255, 230, 150))
    # ground: city silhouette with lit windows
    R(g, 0, 38, 344, 9, (10, 16, 26))
    for bx, bw, bh in [(6, 34, 6), (20, 24, 4), (48, 28, 4), (82, 42, 8),
                       (110, 20, 5), (216, 38, 8), (250, 30, 5), (280, 22, 4),
                       (302, 34, 6), (320, 26, 6)]:
        R(g, bx, 38 - bh, bw, bh, (16, 26, 40))
        for wy in range(2):
            for wx in range(bw // 10 + 1):
                P(g, bx + 4 + wx * 10, 38 - bh + 2 + wy * 3, (255, 205, 110))
    # the Dymer block, hit and burning — big flames
    R(g, 140, 28, 36, 10, (24, 34, 50))
    PG(g, [(144, 28), (150, 14), (154, 24), (158, 12), (162, 24),
           (168, 16), (174, 28)], (255, 150, 50))
    PG(g, [(150, 28), (154, 20), (160, 28)], (255, 220, 90))
    glow(g, 146, 10, 172, 16, (255, 120, 40))
    return im


def scene_bahrain():
    """The Gulf: one BIG radar dish, Gulf coastline, Bahrain. Slot 344x45."""
    im, g = cv(344, 45, (185, 210, 226))
    # land: Saudi coast (top) with a bay; Qatar peninsula jutting from right
    PG(g, [(0, 0), (344, 0), (344, 10), (316, 14), (300, 20), (286, 26),
           (250, 28), (210, 24), (170, 18), (120, 14), (60, 12), (0, 16)],
       (224, 211, 178))
    PG(g, [(300, 20), (330, 16), (344, 20), (344, 34), (322, 32), (306, 26)],
       (224, 211, 178))
    # Bahrain island in the Gulf + marker ring
    EL(g, 132, 28, 152, 40, (224, 211, 178))
    EL(g, 124, 22, 160, 44, None, o=RED)
    R(g, 140, 32, 4, 4, RED)
    # headland under the dish so its base stands on land
    PG(g, [(236, 30), (284, 30), (280, 45), (240, 45)], (224, 211, 178))
    # BIG radar dish (right, on the coast): a real bowl, feed mast, pedestal
    PG(g, [(302, 6), (301, 12), (297, 17), (290, 22), (282, 25), (272, 27),
           (262, 28), (252, 27), (242, 25), (234, 22), (227, 17), (223, 12),
           (222, 6)], (245, 245, 240), o=(120, 120, 115))
    LN(g, [(262, 28), (262, 5)], (120, 120, 115), w=2)
    R(g, 258, 1, 8, 4, (200, 200, 195))
    R(g, 258, 28, 8, 10, (200, 200, 195))
    R(g, 248, 38, 28, 3, (200, 200, 195))
    # claimed strike: dashed red line from Bahrain to a burst near the dish
    for t in range(0, 21, 3):
        px = int(142 + (214 - 142) * t / 20)
        py = int(34 + (14 - 34) * t / 20)
        R(g, px, py, 3, 3, RED)
    ex, ey = 214, 14
    for ox, oy in [(0, -6), (0, 6), (-6, 0), (6, 0), (-4, -4), (4, -4),
                   (-4, 4), (4, 4)]:
        P(g, ex + ox, ey + oy, (255, 180, 80))
    R(g, ex - 2, ey - 2, 4, 4, (255, 230, 150))
    # chip top-left
    CHIP(g, 8, 3, "CLAIM VS DENIAL", RED)
    return im


def scene_hk():
    """Hong Kong at dusk: BIG Bank of China tower, ballot box. Slot 192x54."""
    im, g = cv(192, 54, (255, 176, 110))
    # dusk bands: orange, checkerboard seam, purple, water
    for yy in range(16, 28):
        for xx in range(192):
            if (xx + yy) % 2 == 0:
                P(g, xx, yy, (74, 52, 104))
    R(g, 0, 28, 192, 8, (74, 52, 104))
    R(g, 0, 38, 192, 16, (46, 64, 96))
    # sun, top right
    R(g, 178, 4, 8, 8, (255, 214, 140))
    # flanking towers (shorter, dark, lit windows)
    for fx, fh, fw in [(0, 18, 20), (22, 22, 18), (132, 20, 18),
                       (152, 16, 20), (174, 22, 18)]:
        R(g, fx, 38 - fh, fw, fh, (42, 36, 56))
    # Bank of China tower, BIG and central: triangular X-brace structure
    PG(g, [(64, 38), (96, 4), (128, 38)], (42, 36, 56))
    LN(g, [(70, 32), (122, 12)], (255, 214, 140), w=1)
    LN(g, [(122, 32), (70, 12)], (255, 214, 140), w=1)
    LN(g, [(78, 24), (114, 10)], (255, 214, 140), w=1)
    LN(g, [(114, 24), (78, 10)], (255, 214, 140), w=1)
    R(g, 95, 4, 2, 34, (255, 214, 140))
    # lit windows on flanking towers
    for wx, wy in [(10, 24), (28, 20), (138, 26), (158, 26), (180, 22),
                   (36, 30), (136, 30), (162, 30), (184, 28)]:
        P(g, wx, wy, (255, 214, 140))
    # water glints
    for wx in (20, 68, 116, 164):
        R(g, wx, 50, 15, 1, (255, 214, 140))
    # ballot box, BIG front right, with a big red check above it
    R(g, 140, 32, 34, 18, (245, 242, 235), o=(120, 110, 95))
    R(g, 147, 34, 20, 2, INK)
    LN(g, [(146, 24), (156, 34)], RED, w=2)
    LN(g, [(156, 34), (174, 10)], RED, w=2)
    # turnout chip
    CHIP(g, 6, 3, "98.79%", DARK)
    return im


def scene_cricket():
    """Wellington: BIG pitch, stumps, bat and ball. Slot 192x54."""
    im, g = cv(192, 54, (58, 122, 66))
    EL(g, -20, -30, 212, 84, None, o=(230, 235, 220))
    # pitch strip, BIG and horizontal
    R(g, 16, 14, 160, 28, (196, 172, 120))
    R(g, 16, 14, 1, 28, (245, 242, 235))
    R(g, 176, 14, 1, 28, (245, 242, 235))
    R(g, 16, 26, 160, 1, (245, 242, 235))
    # stumps + bails, BIG at the left end
    for dx in (0, 5, 10):
        R(g, 28 + dx, 16, 3, 18, (240, 210, 90))
    R(g, 28, 14, 13, 2, (240, 210, 90))
    # bat, BIG diagonal
    PG(g, [(84, 40), (92, 38), (118, 10), (110, 8)], (150, 105, 60))
    R(g, 108, 4, 3, 8, (150, 105, 60))
    # ball, BIG red
    EL(g, 140, 32, 152, 44, (178, 34, 34), o=WHITE)
    P(g, 146, 32, WHITE)
    P(g, 146, 44, WHITE)
    # scoreboard chip top right
    CHIP(g, 192 - 6 - (TXT_W("720/9", F5) + 8), 4, "720/9", DARK)
    TXT(g, 6, 44, "RECORD TOTAL", F7, (235, 235, 225))
    return im


def scene_f1():
    """Las Vegas at night: BIG open-wheel car, Stratosphere. Slot 192x54."""
    im, g = cv(192, 54, (12, 18, 40))
    R(g, 0, 20, 192, 16, (30, 26, 52))
    # Stratosphere needle (clear of the chip, right of it)
    PG(g, [(106, 38), (111, 4), (118, 38)], (70, 64, 100))
    R(g, 104, 2, 16, 4, (255, 190, 90))
    # hotel blocks with lit windows
    for fx, fh, fw in [(34, 16, 24), (64, 12, 22), (140, 14, 24),
                       (168, 18, 24)]:
        R(g, fx, 38 - fh, fw, fh, (36, 30, 60))
        for wy in range(2):
            for wx in range(3):
                P(g, fx + 4 + wx * 8, 38 - fh + 4 + wy * 6, (255, 200, 110))
    # track
    R(g, 0, 38, 192, 16, (52, 52, 58))
    for tx in range(12):
        R(g, tx * 16, 46, 8, 1, (240, 240, 235))
    # BIG open-wheel race car (centre), side profile
    R(g, 50, 24, 4, 16, (120, 20, 20))
    R(g, 44, 22, 16, 4, (178, 34, 34))
    R(g, 44, 30, 16, 3, (178, 34, 34))
    R(g, 130, 42, 14, 3, (178, 34, 34))
    PG(g, [(56, 38), (128, 38), (132, 44), (56, 44)], (178, 34, 34))
    PG(g, [(84, 38), (92, 28), (96, 38)], (178, 34, 34))
    R(g, 72, 34, 22, 6, (150, 28, 28))
    EL(g, 96, 32, 106, 42, (20, 20, 24), o=WHITE)
    EL(g, 58, 40, 74, 53, (15, 15, 18), o=(120, 120, 115))
    EL(g, 64, 46, 68, 50, (180, 180, 175))
    EL(g, 112, 40, 128, 53, (15, 15, 18), o=(120, 120, 115))
    EL(g, 118, 46, 122, 50, (180, 180, 175))
    # checkered flag
    fx0, fy0 = 172, 4
    for r in range(3):
        for c in range(4):
            if (r + c) % 2 == 0:
                R(g, fx0 + c * 4, fy0 + r * 4, 4, 4, (20, 20, 20))
    R(g, fx0, fy0, 1, 22, (220, 220, 215))
    # chip
    CHIP(g, 6, 3, "35 LEAD CHANGES", DARK)
    return im


def scene_tennis():
    """Turin: BIG net, ball and trophy on a blue court. Slot 192x54."""
    im, g = cv(192, 54, (47, 111, 178))
    R(g, 8, 6, 176, 42, None, o=(240, 240, 235))
    R(g, 8, 26, 176, 2, (240, 240, 235))
    R(g, 62, 6, 2, 42, (240, 240, 235))
    R(g, 130, 6, 2, 42, (240, 240, 235))
    # net, BIG across the middle: white top tape + mesh
    R(g, 8, 20, 176, 10, (235, 235, 228))
    R(g, 8, 20, 176, 3, (255, 255, 255))
    for nx in range(16, 176, 8):
        R(g, nx, 23, 1, 7, (120, 120, 115))
    R(g, 6, 18, 4, 14, (30, 30, 34))
    R(g, 182, 18, 4, 14, (30, 30, 34))
    # ball, BIG lime
    EL(g, 38, 6, 56, 24, (204, 255, 0), o=WHITE)
    P(g, 47, 6, WHITE)
    P(g, 47, 24, WHITE)
    # trophy, BIG gold at right
    tx, ty = 158, 36
    PG(g, [(tx - 12, ty - 14), (tx + 12, ty - 14), (tx + 7, ty + 2),
           (tx - 7, ty + 2)], (212, 175, 55))
    R(g, tx - 17, ty - 14, 5, 10, (212, 175, 55))
    R(g, tx + 12, ty - 14, 5, 10, (212, 175, 55))
    R(g, tx - 1, ty + 2, 2, 8, (212, 175, 55))
    R(g, tx - 10, ty + 10, 20, 4, (212, 175, 55))
    TXT(g, 6, 44, "MAIDEN TITLE", F7, (235, 235, 225))
    return im


def scene_football():
    """Anfield: BIG goal with net, ball, centre circle. Slot 192x54."""
    im, g = cv(192, 54, (46, 125, 62))
    R(g, 6, 4, 180, 46, None, o=(240, 240, 235))
    R(g, 96, 4, 2, 46, (240, 240, 235))
    EL(g, 82, 14, 112, 42, None, o=(240, 240, 235))
    R(g, 6, 16, 44, 22, None, o=(240, 240, 235))
    R(g, 142, 16, 44, 22, None, o=(240, 240, 235))
    # goal, BIG with a clear net (right)
    gx0, gy0 = 138, 10
    R(g, gx0, gy0, 48, 32, None, o=WHITE)
    for i in range(1, 6):
        R(g, gx0 + i * 8, gy0, 2, 32, (220, 220, 215))
        R(g, gx0, gy0 + i * 6, 48, 2, (220, 220, 215))
    # ball, BIG
    EL(g, 70, 26, 88, 44, (250, 250, 245), o=(30, 30, 30))
    R(g, 77, 32, 6, 6, (30, 30, 30))
    # scoreboard chip
    CHIP(g, 6, 3, "4–0", DARK)
    return im


def scene_manipur():
    """Manipur: pixel map of NE India, Imphal ring, hospital crosses. Slot 192x54."""
    im, g = cv(192, 54, (185, 210, 226))
    # NE India landmass, simplified low-res shape
    PG(g, [(16, 8), (60, 4), (120, 10), (176, 6), (186, 24), (170, 40),
           (120, 48), (60, 50), (24, 44), (8, 24)], (224, 211, 178))
    # darker hill patch for texture
    PG(g, [(80, 16), (110, 14), (124, 24), (110, 32), (84, 30)],
       (205, 192, 158))
    # Imphal ring + dot
    EL(g, 72, 24, 88, 40, None, o=RED)
    R(g, 78, 30, 2, 2, RED)
    # hospital crosses
    for cx, cy in [(58, 18), (106, 34), (138, 16)]:
        R(g, cx, cy - 4, 2, 9, RED)
        R(g, cx - 4, cy, 9, 2, RED)
    # toll chip
    CHIP(g, 30, 4, "17 DEAD", RED)
    return im


def scene_cikande():
    """Cikande: factory, sawtooth roof, flames, smoke. Slot 192x54."""
    im, g = cv(192, 54, (200, 195, 185))
    # sky bands: dusk grey top, pale bottom, checkerboard seam
    R(g, 0, 0, 192, 24, (140, 150, 165))
    for xx in range(192):
        if xx % 2 == 0:
            P(g, xx, 24, (200, 195, 185))
    # smoke puffs
    for cx, cy, r in [(58, 10, 10), (70, 6, 12), (84, 12, 8), (120, 8, 10),
                      (134, 12, 8)]:
        EL(g, cx - r, cy - r, cx + r, cy + r, (110, 112, 118))
        EL(g, cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4, (140, 142, 148))
    # factory body + sawtooth roof + chimney
    R(g, 8, 26, 184, 22, (138, 141, 144))
    for i in range(5):
        sx = 8 + i * 32
        PG(g, [(sx, 26), (sx + 16, 16), (sx + 32, 26)], (110, 113, 116))
    R(g, 158, 10, 8, 38, (100, 102, 105))
    # windows: 3 rows x 6 cols (third row clips below the box, as before)
    for wy in range(3):
        for wx in range(6):
            R(g, 16 + wx * 28, 30 + wy * 12, 4, 4, (255, 205, 110))
    # flames from the roof
    for cx in (48, 86, 124):
        PG(g, [(cx - 6, 26), (cx, 14), (cx + 4, 24), (cx + 8, 16),
               (cx + 10, 26)], (255, 150, 50))
        PG(g, [(cx - 2, 26), (cx, 20), (cx + 4, 26)], (255, 220, 90))
    # casualty chip: the string is too long for one pixel line, so it stacks
    CHIP2(g, 34, 4, "3 DEAD", "36 MISSING", RED)
    return im


def scene_sparta():
    """Sparta II: sea, burning ship, containers, lifeboat. Slot 192x54.

    The stern flame and smoke sit at the stern, left of the chip, so the
    fire reads (the old smooth version hid them behind the chip)."""
    im, g = cv(192, 54, (52, 96, 130))
    R(g, 0, 0, 192, 26, (120, 165, 195))
    for xx in range(192):
        if xx % 2 == 0:
            P(g, xx, 26, (52, 96, 130))
    # waves
    for wy in (30, 36, 44, 50):
        for wx in (10, 58, 106, 154):
            P(g, wx - 4, wy, (220, 235, 245))
            P(g, wx - 2, wy + 2, (220, 235, 245))
            P(g, wx, wy + 2, (220, 235, 245))
            P(g, wx + 2, wy + 2, (220, 235, 245))
            P(g, wx + 4, wy, (220, 235, 245))
    # smoke + flame at the stern
    for cx, cy, r in [(22, 10, 8), (28, 4, 8), (18, 4, 6)]:
        EL(g, cx - r, cy - r, cx + r, cy + r, (105, 108, 114))
    PG(g, [(20, 30), (24, 16), (26, 24), (28, 18), (30, 30)], (255, 150, 50))
    PG(g, [(22, 30), (24, 22), (28, 30)], (255, 220, 90))
    # hull + name + containers + bridge
    PG(g, [(16, 34), (176, 34), (166, 44), (26, 44)], (40, 44, 52))
    TXT(g, 62, 36, "SPARTA II", F5, (240, 240, 235))
    for i, col in enumerate([(178, 84, 44), (52, 96, 150), (90, 140, 70),
                             (178, 84, 44)]):
        R(g, 30 + i * 32, 20, 26, 12, col, o=(30, 30, 34))
    R(g, 158, 8, 14, 24, (235, 235, 230))
    R(g, 162, 2, 6, 6, (178, 34, 34))
    # lifeboat
    PG(g, [(110, 46), (128, 46), (126, 50), (112, 50)], (255, 140, 40))
    # chip
    CHIP(g, 30, 4, "16 SAFE", (46, 139, 87))
    return im


def scene_tehran():
    """Tehran at dusk: Milad Tower, skyline, lightbulb. Slot 192x54."""
    im, g = cv(192, 54, (255, 150, 80))
    # dusk bands: purple top, orange bottom, checkerboard seam
    R(g, 0, 0, 192, 24, (88, 66, 122))
    for xx in range(192):
        if xx % 2 == 0:
            P(g, xx, 24, (255, 150, 80))
    # Milad Tower
    PG(g, [(120, 48), (128, 8), (132, 8), (140, 48)], (52, 44, 66))
    EL(g, 116, 10, 144, 22, (72, 60, 88))
    R(g, 126, 4, 8, 4, (255, 190, 90))
    # skyline
    for fx, fh, fw in [(0, 16, 24), (24, 22, 20), (46, 18, 24), (72, 26, 24),
                       (100, 20, 20), (150, 24, 24), (172, 18, 20)]:
        R(g, fx, 48 - fh, fw, fh, (48, 40, 60))
    # one lit window
    R(g, 76, 30, 4, 2, (255, 210, 110))
    # lightbulb, top left
    bx, by = 26, 12
    EL(g, bx - 6, by - 8, bx + 6, by + 6, None, o=(255, 235, 180))
    R(g, bx - 2, by + 6, 4, 2, (255, 235, 180))
    R(g, bx - 2, by + 10, 4, 1, (255, 235, 180))
    P(g, bx - 6, by - 12, (255, 235, 180))
    P(g, bx + 6, by - 12, (255, 235, 180))
    P(g, bx, by - 14, (255, 235, 180))
    # chip (starts at 86: the pixel chip is wider than the old smooth one)
    CHIP(g, 86, 4, "UP TO 2 HRS", DARK)
    return im


def scene_gaza():
    """Gaza coast: sea, sand, strip outline, aid truck. Slot 192x54."""
    im, g = cv(192, 54, (224, 211, 178))
    # sea left, coastline diagonal
    PG(g, [(0, 0), (80, 0), (58, 54), (0, 54)], (146, 186, 214))
    LN(g, [(80, 0), (58, 54)], (240, 240, 235), w=1)
    # Gaza strip outline (thin coastal strip)
    PG(g, [(84, 4), (108, 4), (96, 50), (74, 50)], None, o=RED)
    TXT(g, 112, 6, "GAZA", F5, INK_SOFT)
    # aid truck on the road
    tx, ty = 100, 36
    R(g, tx, ty - 12, 34, 14, (245, 245, 240), o=(120, 120, 115))
    R(g, tx + 34, ty - 8, 10, 10, (200, 205, 210), o=(120, 120, 115))
    R(g, tx + 14, ty - 10, 6, 6, RED)
    R(g, tx + 16, ty - 12, 2, 10, RED)
    R(g, tx + 6, ty, 4, 6, (20, 20, 24))
    R(g, tx + 26, ty, 4, 6, (20, 20, 24))
    R(g, tx + 38, ty, 4, 6, (20, 20, 24))
    # chip
    CHIP(g, 30, 4, "3 KILLED", RED)
    return im


SCENES = {
    "drones.png": (344, 47, scene_drones),
    "bahrain.png": (344, 45, scene_bahrain),
    "hk.png": (192, 54, scene_hk),
    "cricket.png": (192, 54, scene_cricket),
    "f1.png": (192, 54, scene_f1),
    "tennis.png": (192, 54, scene_tennis),
    "football.png": (192, 54, scene_football),
    "manipur.png": (192, 54, scene_manipur),
    "cikande.png": (192, 54, scene_cikande),
    "sparta.png": (192, 54, scene_sparta),
    "tehran.png": (192, 54, scene_tehran),
    "gaza.png": (192, 54, scene_gaza),
}


def main():
    out = os.path.join(HERE, "scenes")
    os.makedirs(out, exist_ok=True)
    for name, (w, h, fn) in SCENES.items():
        im = fn()
        assert im.size == (w * S, h * S), (name, im.size)
        im.save(os.path.join(out, name))


if __name__ == "__main__":
    main()
