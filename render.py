#!/usr/bin/env python3
"""Sunday 22 November 2026 — broadsheet front page, drawn entirely in code.
Design: classic broadsheet (cream paper, huge Playfair masthead, one big lead
scene, 12 numbered cards each with its own drawn scene, world map + index,
stat strip, DATE CHECK, footer). All text is real text; all art is Pillow.
Deterministic: no randomness, no timestamps, no network."""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 229)
INK = (20, 20, 31)
INK_SOFT = (60, 60, 72)
GREY = (110, 110, 118)
RED = (179, 39, 30)
RED_DK = (140, 28, 22)
SEA = (201, 220, 232)
LAND = (230, 217, 184)
LAND_LINE = (196, 178, 138)
GOLD = (201, 168, 106)

REGIONS = [
    ("ASIA", 8, (123, 75, 168)),
    ("MIDDLE EAST", 9, (217, 123, 41)),
    ("EUROPE", 14, (43, 94, 167)),
    ("AFRICA", 4, (46, 139, 87)),
    ("AMERICAS", 4, (192, 57, 43)),
    ("OCEANIA", 2, (26, 158, 143)),
    ("GLOBAL", 1, (107, 107, 107)),
]
RCOL = {name: col for name, _, col in REGIONS}

# ---------------------------------------------------------------- fonts
_CACHE = {}


def F(name, size):
    key = (name, size)
    if key not in _CACHE:
        _CACHE[key] = ImageFont.truetype(os.path.join(FONTS, name), size)
    return _CACHE[key]


def PF(size, weight="Bold"):
    return F("Playfair-%s.ttf" % weight, size)


def PT(size, style="Regular"):
    return F("PTSerif-%s.ttf" % style, size)


def IN(size, weight="Bold"):
    return F("Inter-%s.ttf" % weight, size)


# ---------------------------------------------------------------- text tools
def text_w(d, s, font):
    return d.textlength(s, font=font)


def tracked_w(d, s, font, tr=1.0):
    return sum(d.textlength(ch, font=font) + tr for ch in s) - tr


def draw_tracked(d, x, y, s, font, fill, tr=1.0):
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=font, fill=fill)
        cx += d.textlength(ch, font=font) + tr
    return cx - x


def draw_tracked_c(d, cx, y, s, font, fill, tr=1.0):
    w = tracked_w(d, s, font, tr)
    return draw_tracked(d, cx - w / 2, y, s, font, fill, tr)


def wrap(d, s, font, maxw):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(d, s, font, maxw, max_lines, size=None):
    """Wrap s to at most max_lines; truncate the last line with an ellipsis."""
    lines = wrap(d, s, font, maxw)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    while lines and d.textlength(lines[-1] + " ...", font=font) > maxw:
        lines[-1] = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1][:-1]
    lines[-1] = lines[-1] + " ..."
    return lines


def center_text(d, cx, y, s, font, fill):
    w = d.textlength(s, font=font)
    d.text((cx - w / 2, y), s, font=font, fill=fill)
    return w


