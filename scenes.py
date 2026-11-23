#!/usr/bin/env python3
"""High-resolution pixel scenes for the Nov 22 broadsheet (v5).

Every scene is drawn DIRECTLY at its final slot resolution — 1x1 pixels,
no intermediate canvas, no downscale, no NEAREST resize anywhere. A grid
card is 192x54, a side card 344x47 or 344x45, and every pixel placed here
survives into the page. Only the drawings are pixel art: page typography,
the index and the stat strip stay smooth.

Each scene is a small story in three layers — background, midground,
foreground — with 2-3 big, frame-filling, instantly recognizable elements.
All text uses bitmap glyphs defined here (my own letterforms); no Pillow
fonts anywhere. Deterministic: no randomness, no timestamps, no network.
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

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
# Every primitive draws DIRECTLY at final slot resolution (1x1 pixels).
# One logical pixel IS one final pixel; nothing is scaled or downsampled.
def cv(w, h, bg):
    """Blank scene canvas at exactly the slot size."""
    im = Image.new("RGB", (w, h), bg)
    return im, ImageDraw.Draw(im)


def R(g, x, y, w, h, c, o=None):
    g.rectangle([x, y, x + w - 1, y + h - 1], fill=c, outline=o)


def P(g, x, y, c):
    g.point((x, y), fill=c)


def LN(g, pts, c, w=1):
    g.line(pts, fill=c, width=w)


def EL(g, x0, y0, x1, y1, c, o=None):
    g.ellipse([x0, y0, x1, y1], fill=c, outline=o)


def PG(g, pts, c, o=None):
    g.polygon(pts, fill=c, outline=o)


def TXT(g, x, y, s, font, c):
    """Draw bitmap text; one glyph pixel = one final pixel.
    Returns the width in px."""
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
    """Pixel chip, 13 px tall, F5 text."""
    tw = TXT_W(s, F5)
    R(g, x, y, tw + 8, 13, fill)
    TXT(g, x + 4, y + 3, s, F5, WHITE)
    return tw + 8


def CHIP2(g, x, y, l1, l2, fill):
    """Two-line pixel chip, 24 px tall, F5 text."""
    w = max(TXT_W(l1, F5), TXT_W(l2, F5)) + 8
    R(g, x, y, w, 24, fill)
    TXT(g, x + 4, y + 3, l1, F5, WHITE)
    TXT(g, x + 4, y + 14, l2, F5, WHITE)
    return w


def glow(g, x0, y0, x1, y1, c, mod=11):
    """Sparse deterministic glow dots (~1 in 11 pixels)."""
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            if (xx * 5 + yy * 11) % mod == 0:
                P(g, xx, yy, c)


def flame(g, x, y0, w, h, c1=(255, 150, 50), c2=(255, 220, 90)):
    """One flame tongue: outer flame + bright inner core, base at y0."""
    PG(g, [(x - w // 2, y0), (x - w // 4, y0 - h), (x, y0 - h // 2),
           (x + w // 4, y0 - h), (x + w // 2, y0)], c1)
    PG(g, [(x - w // 4, y0), (x, y0 - h * 2 // 3), (x + w // 4, y0)], c2)


def smoke(g, cx, cy, r, c1=(105, 108, 114), c2=(140, 142, 148)):
    """One smoke puff: dark ring + pale core."""
    EL(g, cx - r, cy - r, cx + r, cy + r, c1)
    EL(g, cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4, c2)


# ---------------------------------------------------------------- scenes
# Slot sizes: side cards 344x47 (drones) and 344x45 (bahrain);
# grid cards 192x54. Each scene is drawn DIRECTLY at its slot size.
def scene_drones():
    """Night over Ukraine: searchlights, tracers, two BIG drones, a burning
    block with a smoke column. Slot 344x47."""
    im, g = cv(344, 47, (13, 27, 46))
    # background: stars + crescent moon
    for sx, sy in [(14, 6), (30, 3), (48, 8), (150, 6), (196, 7), (262, 2),
                   (282, 8), (310, 4), (330, 7), (180, 12), (96, 4),
                   (240, 5), (120, 9)]:
        P(g, sx, sy, (220, 225, 235))
    EL(g, 322, 4, 334, 16, (232, 228, 205))
    EL(g, 326, 4, 334, 16, (13, 27, 46))
    # searchlight beams sweeping up from the ground
    PG(g, [(58, 38), (62, 38), (40, 2), (36, 2)], (255, 230, 150))
    PG(g, [(288, 38), (292, 38), (312, 2), (308, 2)], (255, 230, 150))
    R(g, 57, 37, 6, 2, (255, 240, 180))
    R(g, 287, 37, 6, 2, (255, 240, 180))
    # tracer dashes rising from the ground
    for tx, ty in [(100, 34), (104, 27), (108, 20), (200, 34), (196, 27),
                   (192, 20)]:
        R(g, tx, ty, 1, 4, (255, 90, 70))
    # midground: a small distant drone, far left
    R(g, 40, 24, 16, 4, (170, 175, 185))
    R(g, 36, 22, 24, 1, (150, 155, 165))
    P(g, 38, 26, (255, 60, 50))
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
    # foreground: city silhouette with lit windows
    R(g, 0, 38, 344, 9, (10, 16, 26))
    for bx, bw, bh in [(6, 34, 6), (20, 24, 4), (48, 28, 4), (82, 42, 8),
                       (110, 20, 5), (216, 38, 8), (250, 30, 5), (280, 22, 4),
                       (302, 34, 6), (320, 26, 6)]:
        R(g, bx, 38 - bh, bw, bh, (16, 26, 40))
        for wy in range(2):
            for wx in range(bw // 10 + 1):
                P(g, bx + 4 + wx * 10, 38 - bh + 2 + wy * 3, (255, 205, 110))
    # the Dymer block, hit and burning — BIG flames + smoke column
    R(g, 140, 28, 36, 10, (24, 34, 50))
    flame(g, 148, 28, 10, 18)
    flame(g, 158, 28, 12, 22)
    flame(g, 168, 28, 10, 16)
    smoke(g, 152, 8, 5)
    smoke(g, 160, 2, 6)
    glow(g, 146, 8, 172, 14, (255, 120, 40))
    return im


def scene_bahrain():
    """The Gulf: deep sea, a tanker, one BIG radar dish, Bahrain island,
    the claimed strike with smoke. Slot 344x45."""
    im, g = cv(344, 45, (120, 175, 205))
    # background: Saudi coast (top) with a bay; Qatar peninsula, right
    PG(g, [(0, 0), (344, 0), (344, 10), (316, 14), (300, 20), (286, 26),
           (250, 28), (210, 24), (170, 18), (120, 14), (60, 12), (0, 16)],
       (215, 195, 155))
    PG(g, [(300, 20), (330, 16), (344, 20), (344, 34), (322, 32), (306, 26)],
       (215, 195, 155))
    # Bahrain island in the Gulf + marker ring
    EL(g, 132, 28, 152, 40, (215, 195, 155))
    EL(g, 124, 22, 160, 44, None, o=RED)
    R(g, 140, 32, 4, 4, RED)
    # headland under the dish so its base stands on land
    PG(g, [(236, 30), (284, 30), (280, 45), (240, 45)], (215, 195, 155))
    # BIG radar dish (right, on the coast): a real bowl, feed mast, pedestal
    PG(g, [(302, 6), (301, 12), (297, 17), (290, 22), (282, 25), (272, 27),
           (262, 28), (252, 27), (242, 25), (234, 22), (227, 17), (223, 12),
           (222, 6)], (245, 245, 240), o=(90, 90, 85))
    LN(g, [(262, 28), (262, 5)], (90, 90, 85), w=2)
    R(g, 258, 1, 8, 4, (200, 200, 195))
    R(g, 258, 28, 8, 10, (200, 200, 195))
    R(g, 248, 38, 28, 3, (200, 200, 195))
    # foreground: a tanker crossing the Gulf, with a wake
    PG(g, [(40, 36), (92, 36), (88, 42), (44, 42)], (40, 44, 52))
    R(g, 48, 30, 12, 6, (178, 84, 44))
    R(g, 62, 30, 12, 6, (52, 96, 150))
    R(g, 84, 28, 6, 8, (235, 235, 230))
    for wx in (30, 24, 18):
        R(g, wx, 39, 4, 1, (240, 244, 248))
    # claimed strike: dashed red line from Bahrain to a burst near the dish
    for t in range(0, 21, 3):
        px = int(142 + (214 - 142) * t / 20)
        py = int(34 + (16 - 34) * t / 20)
        R(g, px, py, 3, 3, RED)
    ex, ey = 214, 16
    for ox, oy in [(0, -6), (0, 6), (-6, 0), (6, 0), (-4, -4), (4, -4),
                   (-4, 4), (4, 4)]:
        P(g, ex + ox, ey + oy, (255, 180, 80))
    R(g, ex - 2, ey - 2, 4, 4, (255, 230, 150))
    smoke(g, 208, 8, 4)
    smoke(g, 218, 3, 5)
    # chip top-left
    CHIP(g, 24, 3, "CLAIM VS DENIAL", RED)
    return im


def scene_hk():
    """Hong Kong at dusk: BIG Bank of China tower, a ferry on the harbour,
    the ballot box. Slot 192x54."""
    im, g = cv(192, 54, (255, 176, 110))
    # background: dusk bands, checkerboard seam, bigger sun
    for yy in range(16, 28):
        for xx in range(192):
            if (xx + yy) % 2 == 0:
                P(g, xx, yy, (74, 52, 104))
    R(g, 0, 28, 192, 8, (74, 52, 104))
    R(g, 0, 38, 192, 16, (46, 64, 96))
    R(g, 176, 4, 10, 10, (255, 214, 140))
    # midground: flanking towers (shorter, dark, lit windows)
    for fx, fh, fw in [(0, 18, 20), (22, 22, 18), (132, 20, 18),
                       (152, 16, 20), (174, 22, 18)]:
        R(g, fx, 38 - fh, fw, fh, (42, 36, 56))
    for wx, wy in [(10, 24), (28, 20), (138, 26), (158, 26), (180, 22),
                   (36, 30), (136, 30), (162, 30), (184, 28), (6, 28),
                   (26, 26), (142, 22), (170, 26)]:
        P(g, wx, wy, (255, 214, 140))
    # Bank of China tower, BIG and central: triangular X-brace structure
    PG(g, [(64, 38), (96, 4), (128, 38)], (42, 36, 56))
    LN(g, [(70, 32), (122, 12)], (255, 214, 140), w=1)
    LN(g, [(122, 32), (70, 12)], (255, 214, 140), w=1)
    LN(g, [(78, 24), (114, 10)], (255, 214, 140), w=1)
    LN(g, [(114, 24), (78, 10)], (255, 214, 140), w=1)
    R(g, 95, 4, 2, 34, (255, 214, 140))
    # foreground: a ferry crossing the harbour, with a wake + glints
    PG(g, [(20, 44), (46, 44), (42, 50), (24, 50)], (30, 30, 34))
    R(g, 28, 40, 12, 4, (245, 242, 235))
    P(g, 30, 41, (255, 214, 140))
    P(g, 36, 41, (255, 214, 140))
    for wx in (12, 6):
        R(g, wx, 47, 4, 1, (220, 230, 240))
    for wx in (68, 116, 164):
        R(g, wx, 50, 15, 1, (255, 214, 140))
    # ballot box, BIG front right, with a big red check above it
    R(g, 140, 32, 34, 18, (245, 242, 235), o=(120, 110, 95))
    R(g, 147, 34, 20, 2, INK)
    LN(g, [(146, 24), (156, 34)], RED, w=2)
    LN(g, [(156, 34), (174, 10)], RED, w=2)
    # turnout chip
    CHIP(g, 24, 3, "98.79%", DARK)
    return im


def scene_cricket():
    """Wellington: stands, a BIG pitch, stumps, a batsman and a bowler,
    the ball. Slot 192x54."""
    im, g = cv(192, 54, (58, 122, 66))
    EL(g, -20, -30, 212, 84, None, o=(230, 235, 220))
    # background: stands with a crowd
    R(g, 0, 0, 192, 8, (40, 50, 44))
    for cx in range(4, 192, 7):
        for cy in (2, 5):
            if (cx * 3 + cy * 7) % 5 == 0:
                P(g, cx, cy, (240, 240, 230))
            elif (cx + cy) % 3 == 0:
                P(g, cx, cy, (255, 214, 140))
    # midground: pitch strip, BIG and horizontal
    R(g, 16, 14, 160, 28, (196, 172, 120))
    R(g, 16, 14, 1, 28, (245, 242, 235))
    R(g, 176, 14, 1, 28, (245, 242, 235))
    R(g, 16, 26, 160, 1, (245, 242, 235))
    # stumps + bails, BIG at the left end
    for dx in (0, 5, 10):
        R(g, 28 + dx, 16, 3, 18, (240, 210, 90))
    R(g, 28, 14, 13, 2, (240, 210, 90))
    # batsman, standing at the stumps: helmet, pads, bat held diagonal
    EL(g, 96, 18, 104, 26, (198, 164, 132))
    R(g, 95, 17, 10, 4, (30, 30, 34))
    R(g, 94, 26, 12, 14, (245, 242, 235))
    R(g, 95, 40, 4, 3, (30, 30, 34))
    R(g, 103, 40, 4, 3, (30, 30, 34))
    PG(g, [(84, 40), (92, 38), (118, 10), (110, 8)], (150, 105, 60))
    R(g, 108, 4, 3, 8, (150, 105, 60))
    # bowler, mid-delivery at the far end
    EL(g, 158, 12, 164, 18, (172, 128, 96))
    R(g, 157, 18, 8, 14, (40, 60, 40))
    LN(g, [(164, 20), (172, 10)], (172, 128, 96), w=2)
    R(g, 158, 32, 3, 6, (40, 60, 40))
    R(g, 162, 32, 3, 6, (40, 60, 40))
    # foreground: the ball, BIG red, with a seam
    EL(g, 140, 32, 152, 44, (178, 34, 34), o=WHITE)
    P(g, 146, 32, WHITE)
    P(g, 146, 44, WHITE)
    R(g, 142, 37, 8, 1, (255, 255, 255))
    # scoreboard chip top right
    CHIP(g, 192 - 6 - (TXT_W("720/9", F5) + 8), 4, "720/9", DARK)
    TXT(g, 6, 44, "RECORD TOTAL", F7, (235, 235, 225))
    return im


def scene_f1():
    """Las Vegas at night: hotels, the Stratosphere, a BIG open-wheel car
    and a rival behind it, the chequered flag. Slot 192x54."""
    im, g = cv(192, 54, (12, 18, 40))
    # background: stars + city band
    for sx, sy in [(10, 4), (26, 8), (52, 3), (90, 6), (150, 4), (180, 8)]:
        P(g, sx, sy, (220, 225, 235))
    R(g, 0, 20, 192, 16, (30, 26, 52))
    # Stratosphere needle (clear of the chip, right of it)
    PG(g, [(124, 38), (129, 4), (134, 38)], (70, 64, 100))
    R(g, 122, 2, 16, 4, (255, 190, 90))
    # hotel blocks with lit windows
    for fx, fh, fw in [(34, 16, 24), (64, 12, 22), (140, 14, 24),
                       (168, 18, 24)]:
        R(g, fx, 38 - fh, fw, fh, (36, 30, 60))
        for wy in range(2):
            for wx in range(3):
                P(g, fx + 4 + wx * 8, 38 - fh + 4 + wy * 6, (255, 200, 110))
    # midground: the track
    R(g, 0, 38, 192, 16, (52, 52, 58))
    for tx in range(12):
        R(g, tx * 16, 46, 8, 1, (240, 240, 235))
    # a rival car behind, smaller and darker, at the left
    R(g, 14, 44, 24, 4, (90, 90, 100))
    EL(g, 16, 46, 22, 52, (15, 15, 18), o=(120, 120, 115))
    EL(g, 32, 46, 38, 52, (15, 15, 18), o=(120, 120, 115))
    # foreground: BIG open-wheel race car (centre), side profile
    R(g, 50, 24, 4, 16, (120, 20, 20))
    R(g, 44, 22, 16, 4, (178, 34, 34))
    R(g, 44, 30, 16, 3, (178, 34, 34))
    R(g, 130, 42, 14, 3, (178, 34, 34))
    PG(g, [(56, 38), (128, 38), (132, 44), (56, 44)], (178, 34, 34))
    PG(g, [(84, 38), (92, 28), (96, 38)], (178, 34, 34))
    R(g, 72, 34, 22, 6, (150, 28, 28))
    EL(g, 88, 28, 94, 34, (245, 245, 240))
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
    CHIP(g, 24, 3, "35 LEAD CHANGES", DARK)
    return im


def scene_tennis():
    """Turin: stands, a BIG net, a player striking the ball, the trophy.
    Slot 192x54."""
    im, g = cv(192, 54, (47, 111, 178))
    # background: stands at the top
    R(g, 0, 0, 192, 4, (28, 44, 72))
    for cx in range(4, 192, 9):
        if cx % 3 == 0:
            P(g, cx, 2, (240, 240, 230))
    # court lines
    R(g, 8, 6, 176, 42, None, o=(240, 240, 235))
    R(g, 8, 26, 176, 2, (240, 240, 235))
    R(g, 62, 6, 2, 42, (240, 240, 235))
    R(g, 130, 6, 2, 42, (240, 240, 235))
    # midground: net, BIG across the middle: white top tape + mesh
    R(g, 8, 20, 176, 10, (235, 235, 228))
    R(g, 8, 20, 176, 3, (255, 255, 255))
    for nx in range(16, 176, 8):
        R(g, nx, 23, 1, 7, (120, 120, 115))
    R(g, 6, 18, 4, 14, (30, 30, 34))
    R(g, 182, 18, 4, 14, (30, 30, 34))
    # foreground: the player, left, racket raised to the ball
    EL(g, 28, 16, 36, 24, (198, 164, 132))
    R(g, 27, 15, 10, 4, (30, 30, 34))
    R(g, 26, 24, 12, 14, (40, 60, 90))
    R(g, 27, 38, 4, 4, (30, 30, 34))
    R(g, 33, 38, 4, 4, (30, 30, 34))
    LN(g, [(38, 22), (50, 10)], (120, 90, 60), w=2)
    EL(g, 48, 2, 60, 14, None, o=(240, 240, 235))
    # the ball, BIG lime, at the racket
    EL(g, 60, 8, 78, 26, (204, 255, 0), o=WHITE)
    P(g, 69, 8, WHITE)
    P(g, 69, 26, WHITE)
    R(g, 64, 16, 10, 1, (255, 255, 255))
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
    """Anfield: stands, a BIG goal with a keeper, a striker and the ball.
    Slot 192x54."""
    im, g = cv(192, 54, (46, 125, 62))
    # background: stands at the top
    R(g, 0, 0, 192, 4, (30, 50, 34))
    for cx in range(4, 192, 9):
        if cx % 3 == 0:
            P(g, cx, 2, (240, 240, 230))
    # pitch lines
    R(g, 6, 4, 180, 46, None, o=(240, 240, 235))
    R(g, 96, 4, 2, 46, (240, 240, 235))
    EL(g, 82, 14, 112, 42, None, o=(240, 240, 235))
    R(g, 6, 16, 44, 22, None, o=(240, 240, 235))
    R(g, 142, 16, 44, 22, None, o=(240, 240, 235))
    # midground: goal, BIG with a clear net (right)
    gx0, gy0 = 138, 10
    R(g, gx0, gy0, 48, 32, None, o=WHITE)
    for i in range(1, 6):
        R(g, gx0 + i * 8, gy0, 2, 32, (220, 220, 215))
        R(g, gx0, gy0 + i * 6, 48, 2, (220, 220, 215))
    # goalkeeper, standing in the goal with arms out
    EL(g, 158, 20, 164, 26, (198, 164, 132))
    R(g, 156, 26, 12, 12, (220, 200, 60))
    R(g, 150, 28, 6, 3, (198, 164, 132))
    R(g, 168, 28, 6, 3, (198, 164, 132))
    R(g, 158, 38, 4, 4, (30, 30, 34))
    R(g, 164, 38, 4, 4, (30, 30, 34))
    # foreground: the striker's leg + boot, and the ball, BIG
    R(g, 38, 34, 10, 12, (30, 30, 34))
    R(g, 46, 42, 14, 4, (30, 30, 34))
    R(g, 50, 40, 18, 4, (30, 30, 34))
    R(g, 66, 34, 10, 6, (30, 30, 34))
    EL(g, 70, 26, 88, 44, (250, 250, 245), o=(30, 30, 30))
    R(g, 77, 32, 6, 6, (30, 30, 30))
    # scoreboard chip
    CHIP(g, 24, 3, "4–0", DARK)
    return im


def scene_manipur():
    """Manipur: a deeper sea, a warmer NE-India map, a BIG Imphal ring,
    hospital crosses and a clinic. Slot 192x54."""
    im, g = cv(192, 54, (150, 180, 205))
    # midground: NE India, blocky east region + narrow western corridor
    PG(g, [(70, 8), (150, 6), (186, 14), (188, 30), (170, 46), (120, 50),
           (80, 46), (70, 32), (60, 30), (30, 26), (8, 24), (8, 32),
           (30, 34), (60, 34), (70, 36)], (200, 175, 130))
    # darker hill patch for texture
    PG(g, [(100, 16), (130, 14), (144, 24), (130, 32), (104, 30)],
       (180, 155, 110))
    # a clinic on the map
    R(g, 80, 38, 12, 8, (245, 242, 235), o=(120, 110, 95))
    R(g, 84, 40, 4, 4, RED)
    # foreground: Imphal ring + dot, BIG
    EL(g, 118, 20, 140, 42, None, o=RED)
    R(g, 127, 29, 4, 4, RED)
    # hospital crosses, BIG
    for cx, cy in [(88, 16), (158, 40), (168, 14)]:
        R(g, cx - 1, cy - 6, 3, 12, RED)
        R(g, cx - 6, cy - 1, 12, 3, RED)
    # toll chip
    CHIP(g, 24, 3, "17 DEAD", RED)
    return im


def scene_cikande():
    """Cikande: a smoke column, a BIG factory, BIG flames, a fire truck.
    Slot 192x54."""
    im, g = cv(192, 54, (200, 195, 185))
    # background: dusk grey top, pale bottom, checkerboard seam
    R(g, 0, 0, 192, 24, (140, 150, 165))
    for xx in range(192):
        if xx % 2 == 0:
            P(g, xx, 24, (200, 195, 185))
    # smoke column, BIG and rising above the flames
    smoke(g, 110, 10, 10)
    smoke(g, 124, 6, 12)
    smoke(g, 138, 12, 8)
    smoke(g, 160, 8, 10)
    smoke(g, 174, 12, 8)
    smoke(g, 96, 14, 7)
    # midground: factory body + sawtooth roof + chimney (far right)
    R(g, 8, 26, 184, 22, (138, 141, 144))
    for i in range(5):
        sx = 8 + i * 32
        PG(g, [(sx, 26), (sx + 16, 16), (sx + 32, 26)], (110, 113, 116))
    R(g, 176, 10, 8, 38, (100, 102, 105))
    # windows: 2 rows x 6 cols, all lit
    for wy in range(2):
        for wx in range(6):
            R(g, 16 + wx * 28, 30 + wy * 12, 4, 4, (255, 205, 110))
    # foreground: flames, BIG and clear of the chip (right side)
    flame(g, 102, 26, 10, 18)
    flame(g, 132, 26, 12, 20)
    flame(g, 160, 26, 10, 16)
    # fire truck, front left, ladder raised toward the flames
    R(g, 10, 46, 28, 6, (178, 34, 34))
    R(g, 38, 47, 10, 5, (178, 34, 34))
    EL(g, 14, 50, 20, 54, (20, 20, 24))
    EL(g, 34, 50, 40, 54, (20, 20, 24))
    LN(g, [(20, 46), (38, 30)], (200, 200, 195), w=2)
    P(g, 12, 47, (255, 220, 90))
    P(g, 40, 48, (255, 220, 90))
    # casualty chip top-left (two lines, F5)
    CHIP2(g, 24, 3, "3 DEAD", "36 MISSING", RED)
    return im


def scene_sparta():
    """Sparta II: a smoke column, the burning ship, a tug and a lifeboat,
    big waves. Slot 192x54."""
    im, g = cv(192, 54, (52, 96, 130))
    R(g, 0, 0, 192, 26, (120, 165, 195))
    for xx in range(192):
        if xx % 2 == 0:
            P(g, xx, 26, (52, 96, 130))
    # background: a BIG smoke column at the stern
    smoke(g, 24, 12, 8)
    smoke(g, 30, 4, 9)
    smoke(g, 18, 4, 7)
    smoke(g, 36, 10, 6)
    # foreground: BIG flames at the stern
    flame(g, 24, 34, 12, 22)
    flame(g, 34, 34, 8, 14)
    # waves, bigger white caps
    for wy in (30, 36, 44, 50):
        for wx in (10, 58, 106, 154):
            P(g, wx - 4, wy, (220, 235, 245))
            P(g, wx - 2, wy + 2, (220, 235, 245))
            P(g, wx, wy + 2, (220, 235, 245))
            P(g, wx + 2, wy + 2, (220, 235, 245))
            P(g, wx + 4, wy, (220, 235, 245))
    # midground: hull + name + containers + bridge
    PG(g, [(16, 34), (176, 34), (166, 44), (26, 44)], (40, 44, 52))
    TXT(g, 62, 36, "SPARTA II", F5, (240, 240, 235))
    for i, col in enumerate([(178, 84, 44), (52, 96, 150), (90, 140, 70),
                             (178, 84, 44)]):
        R(g, 30 + i * 32, 20, 26, 12, col, o=(30, 30, 34))
    R(g, 158, 8, 14, 24, (235, 235, 230))
    R(g, 162, 2, 6, 6, (178, 34, 34))
    # a tug alongside, bottom right, and the lifeboat
    PG(g, [(150, 46), (172, 46), (170, 51), (152, 51)], (220, 140, 40))
    R(g, 158, 42, 8, 4, (245, 242, 235))
    for wx in (144, 138):
        R(g, wx, 48, 4, 1, (240, 244, 248))
    PG(g, [(110, 46), (128, 46), (126, 50), (112, 50)], (255, 140, 40))
    # chip
    CHIP(g, 30, 4, "16 SAFE", (46, 139, 87))
    return im


def scene_tehran():
    """Tehran at dusk: a BIG Milad Tower, a skyline with lit windows and
    one blacked-out block, a big lightbulb. Slot 192x54."""
    im, g = cv(192, 54, (255, 150, 80))
    # background: dusk bands, purple top, orange bottom, checkerboard seam
    R(g, 0, 0, 192, 24, (88, 66, 122))
    for xx in range(192):
        if xx % 2 == 0:
            P(g, xx, 24, (255, 150, 80))
    # midground: Milad Tower, BIG centre-right
    PG(g, [(112, 48), (126, 10), (138, 10), (152, 48)], (52, 44, 66))
    EL(g, 108, 8, 156, 26, (72, 60, 88))
    R(g, 108, 14, 48, 3, (255, 190, 90))
    R(g, 130, 2, 4, 6, (255, 190, 90))
    # foreground: skyline flanking the tower, many lit windows
    for fx, fh, fw in [(0, 16, 24), (24, 22, 20), (46, 18, 24), (72, 26, 24),
                       (160, 24, 24), (182, 18, 10)]:
        R(g, fx, 48 - fh, fw, fh, (48, 40, 60))
    for wx, wy in [(6, 36), (12, 40), (28, 32), (34, 38), (50, 34), (56, 40),
                   (76, 30), (80, 36), (164, 30), (170, 36), (184, 34),
                   (186, 40), (10, 42), (30, 44), (168, 42)]:
        P(g, wx, wy, (255, 210, 110))
    # one blacked-out block next to the tower (the rationing)
    R(g, 96, 30, 14, 18, (20, 18, 24))
    # lightbulb, BIG top right (rays kept on-canvas)
    bx, by = 172, 16
    EL(g, bx - 8, by - 10, bx + 8, by + 8, None, o=(255, 235, 180))
    R(g, bx - 2, by + 8, 4, 2, (255, 235, 180))
    R(g, bx - 2, by + 12, 4, 1, (255, 235, 180))
    P(g, bx - 8, by - 14, (255, 235, 180))
    P(g, bx + 8, by - 14, (255, 235, 180))
    P(g, bx, by - 16, (255, 235, 180))
    # chip top-left
    CHIP(g, 24, 3, "UP TO 2 HRS", DARK)
    return im


def scene_gaza():
    """Gaza coast: a deeper sea, the strip outline, rubble, a two-truck
    aid convoy. Slot 192x54."""
    im, g = cv(192, 54, (224, 211, 178))
    # background: sea left, coastline diagonal
    PG(g, [(0, 0), (80, 0), (58, 54), (0, 54)], (120, 160, 200))
    LN(g, [(80, 0), (58, 54)], (240, 240, 235), w=1)
    for wx, wy in [(20, 10), (30, 20), (40, 30), (48, 40)]:
        R(g, wx, wy, 4, 1, (240, 244, 248))
    # midground: Gaza strip outline (thicker, two passes) + rubble, clear
    # of the trucks, inside the strip
    strip = [(126, 4), (156, 4), (146, 50), (118, 50), (126, 4)]
    LN(g, strip, RED, w=2)
    TXT(g, 160, 8, "GAZA", F5, INK_SOFT)
    PG(g, [(130, 44), (138, 32), (146, 44)], (140, 138, 132))
    R(g, 134, 44, 10, 4, (120, 118, 112))
    LN(g, [(130, 44), (146, 36)], (100, 98, 92), w=2)
    # foreground: road band under the trucks
    R(g, 0, 40, 192, 10, (120, 118, 112))
    # the second truck, smaller, behind on the left
    R(g, 20, 28, 30, 10, (220, 220, 215), o=(120, 120, 115))
    R(g, 50, 31, 9, 7, (200, 205, 210), o=(120, 120, 115))
    R(g, 24, 38, 5, 6, (20, 20, 24))
    R(g, 40, 38, 5, 6, (20, 20, 24))
    R(g, 54, 38, 5, 6, (20, 20, 24))
    # the lead aid truck, BIG
    tx, ty = 66, 38
    R(g, tx, ty - 14, 44, 16, (245, 245, 240), o=(120, 120, 115))
    R(g, tx + 44, ty - 10, 14, 12, (200, 205, 210), o=(120, 120, 115))
    R(g, tx + 16, ty - 12, 8, 8, RED)
    R(g, tx + 19, ty - 15, 2, 14, RED)
    R(g, tx + 6, ty + 2, 6, 8, (20, 20, 24))
    R(g, tx + 30, ty + 2, 6, 8, (20, 20, 24))
    R(g, tx + 48, ty + 2, 6, 8, (20, 20, 24))
    # chip
    CHIP(g, 24, 3, "3 KILLED", RED)
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
        assert im.size == (w, h), (name, im.size)
        im.save(os.path.join(out, name))
        print(name, im.size)


if __name__ == "__main__":
    main()
