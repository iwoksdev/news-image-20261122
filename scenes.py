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
    """Pixel chip, 18 logical px tall (same height as the page's chips),
    F7 text centred by pixel bbox."""
    tw = TXT_W(s, F7)
    R(g, x, y, tw + 8, 18, fill)
    TXT(g, x + 4, y + 4, s, F7, WHITE)
    return tw + 8


def CHIP2(g, x, y, l1, l2, fill):
    """Two-line pixel chip, 32 logical px tall, for a string too long for
    one pixel line; the line break replaces the separator."""
    w = max(TXT_W(l1, F7), TXT_W(l2, F7)) + 8
    R(g, x, y, w, 32, fill)
    TXT(g, x + 4, y + 3, l1, F7, WHITE)
    TXT(g, x + 4, y + 18, l2, F7, WHITE)
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
    """Night over Ukraine: drones, bursts, a burning block. Slot 344x47."""
    im, g = cv(344, 47, (13, 27, 46))
    R(g, 0, 18, 344, 16, (26, 51, 72))
    R(g, 0, 36, 344, 1, (39, 75, 99))
    # stars
    for sx, sy in [(14, 6), (30, 3), (48, 8), (70, 4), (96, 7), (120, 3),
                   (150, 6), (168, 2), (196, 7), (214, 3), (238, 6),
                   (262, 2), (282, 8), (310, 4), (330, 7), (40, 12),
                   (180, 12), (250, 11)]:
        P(g, sx, sy, (220, 225, 235))
    # crescent moon
    EL(g, 296, 4, 308, 16, (232, 228, 205))
    EL(g, 300, 4, 310, 16, (13, 27, 46))
    # drones: small X with a red and a green light
    for dx, dy in [(56, 14), (90, 20), (144, 10), (180, 8), (228, 18),
                   (260, 14), (290, 24), (320, 18)]:
        P(g, dx - 3, dy - 3, (200, 205, 215))
        P(g, dx + 3, dy - 3, (200, 205, 215))
        P(g, dx - 3, dy + 3, (200, 205, 215))
        P(g, dx + 3, dy + 3, (200, 205, 215))
        R(g, dx - 1, dy - 1, 2, 2, (230, 230, 230))
        P(g, dx - 5, dy, (255, 60, 50))
        P(g, dx + 5, dy, (80, 220, 120))
    # interception bursts
    for bx, by in [(104, 26), (200, 22), (248, 30), (300, 28)]:
        glow(g, bx - 8, by - 8, bx + 9, by + 9, (255, 170, 60))
        for ox, oy in [(0, -6), (0, 6), (-6, 0), (6, 0), (-4, -4), (4, -4),
                       (-4, 4), (4, 4)]:
            P(g, bx + ox, by + oy, (255, 205, 90))
        R(g, bx - 2, by - 2, 4, 4, (255, 230, 150))
    # ground: city silhouette with lit windows
    R(g, 0, 38, 344, 9, (10, 16, 26))
    for bx, bw, bh in [(6, 34, 6), (20, 24, 4), (48, 28, 4), (82, 42, 8),
                       (110, 20, 5), (140, 26, 7), (178, 32, 6),
                       (216, 38, 8), (250, 30, 5), (280, 22, 4),
                       (302, 34, 6), (320, 26, 6)]:
        R(g, bx, 38 - bh, bw, bh, (16, 26, 40))
        for wy in range(2):
            for wx in range(bw // 10 + 1):
                P(g, bx + 4 + wx * 10, 38 - bh + 2 + wy * 3, (255, 205, 110))
    # the Dymer block, hit and burning
    R(g, 130, 28, 34, 10, (24, 34, 50))
    glow(g, 134, 22, 162, 30, (255, 120, 40))
    P(g, 140, 24, (255, 150, 50))
    P(g, 148, 22, (255, 220, 90))
    P(g, 154, 24, (255, 150, 50))
    R(g, 146, 25, 3, 3, (255, 200, 80))
    return im


def scene_bahrain():
    """The Gulf: Bahrain, two radar dishes, claim vs denial. Slot 344x45."""
    im = region_map(344, 45, 47, 57, 24, 30, (185, 210, 226), (224, 211, 178))
    g = ImageDraw.Draw(im)
    # Bahrain island marker
    bx, by = 124, 30
    EL(g, bx - 8, by - 8, bx + 8, by + 8, None, o=RED)
    R(g, bx - 1, by - 1, 3, 3, RED)
    # radar dishes at al-Riffa and Awali
    for dx, dy in [(214, 20), (268, 26)]:
        R(g, dx, dy + 2, 1, 8, (240, 240, 235))
        R(g, dx - 6, dy + 10, 13, 1, (240, 240, 235))
        R(g, dx - 8, dy - 6, 17, 4, (245, 245, 240))
        R(g, dx - 4, dy - 8, 9, 2, (245, 245, 240))
        R(g, dx - 8, dy - 2, 17, 1, (120, 120, 115))
    # claimed strike: dashed red line to a burst
    ex, ey = 240, 14
    for t in range(0, 21, 3):
        px = int(bx + (ex - bx) * t / 20)
        py = int(by + (ey - by) * t / 20)
        R(g, px, py, 3, 3, RED)
    for ox, oy in [(0, -6), (0, 6), (-6, 0), (6, 0), (-4, -4), (4, -4),
                   (-4, 4), (4, 4)]:
        P(g, ex + ox, ey + oy, (255, 180, 80))
    R(g, ex - 2, ey - 2, 4, 4, (255, 230, 150))
    # chip top-left, clear of the marker ring
    CHIP(g, 38, 4, "CLAIM VS DENIAL", RED)
    return im


SCENES = {
    "drones.png": (344, 47, scene_drones),
    "bahrain.png": (344, 45, scene_bahrain),
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