def draw_chip(d, x, y, s, fill):
    """One consistent chip: 18px tall, PT Serif Bold 12, text centred by bbox.

    Every numeral chip on the page uses this — same height, same font, same
    baseline — so no chip's number sits high, low, big or small vs the others.
    Returns the chip width."""
    fw = PT(12, "Bold")
    cw = d.textlength(s, font=fw) + 12
    rrect(d, [x, y, x + cw, y + 18], 3, fill=fill)
    bb = d.textbbox((0, 0), s, font=fw)
    th = bb[3] - bb[1]
    d.text((x + 6, y + (18 - th) // 2 - bb[1]), s, font=fw, fill=(255, 255, 255))
    return cw


# ---------------------------------------------------------------- pixel art
# v5: every drawing is made DIRECTLY at final slot resolution, 1x1 blocks,
# no downscale — each placed pixel survives to the final image. The 12 card
# scenes live in scenes.py (drawn at exact slot size); the lead is painted
# here at 640x206 with its bitmap text at 2x (each glyph pixel a 2x2 block).
# Scene text uses bitmap glyphs defined here (my own letterforms); page
# typography stays smooth.
FONT35 = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "101", "101", "101"),
    "N": ("101", "111", "111", "101", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    " ": ("000", "000", "000", "000", "000"),
    ".": ("000", "000", "000", "000", "010"),
    "%": ("101", "001", "010", "100", "101"),
    "/": ("001", "001", "010", "100", "100"),
    "–": ("000", "000", "111", "000", "000"),
    "·": ("000", "000", "010", "000", "000"),
}
FONT57 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10001", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "10001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def px_text(g, x, y, s, font, color):
    """Draw bitmap text on a grid canvas. Returns the width in grid px."""
    cx = x
    for ch in s:
        gl = font.get(ch, font[" "])
        for ry, row in enumerate(gl):
            for rx, bit in enumerate(row):
                if bit == "1":
                    g.rectangle([cx + rx, y + ry, cx + rx, y + ry], fill=color)
        cx += len(gl[0]) + 1
    return cx - x - 1


def px_text_w(s, font):
    return sum(len(font.get(ch, font[" "])[0]) + 1 for ch in s) - 1


def px_text_c(g, cx, y, s, font, color):
    return px_text(g, cx - px_text_w(s, font) // 2, y, s, font, color)


def px_chip(g, x, y, s, fill):
    """Pixel chip on the grid canvas: 9 grid px tall = 18 final px, the same
    height as the old smooth chips, so every chip on the page still matches.
    Text is FONT35, centred by pixel bbox."""
    tw = px_text_w(s, FONT35)
    g.rounded_rectangle([x, y, x + tw + 6, y + 8], radius=2, fill=fill)
    px_text(g, x + 3, y + 2, s, FONT35, (255, 255, 255))
    return tw + 7


def px_chip2(g, x, y, l1, l2, fill):
    """Two-line pixel chip (16 grid px tall) for a string too long to fit one
    pixel line on a 96-wide card; the line break replaces the separator.
    FONT35 glyphs are 5 rows tall, so the lines sit at y+2 and y+9 with a
    2px gap — a 1px gap read as one jumbled line."""
    w = max(px_text_w(l1, FONT35), px_text_w(l2, FONT35)) + 7
    g.rounded_rectangle([x, y, x + w - 1, y + 15], radius=2, fill=fill)
    px_text(g, x + 3, y + 2, l1, FONT35, (255, 255, 255))
    px_text(g, x + 3, y + 9, l2, FONT35, (255, 255, 255))
    return w


def px2_text(g, x, y, s, font, color):
    """Bitmap text at 2x: every glyph pixel is a 2x2 block placed directly
    at final resolution (no downscale). Returns the width in final px."""
    cx = x
    for ch in s:
        gl = font.get(ch, font[" "])
        for ry, row in enumerate(gl):
            for rx, bit in enumerate(row):
                if bit == "1":
                    g.rectangle([cx + rx * 2, y + ry * 2,
                                 cx + rx * 2 + 1, y + ry * 2 + 1], fill=color)
        cx += (len(gl[0]) + 1) * 2
    return cx - x - 2


def px2_text_w(s, font):
    return sum((len(font.get(ch, font[" "])[0]) + 1) * 2 for ch in s) - 2


def px2_text_c(g, cx, y, s, font, color):
    return px2_text(g, cx - px2_text_w(s, font) // 2, y, s, font, color)


def px2_chip(g, x, y, s, fill):
    """Pixel chip at final resolution: 18px tall (the same height as the
    old grid chips), FONT35 text at 2x, centred by pixel bbox."""
    tw = px2_text_w(s, FONT35)
    g.rounded_rectangle([x, y, x + tw + 7, y + 17], radius=2, fill=fill)
    px2_text(g, x + 4, y + 4, s, FONT35, (255, 255, 255))
    return tw + 8


def px_canvas(w, h, bg):
    im = Image.new("RGB", (w, h), bg)
    return im, ImageDraw.Draw(im)


def px_paste(d, box, im):
    """Upscale a grid canvas 2x with NEAREST and paste it into the page.
    Odd dimensions crop 1px (grid = ceil(size / 2))."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    up = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    if up.size != (w, h):
        up = up.crop((0, 0, w, h))
    d._image.paste(up, (int(x0), int(y0)))


def px_glow(g, x0, y0, x1, y1, color):
    """Sparse deterministic glow dots (~1 in 11 pixels)."""
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            if (xx * 5 + yy * 11) % 11 == 0:
                g.point((xx, yy), fill=color)


def px2_glow(g, x0, y0, x1, y1, color):
    """Sparse deterministic glow at final resolution: 2x2 blocks on a 2px
    grid (~1 in 17 positions)."""
    for yy in range(y0, y1, 2):
        for xx in range(x0, x1, 2):
            if (xx * 7 + yy * 13) % 17 == 0:
                g.rectangle([xx, yy, xx + 1, yy + 1], fill=color)


def px_map(gw, gh, lon0, lon1, lat0, lat1, sea, land):
    """Region map rasterised straight onto a grid-size canvas."""
    im = Image.new("RGB", (gw, gh), sea)
    dd = ImageDraw.Draw(im)
    for ring in POLYS:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        if max(xs) < lon0 or min(xs) > lon1 or max(ys) < lat0 or min(ys) > lat1:
            continue
        pts = []
        for lon, lat in ring:
            pts.append(((lon - lon0) / (lon1 - lon0) * gw,
                        (lat1 - lat) / (lat1 - lat0) * gh))
        if len(pts) >= 3:
            dd.polygon(pts, fill=land)
    return im


def pixel_map(w, h, block, lon0, lon1, lat0, lat1, sea, land):
    """World map rasterised into pixel blocks: drawn on a
    (w/block)x(h/block) grid (antimeridian-split, like draw_land), upscaled
    block x NEAREST and cropped to (w, h). Every placed block survives;
    no smooth vector anywhere."""
    gw = (w + block - 1) // block
    gh = (h + block - 1) // block
    im = Image.new("RGB", (gw, gh), sea)
    dd = ImageDraw.Draw(im)
    for ring in POLYS:
        pts = []
        prev_lon = None
        for lon, lat in ring:
            if prev_lon is not None and abs(lon - prev_lon) > 180:
                if len(pts) >= 3:
                    dd.polygon(pts, fill=land)
                pts = []
            pts.append(((lon - lon0) / (lon1 - lon0) * gw,
                        (lat1 - lat) / (lat1 - lat0) * gh))
            prev_lon = lon
        if len(pts) >= 3:
            dd.polygon(pts, fill=land)
    up = im.resize((gw * block, gh * block), Image.NEAREST)
    if up.size != (w, h):
        up = up.crop((0, 0, w, h))
    return up


def px_pin(d, cx, cy, size, color, num, big):
    """A pixel pin: a square block with a 1px outline and the number in a
    bitmap font (FONT57 5x7 for big pins, FONT35 3x5 for small)."""
    half = size // 2
    d.rectangle([cx - half, cy - half, cx + half, cy + half],
                fill=color, outline=INK)
    font = FONT57 if big else FONT35
    tw = px_text_w(str(num), font)
    th = 7 if big else 5
    px_text(d, cx - tw // 2, cy - th // 2, str(num), font, (255, 255, 255))


def px_person(g, cx, top, skin, suit, hair, bald=False):
    """Seated delegate on the grid: head + shoulders."""
    g.rectangle([cx - 2, top, cx + 2, top + 3], fill=skin)
    if not bald:
        g.rectangle([cx - 2, top, cx + 2, top + 1], fill=hair)
    g.rectangle([cx - 4, top + 4, cx + 4, top + 7], fill=suit)


def px2_person(g, cx, top, skin, suit, hair, bald=False):
    """Seated delegate at final resolution: head + shoulders, the same
    figure as px_person, each grid pixel a 2x2 block."""
    g.rectangle([cx - 4, top, cx + 5, top + 7], fill=skin)
    if not bald:
        g.rectangle([cx - 4, top, cx + 5, top + 3], fill=hair)
    g.rectangle([cx - 8, top + 8, cx + 9, top + 15], fill=suit)


# Region legend icons: 9x9 pixel glyphs, one per region, drawn white on the
# region bar. (My own glyphs.)
REGION_ICONS = {
    "ASIA": (
        "111111111",
        "000000000",
        "011111110",
        "001000100",
        "001000100",
        "001000100",
        "001000100",
        "001000100",
        "001000100",
    ),
    "MIDDLE EAST": (
        "000010000",
        "000010000",
        "000010000",
        "000111000",
        "001111100",
        "011111110",
        "011111110",
        "000000000",
        "111111111",
    ),
    "EUROPE": (
        "011111110",
        "000111000",
        "000111000",
        "000111000",
        "000111000",
        "000111000",
        "000111000",
        "000111000",
        "011111110",
    ),
    "AFRICA": (
        "000010000",
        "000111000",
        "001111100",
        "001111100",
        "011111110",
        "011111110",
        "111111111",
        "111111111",
        "000000000",
    ),
    "AMERICAS": (
        "000010000",
        "000111000",
        "111111111",
        "011111110",
        "001111100",
        "010111010",
        "110000011",
        "000000000",
        "000000000",
    ),
    "OCEANIA": (
        "000000000",
        "001100110",
        "011011011",
        "110110110",
        "110110110",
        "011001100",
        "000000000",
        "000000000",
        "000000000",
    ),
    "GLOBAL": (
        "001111100",
        "011111110",
        "110101011",
        "101110101",
        "101011101",
        "110101011",
        "011111110",
        "001111100",
        "000000000",
    ),
}


def draw_px_icon(d, x, y, rows, color):
    """Draw a 9x9 pixel icon (1x1 blocks) at (x, y)."""
    for ry, row in enumerate(rows):
        for rx, bit in enumerate(row):
            if bit == "1":
                d.point((x + rx, y + ry), fill=color)


def vgrad(w, h, top, bottom):
    img = Image.new("RGB", (1, h))
    px = img.load()
    for i in range(h):
        t = i / max(1, h - 1)
        px[0, i] = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
    return img.resize((w, h))


def glow(img, box, color, alpha=70):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.ellipse(box, fill=color + (alpha,))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))


def rrect(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)


# ---------------------------------------------------------------- map data
with open(os.path.join(HERE, "map.json")) as fh:
    POLYS = json.load(fh)["polys"]


def proj(lon, lat, box):
    x0, y0, x1, y1 = box
    x = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    y = y0 + (90.0 - lat) / 180.0 * (y1 - y0)
    return x, y


def draw_land(d, box, fill=LAND, outline=None):
    for ring in POLYS:
        pts = []
        prev_lon = None
        for lon, lat in ring:
            if prev_lon is not None and abs(lon - prev_lon) > 180:
                if len(pts) >= 3:
                    d.polygon(pts, fill=fill, outline=outline)
                pts = []
            pts.append(proj(lon, lat, box))
            prev_lon = lon
        if len(pts) >= 3:
            d.polygon(pts, fill=fill, outline=outline)


def crop_map(box, lon0, lon1, lat0, lat1, sea, land):
    """A small map of one region, drawn on its own image (correctly clipped)."""
    w, h = int(box[2] - box[0]), int(box[3] - box[1])
    im = Image.new("RGB", (w, h), sea)
    dd = ImageDraw.Draw(im)
    for ring in POLYS:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        if max(xs) < lon0 or min(xs) > lon1 or max(ys) < lat0 or min(ys) > lat1:
            continue
        pts = []
        for lon, lat in ring:
            x = (lon - lon0) / (lon1 - lon0) * w
            y = (lat1 - lat) / (lat1 - lat0) * h
            pts.append((x, y))
        if len(pts) >= 3:
            dd.polygon(pts, fill=land)
    return im


def place_pins(items, box):
    """items: (num, lon, lat, color, big). Spiral-nudge so pins never overlap."""
    placed, out = [], []
    for num, lon, lat, color, big in items:
        x, y = proj(lon, lat, box)
        r = 7 if big else 5
        done = False
        for ox, oy in [(0, 0), (10, 0), (-10, 0), (0, 10), (0, -10),
                       (10, 10), (-10, -10), (10, -10), (-10, 10),
                       (16, 0), (-16, 0), (0, 16), (0, -16), (16, 16), (-16, -16)]:
            nx, ny = x + ox, y + oy
            if all((nx - px) ** 2 + (ny - py) ** 2 >= (r + pr + 1) ** 2
                   for px, py, pr in placed):
                placed.append((nx, ny, r))
                out.append((num, nx, ny, color, big))
                done = True
                break
        if not done:
            placed.append((x, y, r))
            out.append((num, x, y, color, big))
    return out


def _scene(d, box, name):
    """Paste a pre-rendered scene PNG into its slot.

    The PNG is drawn by scenes.py DIRECTLY at the slot size (1x1 blocks,
    no downscale), so it is pasted as-is; the resize only fires if a size
    ever drifts."""
    im = Image.open(os.path.join(HERE, "scenes", name)).convert("RGB")
    x0, y0, x1, y1 = box
    w, h = int(x1 - x0), int(y1 - y0)
    if im.size != (w, h):
        im = im.resize((w, h), Image.NEAREST)
    d._image.paste(im, (int(x0), int(y0)))


# ---------------------------------------------------------------- scenes
def _person(d, cx, top, s, skin, suit, hair, bald=False):
    """A seated delegate: head + shoulders, seen from behind the desk."""
    hr = 3.4 * s
    d.ellipse([cx - hr, top, cx + hr, top + 2 * hr], fill=skin)
    if not bald:
        d.pieslice([cx - hr, top - hr * 0.25, cx + hr, top + hr * 0.9],
                   180, 360, fill=hair)
    sw = 7.5 * s
    sh = 7.0 * s
    d.rounded_rectangle([cx - sw, top + 2 * hr - 1, cx + sw,
                         top + 2 * hr + sh], radius=2 * s, fill=suit)


def paint_lead(d, box):
    """COP31 plenary hall, Antalya — pixel art drawn DIRECTLY at 640x206,
    1x1 blocks (v5: no grid canvas, no downscale). Same composition as v4,
    finer grid: thin clock hands, a bigger gavel and globe, more varied
    delegates and desk flags. Bitmap text at 2x (each glyph pixel a 2x2
    block)."""
    x0, y0, x1, y1 = box
    im = Image.new("RGB", (640, 206), (22, 40, 58))
    g = ImageDraw.Draw(im)
    # ceiling band + gold line
    g.rectangle([0, 0, 639, 11], fill=(30, 48, 68))
    g.rectangle([0, 10, 639, 11], fill=(201, 168, 106))
    # side drapes with folds
    for dx0 in (0, 620):
        g.rectangle([dx0, 0, dx0 + 19, 205], fill=(56, 32, 36))
        g.rectangle([dx0 + 6, 0, dx0 + 9, 205], fill=(78, 46, 50))
        g.rectangle([dx0 + 14, 0, dx0 + 17, 205], fill=(78, 46, 50))
    # warm glow behind the screen: sparse gold blocks
    px2_glow(g, 200, 16, 440, 84, (255, 190, 110))
    # chandelier, two tiers, top centre
    cx = 320
    g.rectangle([319, 2, 320, 13], fill=(201, 168, 106))
    g.rectangle([280, 14, 361, 15], fill=(201, 168, 106))
    for dx in (-36, -18, 0, 18, 36):
        g.rectangle([cx + dx - 2, 10, cx + dx + 3, 15], fill=(255, 217, 122))
    g.rectangle([296, 16, 297, 23], fill=(201, 168, 106))
    g.rectangle([342, 16, 343, 23], fill=(201, 168, 106))
    g.rectangle([260, 24, 381, 25], fill=(201, 168, 106))
    for dx in (-56, -38, -20, 0, 20, 38, 56):
        g.rectangle([cx + dx - 2, 20, cx + dx + 3, 25], fill=(255, 217, 122))
        g.rectangle([cx + dx, 26, cx + dx + 1, 31], fill=(255, 225, 150))
        g.point((cx + dx, 32), fill=(255, 225, 150))
    g.rectangle([316, 8, 325, 13], fill=(255, 217, 122))
    # wall clock, top left — thin hands so they read as hands, not a blob.
    # Centred at x=56 so the OVERTIME label clears the left drape.
    ccx, ccy = 56, 28
    g.ellipse([44, 16, 69, 41], fill=(238, 232, 214), outline=(120, 100, 70))
    for tx, ty in [(54, 18), (54, 34), (46, 26), (62, 26)]:
        g.rectangle([tx, ty, tx + 5, ty + 5], fill=(120, 100, 70))
    g.line([(ccx, ccy), (ccx, ccy - 9)], fill=INK, width=2)
    g.line([(ccx, ccy), (ccx + 7, ccy - 3)], fill=INK, width=2)
    g.point((ccx, ccy), fill=INK)
    px2_text_c(g, ccx, 44, "OVERTIME", FONT35, (232, 220, 192))
    # big screen: the pact, no consensus
    g.rectangle([214, 32, 427, 77], fill=(13, 26, 38), outline=(201, 168, 106))
    px2_text_c(g, 320, 38, "ANTALYA PACT", FONT57, (232, 220, 192))
    g.rectangle([230, 56, 411, 57], fill=(120, 100, 70))
    px2_text_c(g, 320, 60, "NO CONSENSUS", FONT57, (224, 82, 68))
    # podium with gold trim; globe on its front, gavel on the front-left
    # (moved off the top: the old gavel overlapped the screen text)
    g.polygon([(268, 114), (276, 82), (364, 82), (372, 114)], fill=(107, 74, 47))
    g.rectangle([262, 78, 379, 83], fill=(84, 58, 36))
    g.rectangle([272, 92, 369, 93], fill=(201, 168, 106))
    gx, gy = 320, 100
    g.ellipse([gx - 13, gy - 13, gx + 13, gy + 13], fill=(127, 176, 216),
              outline=(232, 220, 192))
    g.rectangle([gx - 8, gy - 8, gx - 2, gy - 2], fill=(240, 240, 230))
    g.rectangle([gx + 2, gy + 2, gx + 8, gy + 8], fill=(240, 240, 230))
    # gavel: handle + head + sound block, on the podium front-left
    g.rectangle([272, 97, 296, 100], fill=(201, 168, 106))
    g.rectangle([290, 92, 302, 102], fill=(201, 168, 106))
    g.rectangle([291, 104, 301, 107], fill=(84, 58, 36))
    # delegate rows: desks + figures, jittered and varied
    skins = [(198, 164, 132), (172, 128, 96), (214, 182, 150), (150, 108, 82),
             (226, 196, 164)]
    suits = [(30, 44, 66), (52, 52, 56), (44, 62, 48), (86, 42, 44),
             (38, 38, 44), (66, 54, 40), (70, 60, 90)]
    hairs = [(30, 22, 16), (70, 70, 70), (160, 160, 160), (20, 20, 20)]
    for ri, (dy, n) in enumerate([(116, 7), (144, 8), (176, 9)]):
        g.rectangle([24, dy, 617, dy + 9], fill=(58, 44, 32))
        g.rectangle([24, dy, 617, dy + 1], fill=(120, 96, 66))
        for i in range(n):
            jx = ((i * 13 + ri * 7) % 5 - 2) * 2
            fx = int(24 + (i + 0.5) * 592 / n) + jx
            k = (ri * 7 + i * 3) % 5
            top = dy - 16
            px2_person(g, fx, top, skins[k], suits[(ri * 5 + i) % 7],
                       hairs[(ri + i) % 4], bald=((ri + i) % 6 == 0))
            if (ri * 3 + i) % 5 == 0:
                g.rectangle([fx + 10, top + 4, fx + 13, top + 13], fill=skins[k])
                g.rectangle([fx + 10, top - 2, fx + 15, top + 3], fill=skins[k])
            m = (ri + i) % 4
            if m == 0:
                g.rectangle([fx - 10, dy + 2, fx - 3, dy + 7], fill=(238, 232, 214))
                g.rectangle([fx + 2, dy + 2, fx + 11, dy + 7], fill=(150, 190, 210))
            elif m == 1:
                g.rectangle([fx - 10, dy + 2, fx - 3, dy + 7], fill=(238, 232, 214))
                g.rectangle([fx + 4, dy + 2, fx + 9, dy + 7], fill=(200, 220, 235))
            elif m == 2:
                g.rectangle([fx + 10, dy - 8, fx + 17, dy - 1], fill=(43, 94, 167))
                g.rectangle([fx + 12, dy - 6, fx + 15, dy - 3], fill=(255, 217, 0))
            else:
                g.rectangle([fx - 12, dy + 2, fx - 5, dy + 7], fill=(150, 190, 210))
                g.rectangle([fx, dy + 2, fx + 9, dy + 7], fill=(238, 232, 214))
    # two standing objectors at the edges, arms raised
    for sx, flip, suit in ((32, 1, (30, 44, 66)), (608, -1, (86, 42, 44))):
        by = 184
        g.rectangle([sx - 4, by - 32, sx + 5, by - 23], fill=(198, 164, 132))
        g.rectangle([sx - 4, by - 32, sx + 5, by - 29], fill=(30, 22, 16))
        g.rectangle([sx - 8, by - 22, sx + 9, by + 1], fill=suit)
        ax0, ax1 = sorted((sx + flip * 8, sx + flip * 11))
        g.rectangle([ax0, by - 38, ax1, by - 21], fill=(198, 164, 132))
        hx0, hx1 = sorted((sx + flip * 8, sx + flip * 13))
        g.rectangle([hx0, by - 40, hx1, by - 37], fill=(198, 164, 132))
    # floor strip, then warm reflection blocks under the podium
    g.rectangle([0, 194, 639, 205], fill=(58, 42, 28))
    g.rectangle([0, 194, 639, 195], fill=(140, 112, 78))
    px2_glow(g, 260, 196, 380, 204, (255, 190, 110))
    # NO DEAL chip, top right (pixel chip, same 18px height as the rest)
    px2_chip(g, 640 - 16 - (px2_text_w("NO DEAL", FONT35) + 8), 16,
             "NO DEAL", RED)
    d._image.paste(im, (int(x0), int(y0)))
def paint_drones(d, box):
    """Night over Ukraine — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "drones.png")



def paint_bahrain(d, box):
    """The Gulf — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "bahrain.png")



def paint_hk(d, box):
    """Hong Kong at dusk — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "hk.png")



def paint_cricket(d, box):
    """Wellington cricket — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "cricket.png")



def paint_f1(d, box):
    """Las Vegas F1 — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "f1.png")



def paint_tennis(d, box):
    """Turin tennis — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "tennis.png")



def paint_football(d, box):
    """Anfield football — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "football.png")



def paint_manipur(d, box):
    """Manipur map — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "manipur.png")



def paint_cikande(d, box):
    """Cikande factory fire — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "cikande.png")



def paint_sparta(d, box):
    """Sparta II — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "sparta.png")



def paint_tehran(d, box):
    """Tehran at dusk — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "tehran.png")



def paint_gaza(d, box):
    """Gaza coast — pre-rendered high-res pixel scene (scenes.py)."""
    _scene(d, box, "gaza.png")



# ---------------------------------------------------------------- stories
# All facts verified in-session against the wires for Sunday 22 Nov 2026.
LEAD = dict(
    num=1, city="ANTALYA", region="EUROPE", topic="CLIMATE",
    headline="COP31 collapses: no deal as the EU revolts over fossil fuels",
    dek=("After a record two days in overtime, the Antalya Pact falls: the EU, "
         "Panama and island states refuse a text that never mentions fossil "
         "fuels. The longest COP in history ends with no deal — the first "
         "collapse since Copenhagen in 2009."),
    source="CNN · Al Jazeera", lon=30.7, lat=36.9)

CARDS = [
    dict(num=2, city="KYIV REGION", region="EUROPE", topic="WAR",
         headline="Russia fires 186 drones; a Kyiv-region block is destroyed",
         dek="161 of 186 drones downed; hits at 18 sites. Five dead in Dymer.",
         source="Air Force", art=paint_drones, lon=30.3, lat=50.9),
    dict(num=3, city="MANAMA", region="MIDDLE EAST", topic="IRAN WAR",
         headline="Iran claims two US radars hit; Bahrain denies it",
         dek="Bahrain says a civilian site was hit; two hurt, no US damage.",
         source="Al Jazeera", art=paint_bahrain, lon=50.6, lat=26.2),
    dict(num=4, city="HONG KONG", region="ASIA", topic="POLITICS",
         headline="Hong Kong votes for its Election Committee",
         dek=("Record 98.79% turnout: 5,640 of 5,709 voters cast ballots; "
              "856 candidates chase 723 seats."),
         source="SCMP", art=paint_hk, lon=114.2, lat=22.3),
    dict(num=5, city="WELLINGTON", region="OCEANIA", topic="SPORT",
         headline="India declare on a record 720/9 in New Zealand",
         dek=("Rahul 136, Pant 128; the highest total ever in New Zealand "
              "and India's best overseas. NZ 119-2 at stumps."),
         source="Dawn", art=paint_cricket, lon=174.8, lat=-41.3),
    dict(num=6, city="LAS VEGAS", region="AMERICAS", topic="SPORT",
         headline="Verstappen wins a wild Las Vegas GP",
         dek=("From pole, Norris second by 0.639s; Piastri third from 17th. "
              "35 lead changes, 352 overtakes."),
         source="Reuters", art=paint_f1, lon=-115.1, lat=36.2),
    dict(num=7, city="TURIN", region="EUROPE", topic="SPORT",
         headline="Alcaraz beats Zverev for the ATP Finals title",
         dek=("6-2, 7-6(9-7): the Spaniard saves three set points to win "
              "his first ATP Finals crown."),
         source="Reuters", art=paint_tennis, lon=7.7, lat=45.1),
    dict(num=8, city="LIVERPOOL", region="EUROPE", topic="SPORT",
         headline="Liverpool thrash 10-man United in Pochettino's debut",
         dek=("Yoro off after 8 minutes; Szoboszlai, Wirtz, Ngumoha, Munoz "
              "score. United 19th."),
         source="Reuters", art=paint_football, lon=-3.0, lat=53.4),
    dict(num=9, city="MANIPUR", region="ASIA", topic="DISASTER",
         headline="Toxic-liquor toll in Manipur climbs to 17",
         dek=("228 in hospital, 38 on dialysis; 1,130 screened. Six "
              "arrested, 4,500 litres seized."),
         source="ThePrint", art=paint_manipur, lon=93.9, lat=24.8),
    dict(num=10, city="CIKANDE", region="ASIA", topic="DISASTER",
         headline="Candy-factory fire in Cikande: 3 dead, 36 missing",
         dek=("Blaze tore through the Fonusa plant Saturday; 300 were on "
              "site. Search goes on."),
         source="CNA", art=paint_cikande, lon=106.3, lat=-6.2),
    dict(num=11, city="GULF OF FINLAND", region="EUROPE", topic="WAR",
         headline="Russian cargo ship still burning off Finland",
         dek=("Drones hit the sanctioned Sparta II on Saturday; her 16 crew "
              "are safe. Towing begins Sunday."),
         source="Reuters", art=paint_sparta, lon=26.2, lat=60.45),
    dict(num=12, city="TEHRAN", region="ENERGY", topic="ENERGY",
         headline="Iran begins rationing electricity",
         dek=("Rolling cuts of up to two hours a day as war strains the "
              "grid; Pezeshkian works in the dark."),
         source="Straits Times", art=paint_tehran, lon=51.4, lat=35.7),
    dict(num=13, city="GAZA CITY", region="MIDDLE EAST", topic="WAR",
         headline="Hamas seeks urgent mediator talks",
         dek=("A drone strike on a food-aid vehicle killed three in Tel "
              "al-Hawa. Hamas demands aid flow freely."),
         source="AFP", art=paint_gaza, lon=34.5, lat=31.5),
]
# fix: card 12 kicker region is MIDDLE EAST, topic ENERGY
CARDS[10]["region"] = "MIDDLE EAST"

INDEX = [
    (14, "Khartoum", "AFRICA", "Drones hit homes and a UN building.", "AFP", 32.5, 15.6),
    (15, "Jerusalem", "MIDDLE EAST", "Netanyahu and Eisenkot end talks with no deal.", "AP", 35.2, 31.8),
    (16, "Paris", "EUROPE", "French protesters rally for a sixth weekend.", "AFP", 2.35, 48.85),
    (17, "Lisbon", "EUROPE", "Thousands march over soaring living costs.", "Dawn", -9.1, 38.7),
    (18, "Warsaw", "EUROPE", "Poland says Russia twice tried to kill a rapper.", "AP", 21.0, 52.25),
    (19, "West Bank", "MIDDLE EAST", 'Eisenkot calls settler arson "terrorism".', "The Hindu", 35.2, 31.9),
    (20, "Riyadh", "MIDDLE EAST", "Saudi coalition intercepts a Houthi drone.", "TOI", 46.7, 24.6),
    (21, "Qeshm Island", "MIDDLE EAST", "Iran says it shot down a US drone over Qeshm.", "TOI", 56.3, 26.9),
    (22, "Makkah", "MIDDLE EAST", "Saudi Arabia issues an alert for Makkah.", "AIR", 39.8, 21.4),
    (23, "Washington", "AMERICAS", "Trump says Iran wants a deal, terms unacceptable.", "AP", -77.0, 38.9),
    (24, "Moscow", "EUROPE", "Russia seizes on a US offer on European security.", "AP", 37.6, 55.75),
    (25, "New Delhi", "ASIA", "Nepal PM Balendra Shah arrives in Delhi.", "The Hindu", 77.2, 28.6),
    (26, "Arunachal", "ASIA", "40 border villages see families return.", "The Hindu", 96.0, 27.3),
    (27, "India", "ASIA", "India thrash Thailand 7-0 in women's hockey.", "The Hindu", 80.0, 21.0),
    (28, "Johannesburg", "AFRICA", "Ex-deputy president Mlambo-Ngcuka dies at 71.", "AP", 28.0, -26.2),
    (29, "Nigeria", "AFRICA", "Boat capsizes on the way to a funeral; 24 dead.", "AP", 8.0, 9.0),
    (30, "Rome", "EUROPE", "Paolo Bulgari, jeweller and luxury builder, dies at 89.", "AP", 12.5, 41.9),
    (31, "London", "EUROPE", "England beat New Zealand 37-12.", "All Blacks", -0.1, 51.5),
    (32, "Wollongong", "OCEANIA", "England beat France 50-38 in wheelchair final.", "BBC", 150.9, -34.4),
    (33, "Geneva", "EUROPE", 'Countries open a path to a "killer robots" accord.', "Dawn", 6.1, 46.2),
    (34, "Strait of Hormuz", "MIDDLE EAST", "Briton swims the strait for the environment.", "Dawn", 56.5, 26.5),
    (35, "England", "EUROPE", 'Village votes to "leave the UK" over a migrant camp.', "Dawn", -1.0, 52.5),
    (36, "Washington", "AMERICAS", "Pentagon curbs defence ties with Canada.", "Dawn", -77.0, 38.9),
    (37, "Mexico", "AMERICAS", "US-bound migrant caravan reaches Mexico.", "Dawn", -99.1, 19.4),
    (38, "West Bengal", "ASIA", "Christians complain of rising attacks.", "Dawn", 88.4, 22.6),
    (39, "United Nations", "GLOBAL", "Youth face economic insecurity, UN warns.", "Dawn", -73.97, 40.75),
    (40, "Kabul", "ASIA", "Afghan tradition keeps grapes fresh for winter.", "Dawn", 69.2, 34.5),
    (41, "Benghazi", "AFRICA", "Russian warship reported hit at a Libyan base.", "AP", 20.1, 32.1),
    (42, "Odesa", "EUROPE", "Strikes cripple the power grid.", "Europa Journal", 30.7, 46.5),
]

STATS = [
    ("186", "DRONES LAUNCHED"),
    ("161", "DOWNED OR JAMMED"),
    ("98.79%", "HK TURNOUT"),
    ("720/9", "INDIA'S RECORD TOTAL"),
    ("4–0", "LIVERPOOL"),
]

DATE_CHECK = ("DATE CHECK — NOT SUNDAY:  Friday · Gen Z protests sweep 25 "
              "European countries (AFP)  ·  Saturday · Drones hit the Sparta II "
              "(Yle)  ·  Fire breaks out at Cikande (AP)  ·  Iranian attacks hit "
              "a civilian site in Bahrain (Khaleej Times)")

# ---------------------------------------------------------------- layout


# ---------------------------------------------------------------- stories
# All facts verified in-session against the wires for Sunday 22 Nov 2026.
LEAD = dict(
    num=1, city="ANTALYA", region="EUROPE", topic="CLIMATE",
    headline="COP31 collapses: no deal as the EU revolts over fossil fuels",
    dek=("After a record two days in overtime, the Antalya Pact falls: the EU, "
         "Panama and island states refuse a text that never mentions fossil "
         "fuels. The longest COP in history ends with no deal — the first "
         "collapse since Copenhagen in 2009."),
    source="CNN · Al Jazeera", lon=30.7, lat=36.9)

CARDS = [
    dict(num=2, city="KYIV REGION", region="EUROPE", topic="WAR",
         headline="Russia fires 186 drones; a Kyiv-region block is destroyed",
         dek="161 of 186 drones downed; hits at 18 sites. Five dead in Dymer.",
         source="Air Force", art=paint_drones, lon=30.3, lat=50.9),
    dict(num=3, city="MANAMA", region="MIDDLE EAST", topic="IRAN WAR",
         headline="Iran claims two US radars hit; Bahrain denies it",
         dek="Bahrain says a civilian site was hit; two hurt, no US damage.",
         source="Al Jazeera", art=paint_bahrain, lon=50.6, lat=26.2),
    dict(num=4, city="HONG KONG", region="ASIA", topic="POLITICS",
         headline="Hong Kong votes for its Election Committee",
         dek=("Record 98.79% turnout: 5,640 of 5,709 voters cast ballots; "
              "856 candidates chase 723 seats."),
         source="SCMP", art=paint_hk, lon=114.2, lat=22.3),
    dict(num=5, city="WELLINGTON", region="OCEANIA", topic="SPORT",
         headline="India declare on a record 720/9 in New Zealand",
         dek=("Rahul 136, Pant 128; the highest total ever in New Zealand "
              "and India's best overseas. NZ 119-2 at stumps."),
         source="Dawn", art=paint_cricket, lon=174.8, lat=-41.3),
    dict(num=6, city="LAS VEGAS", region="AMERICAS", topic="SPORT",
         headline="Verstappen wins a wild Las Vegas GP",
         dek=("From pole, Norris second by 0.639s; Piastri third from 17th. "
              "35 lead changes, 352 overtakes."),
         source="Reuters", art=paint_f1, lon=-115.1, lat=36.2),
    dict(num=7, city="TURIN", region="EUROPE", topic="SPORT",
         headline="Alcaraz beats Zverev for the ATP Finals title",
         dek=("6-2, 7-6(9-7): the Spaniard saves three set points to win "
              "his first ATP Finals crown."),
         source="Reuters", art=paint_tennis, lon=7.7, lat=45.1),
    dict(num=8, city="LIVERPOOL", region="EUROPE", topic="SPORT",
         headline="Liverpool thrash 10-man United in Pochettino's debut",
         dek=("Yoro off after 8 minutes; Szoboszlai, Wirtz, Ngumoha, Munoz "
              "score. United 19th."),
         source="Reuters", art=paint_football, lon=-3.0, lat=53.4),
    dict(num=9, city="MANIPUR", region="ASIA", topic="DISASTER",
         headline="Toxic-liquor toll in Manipur climbs to 17",
         dek=("228 in hospital, 38 on dialysis; 1,130 screened. Six "
              "arrested, 4,500 litres seized."),
         source="ThePrint", art=paint_manipur, lon=93.9, lat=24.8),
    dict(num=10, city="CIKANDE", region="ASIA", topic="DISASTER",
         headline="Candy-factory fire in Cikande: 3 dead, 36 missing",
         dek=("Blaze tore through the Fonusa plant Saturday; 300 were on "
              "site. Search goes on."),
         source="CNA", art=paint_cikande, lon=106.3, lat=-6.2),
    dict(num=11, city="GULF OF FINLAND", region="EUROPE", topic="WAR",
         headline="Russian cargo ship still burning off Finland",
         dek=("Drones hit the sanctioned Sparta II on Saturday; her 16 crew "
              "are safe. Towing begins Sunday."),
         source="Reuters", art=paint_sparta, lon=26.2, lat=60.45),
    dict(num=12, city="TEHRAN", region="ENERGY", topic="ENERGY",
         headline="Iran begins rationing electricity",
         dek=("Rolling cuts of up to two hours a day as war strains the "
              "grid; Pezeshkian works in the dark."),
         source="Straits Times", art=paint_tehran, lon=51.4, lat=35.7),
    dict(num=13, city="GAZA CITY", region="MIDDLE EAST", topic="WAR",
         headline="Hamas seeks urgent mediator talks",
         dek=("A drone strike on a food-aid vehicle killed three in Tel "
              "al-Hawa. Hamas demands aid flow freely."),
         source="AFP", art=paint_gaza, lon=34.5, lat=31.5),
]
# fix: card 12 kicker region is MIDDLE EAST, topic ENERGY
CARDS[10]["region"] = "MIDDLE EAST"

INDEX = [
    (14, "Khartoum", "AFRICA", "Drones hit homes and a UN building.", "AFP", 32.5, 15.6),
    (15, "Jerusalem", "MIDDLE EAST", "Netanyahu and Eisenkot end talks with no deal.", "AP", 35.2, 31.8),
    (16, "Paris", "EUROPE", "French protesters rally for a sixth weekend.", "AFP", 2.35, 48.85),
    (17, "Lisbon", "EUROPE", "Thousands march over soaring living costs.", "Dawn", -9.1, 38.7),
    (18, "Warsaw", "EUROPE", "Poland says Russia twice tried to kill a rapper.", "AP", 21.0, 52.25),
    (19, "West Bank", "MIDDLE EAST", 'Eisenkot calls settler arson "terrorism".', "The Hindu", 35.2, 31.9),
    (20, "Riyadh", "MIDDLE EAST", "Saudi coalition intercepts a Houthi drone.", "TOI", 46.7, 24.6),
    (21, "Qeshm Island", "MIDDLE EAST", "Iran says it shot down a US drone over Qeshm.", "TOI", 56.3, 26.9),
    (22, "Makkah", "MIDDLE EAST", "Saudi Arabia issues an alert for Makkah.", "AIR", 39.8, 21.4),
    (23, "Washington", "AMERICAS", "Trump says Iran wants a deal, terms unacceptable.", "AP", -77.0, 38.9),
    (24, "Moscow", "EUROPE", "Russia seizes on a US offer on European security.", "AP", 37.6, 55.75),
    (25, "New Delhi", "ASIA", "Nepal PM Balendra Shah arrives in Delhi.", "The Hindu", 77.2, 28.6),
    (26, "Arunachal", "ASIA", "40 border villages see families return.", "The Hindu", 96.0, 27.3),
    (27, "India", "ASIA", "India thrash Thailand 7-0 in women's hockey.", "The Hindu", 80.0, 21.0),
    (28, "Johannesburg", "AFRICA", "Ex-deputy president Mlambo-Ngcuka dies at 71.", "AP", 28.0, -26.2),
    (29, "Nigeria", "AFRICA", "Boat capsizes on the way to a funeral; 24 dead.", "AP", 8.0, 9.0),
    (30, "Rome", "EUROPE", "Paolo Bulgari, jeweller and luxury builder, dies at 89.", "AP", 12.5, 41.9),
    (31, "London", "EUROPE", "England beat New Zealand 37-12.", "All Blacks", -0.1, 51.5),
    (32, "Wollongong", "OCEANIA", "England beat France 50-38 in wheelchair final.", "BBC", 150.9, -34.4),
    (33, "Geneva", "EUROPE", 'Countries open a path to a "killer robots" accord.', "Dawn", 6.1, 46.2),
    (34, "Strait of Hormuz", "MIDDLE EAST", "Briton swims the strait for the environment.", "Dawn", 56.5, 26.5),
    (35, "England", "EUROPE", 'Village votes to "leave the UK" over a migrant camp.', "Dawn", -1.0, 52.5),
    (36, "Washington", "AMERICAS", "Pentagon curbs defence ties with Canada.", "Dawn", -77.0, 38.9),
    (37, "Mexico", "AMERICAS", "US-bound migrant caravan reaches Mexico.", "Dawn", -99.1, 19.4),
    (38, "West Bengal", "ASIA", "Christians complain of rising attacks.", "Dawn", 88.4, 22.6),
    (39, "United Nations", "GLOBAL", "Youth face economic insecurity, UN warns.", "Dawn", -73.97, 40.75),
    (40, "Kabul", "ASIA", "Afghan tradition keeps grapes fresh for winter.", "Dawn", 69.2, 34.5),
    (41, "Benghazi", "AFRICA", "Russian warship reported hit at a Libyan base.", "AP", 20.1, 32.1),
    (42, "Odesa", "EUROPE", "Strikes cripple the power grid.", "Europa Journal", 30.7, 46.5),
]

STATS = [
    ("186", "DRONES LAUNCHED"),
    ("161", "DOWNED OR JAMMED"),
    ("98.79%", "HK TURNOUT"),
    ("720/9", "INDIA'S RECORD TOTAL"),
    ("4–0", "LIVERPOOL"),
]

DATE_CHECK = ("DATE CHECK — NOT SUNDAY:  Friday · Gen Z protests sweep 25 "
              "European countries (AFP)  ·  Saturday · Drones hit the Sparta II "
              "(Yle)  ·  Fire breaks out at Cikande (AP)  ·  Iranian attacks hit "
              "a civilian site in Bahrain (Khaleej Times)")

# ---------------------------------------------------------------- layout
def num_disc(d, cx, cy, r, color, num, size=9):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color,
              outline=(255, 255, 255), width=1)
    f = IN(size)
    tw = d.textlength(str(num), font=f)
    th = f.getbbox(str(num))[3] - f.getbbox(str(num))[1]
    d.text((cx - tw / 2, cy - th / 2 - 1), str(num), font=f, fill=(255, 255, 255))


def draw_card(d, x, y, w, h, s):
    col = RCOL[s["region"]]
    art_h = 54
    s["art"](d, (x, y, x + w, y + art_h))
    num_disc(d, x + 11, y + 11, 9, col, s["num"], 10)
    kicker = "%d %s · %s" % (s["num"], s["city"], s["topic"])
    draw_tracked(d, x, y + art_h + 5, kicker, IN(9), col, 0.8)
    hl = fit_lines(d, s["headline"], PF(14), w, 2)
    yy = y + art_h + 19
    for ln in hl:
        d.text((x, yy), ln, font=PF(14), fill=INK)
        yy += 16
    dek = s["dek"] + " (" + s["source"] + ")"
    dl = fit_lines(d, dek, PT(10), w, 3)
    yy = y + art_h + 53
    for ln in dl:
        d.text((x, yy), ln, font=PT(10), fill=INK_SOFT)
        yy += 12


def draw_side_card(d, x, y, w, h, s):
    col = RCOL[s["region"]]
    art_h = h - 55
    s["art"](d, (x, y, x + w, y + art_h))
    num_disc(d, x + 11, y + 11, 9, col, s["num"], 10)
    kicker = "%d %s · %s" % (s["num"], s["city"], s["topic"])
    draw_tracked(d, x, y + art_h + 3, kicker, IN(9), col, 0.8)
    hl = fit_lines(d, s["headline"], PF(12), w, 2)
    yy = y + art_h + 15
    for ln in hl:
        d.text((x, yy), ln, font=PF(12), fill=INK)
        yy += 14
    dek = s["dek"] + " (" + s["source"] + ")"
    dl = fit_lines(d, dek, PT(9), w, 1)
    d.text((x, y + art_h + 44), dl[0], font=PT(9), fill=INK_SOFT)


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # kicker line
    draw_tracked(d, 16, 9, "THE DAY IN WORLD NEWS", IN(10), RED, 1.4)
    rw = tracked_w(d, "42 STORIES · 7 REGIONS · ONE DAY", IN(10), 1.4)
    draw_tracked(d, 1008 - rw, 9, "42 STORIES · 7 REGIONS · ONE DAY", IN(10),
                 INK, 1.4)
    d.line([16, 24, 1008, 24], fill=INK, width=1)
    # masthead, fitted
    size = 62
    while size > 30:
        f = PF(size, "Black")
        if d.textlength("Sunday 22 November 2026", font=f) <= 960:
            break
        size -= 1
    center_text(d, 512, 28, "Sunday 22 November 2026", PF(size, "Black"), INK)
    center_text(d, 512, 102,
                "Everything on this page happened, or was first reported, "
                "on Sunday 22 November 2026.",
                PT(13, "Italic"), INK_SOFT)
    # region bar — each segment gets a 9x9 pixel icon before its label
    labels = []
    for name, n, col in REGIONS:
        labels.append((name, n, col, tracked_w(d, "%s %d" % (name, n), IN(9), 1.0) + 14 + 15))
    total = 992
    raw = [max(lw, total * n / 42.0) for _, n, _, lw in labels]
    scale = total / sum(raw)
    widths = [r * scale for r in raw]
    x = 16
    for (name, n, col, _), wd in zip(labels, widths):
        d.rectangle([x, 122, x + wd, 142], fill=col)
        tw = tracked_w(d, "%s %d" % (name, n), IN(9), 1.0)
        ix = x + (wd - (9 + 6 + tw)) / 2
        draw_px_icon(d, int(ix), 127, REGION_ICONS[name], (255, 255, 255))
        draw_tracked(d, ix + 15, 128, "%s %d" % (name, n), IN(9),
                     (255, 255, 255), 1.0)
        x += wd
    # lead art + side cards 2 and 3
    paint_lead(d, (16, 148, 656, 354))
    draw_side_card(d, 664, 148, 344, 102, CARDS[0])
    draw_side_card(d, 664, 254, 344, 100, CARDS[1])
    # lead kicker / headline / dek — headline enlarged to two lines so the
    # white gap between the lead image and the dek is filled. PF(34) with
    # 38pt leading is the largest that fits: line 2's glyphs end at 446,
    # the dek starts at 452, and the cards stay at 486.
    draw_tracked(d, 16, 358, "1 ANTALYA · CLIMATE", IN(10), RED, 1.2)
    rw = tracked_w(d, "AFP · AP · REUTERS", IN(9), 1.0)
    draw_tracked(d, 1008 - rw, 359, "AFP · AP · REUTERS", IN(9), GREY, 1.0)
    hl = wrap(d, LEAD["headline"], PF(34), 600)
    yy = 370
    for ln in hl:
        d.text((16, yy), ln, font=PF(34), fill=INK)
        yy += 38
    dl = fit_lines(d, LEAD["dek"] + " (" + LEAD["source"] + ")", PT(13), 992, 2)
    yy = 452
    for ln in dl:
        d.text((16, yy), ln, font=PT(13), fill=INK_SOFT)
        yy += 15
    # card rows 4-8 and 9-13
    for i, s in enumerate(CARDS[2:7]):
        draw_card(d, 16 + i * 200, 486, 192, 150, s)
    for i, s in enumerate(CARDS[7:12]):
        draw_card(d, 16 + i * 200, 642, 192, 150, s)
    # divider ornament between the card rows and the map section
    d.line([16, 796, 1008, 796], fill=(201, 168, 106), width=1)
    d.polygon([(512, 793), (515, 796), (512, 799), (509, 796)],
              fill=(201, 168, 106))
    d.rectangle([500, 795, 501, 796], fill=(201, 168, 106))
    d.rectangle([523, 795, 524, 796], fill=(201, 168, 106))
    # map + index header
    draw_tracked(d, 16, 800, "ALSO ON SUNDAY 22 NOVEMBER", IN(11), INK, 1.2)
    rw = tracked_w(d, "29 MORE STORIES · NUMBERS 14–42 · DOTS ON THE MAP", IN(8), 0.8)
    draw_tracked(d, 1008 - rw, 801, "29 MORE STORIES · NUMBERS 14–42 · DOTS ON THE MAP",
                 IN(8), GREY, 0.8)
    # map — fully pixelated: rasterised into 4px blocks, then pasted
    mapbox = (16, 816, 396, 954)
    mw, mh = int(mapbox[2] - mapbox[0]), int(mapbox[3] - mapbox[1])
    d._image.paste(pixel_map(mw, mh, 4, -180, 180, -60, 85, SEA, LAND),
                   (int(mapbox[0]), int(mapbox[1])))
    # project with lat range -60..85 so Antarctica stays out
    def proj2(lon, lat):
        x0, y0, x1, y1 = mapbox
        return (x0 + (lon + 180.0) / 360.0 * (x1 - x0),
                y0 + (85.0 - lat) / 145.0 * (y1 - y0))
    d.rectangle(mapbox, outline=INK, width=1)
    # pins: cards 1-13 big, index 14-42 small
    pins = []
    pins.append((1, LEAD["lon"], LEAD["lat"], RCOL[LEAD["region"]], True))
    for s in CARDS:
        pins.append((s["num"], s["lon"], s["lat"], RCOL[s["region"]], True))
    for num, city, region, head, src, lon, lat in INDEX:
        pins.append((num, lon, lat, RCOL[region], False))
    # de-collision in projected space (radii match the pixel-pin halves)
    placed, final = [], []
    for num, lon, lat, col, big in pins:
        x, y = proj2(lon, lat)
        r = 7 if big else 6
        done = False
        for ox, oy in [(0, 0), (10, 0), (-10, 0), (0, 10), (0, -10),
                       (10, 10), (-10, -10), (10, -10), (-10, 10),
                       (16, 0), (-16, 0), (0, 16), (0, -16)]:
            nx, ny = x + ox, y + oy
            if all((nx - px) ** 2 + (ny - py) ** 2 >= (r + pr + 1) ** 2
                   for px, py, pr in placed):
                placed.append((nx, ny, r))
                final.append((num, nx, ny, col, big))
                done = True
                break
        if not done:
            placed.append((x, y, r))
            final.append((num, x, y, col, big))
    for num, x, y, col, big in final:
        px_pin(d, x, y, 13 if big else 11, col, num, big)
    # map caption with pixel pin icons
    cap1 = "dots 1–13"
    cap2 = "dots 14–42"
    d.rectangle([20, 940, 28, 948], fill=RED, outline=INK)
    d.text((34, 938), cap1, font=PT(8, "Italic"), fill=(60, 70, 80))
    x2 = 34 + d.textlength(cap1, font=PT(8, "Italic")) + 8
    d.rectangle([x2, 941, x2 + 6, 947], fill=(120, 120, 120), outline=INK)
    d.text((x2 + 11, 938), cap2, font=PT(8, "Italic"), fill=(60, 70, 80))
    # index, two columns
    cols = [(408, 700), (712, 1008)]
    for ci, (cx0, cx1) in enumerate(cols):
        items = INDEX[ci * 15:(ci + 1) * 15]
        yy = 808
        for num, city, region, head, src, lon, lat in items:
            col = RCOL[region]
            num_disc(d, cx0 + 6, yy + 5, 5, col, num, 7)
            line = "%s — %s (%s)" % (city, head, src)
            maxw = cx1 - cx0 - 16
            while d.textlength(line, font=PT(8)) > maxw and " " in line:
                line = line.rsplit(" ", 1)[0] + " ..."
            d.text((cx0 + 14, yy), line, font=PT(8), fill=INK)
            yy += 10
    # stat strip — numbers lifted 3px so the "720/9" slash clears the labels
    d.line([16, 962, 1008, 962], fill=INK, width=1)
    for i, (num, lab) in enumerate(STATS):
        cx = 16 + i * 198.4 + 99.2
        center_text(d, cx, 963, num, PT(24, "Bold"), INK)
        draw_tracked_c(d, cx, 992, lab, IN(8), GREY, 1.0)
        if i:
            d.line([16 + i * 198.4, 963, 16 + i * 198.4, 1000], fill=(200, 194, 178),
                   width=1)
    # DATE CHECK
    d.text((16, 1001), DATE_CHECK, font=PT(9), fill=INK)
    # footer
    d.text((16, 1012), "Claims by warring sides are attributed. Every drawing "
                       "and map is drawn in code.",
           font=PT(9, "Italic"), fill=GREY)
    src = ("Sources: AP · Reuters · AFP · CNN · Al Jazeera · SCMP · Dawn · "
           "The Hindu · Ukrinform · Khaleej Times · TOI · ThePrint · CNA · "
           "BBC · Yle · Wafa")
    sw = d.textlength(src, font=PT(9))
    d.text((1008 - sw, 1012), src, font=PT(9), fill=GREY)
    return img


def main():
    img = build()
    img.save(os.path.join(HERE, "entry.png"))
    import hashlib
    data = open(os.path.join(HERE, "entry.png"), "rb").read()
    print("entry.png", len(data), "bytes, sha256",
          hashlib.sha256(data).hexdigest(), img.size)


if __name__ == "__main__":
    main()
