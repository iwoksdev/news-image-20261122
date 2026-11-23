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
# Every scene is drawn on a low-res grid canvas (final size / 2) and pasted
# back with Image.NEAREST, so the page shows crisp 2x2 blocks — the pixel
# style the user approved on the v2 lead sample. Scene text uses bitmap
# glyphs defined here (my own letterforms); page typography stays smooth.
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


def px_person(g, cx, top, skin, suit, hair, bald=False):
    """Seated delegate on the grid: head + shoulders."""
    g.rectangle([cx - 2, top, cx + 2, top + 3], fill=skin)
    if not bald:
        g.rectangle([cx - 2, top, cx + 2, top + 1], fill=hair)
    g.rectangle([cx - 4, top + 4, cx + 4, top + 7], fill=suit)


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
    """COP31 plenary hall, Antalya — pixel art (320x103 grid, 2x NEAREST)."""
    im, g = px_canvas(320, 103, (22, 40, 58))
    # ceiling band + gold line
    g.rectangle([0, 0, 320, 5], fill=(30, 48, 68))
    g.rectangle([0, 5, 320, 5], fill=(201, 168, 106))
    # side drapes with folds
    for dx0 in (0, 309):
        g.rectangle([dx0, 0, dx0 + 10, 103], fill=(56, 32, 36))
        g.rectangle([dx0 + 3, 0, dx0 + 4, 103], fill=(78, 46, 50))
        g.rectangle([dx0 + 7, 0, dx0 + 8, 103], fill=(78, 46, 50))
    # warm glow behind the screen: sparse gold dots
    px_glow(g, 100, 8, 220, 42, (255, 190, 110))
    # chandelier, two tiers, top centre
    cx = 160
    g.rectangle([cx, 1, cx, 6], fill=(201, 168, 106))
    g.rectangle([cx - 20, 7, cx + 20, 7], fill=(201, 168, 106))
    for dx in (-18, -9, 0, 9, 18):
        g.rectangle([cx + dx - 1, 5, cx + dx + 1, 7], fill=(255, 217, 122))
    g.rectangle([cx - 12, 8, cx - 12, 11], fill=(201, 168, 106))
    g.rectangle([cx + 12, 8, cx + 12, 11], fill=(201, 168, 106))
    g.rectangle([cx - 30, 12, cx + 30, 12], fill=(201, 168, 106))
    for dx in (-28, -19, -10, 0, 10, 19, 28):
        g.rectangle([cx + dx - 1, 10, cx + dx + 1, 12], fill=(255, 217, 122))
        g.rectangle([cx + dx, 13, cx + dx, 15], fill=(255, 225, 150))
    g.rectangle([cx - 2, 4, cx + 2, 6], fill=(255, 217, 122))
    # wall clock, top left
    ccx, ccy = 24, 14
    g.ellipse([ccx - 6, ccy - 6, ccx + 6, ccy + 6], fill=(238, 232, 214),
              outline=(120, 100, 70))
    g.rectangle([ccx - 1, ccy - 5, ccx + 1, ccy - 3], fill=(120, 100, 70))
    g.rectangle([ccx - 1, ccy + 3, ccx + 1, ccy + 5], fill=(120, 100, 70))
    g.rectangle([ccx - 5, ccy - 1, ccx - 3, ccy + 1], fill=(120, 100, 70))
    g.rectangle([ccx + 3, ccy - 1, ccx + 5, ccy + 1], fill=(120, 100, 70))
    g.rectangle([ccx, ccy - 2, ccx + 3, ccy], fill=INK)
    g.rectangle([ccx, ccy - 4, ccx, ccy], fill=INK)
    px_text_c(g, ccx, ccy + 8, "OVERTIME", FONT35, (232, 220, 192))
    # big screen: the pact, no consensus
    sx0, sy0, sx1, sy1 = 107, 16, 213, 38
    g.rectangle([sx0, sy0, sx1, sy1], fill=(13, 26, 38), outline=(201, 168, 106))
    px_text_c(g, 160, 19, "ANTALYA PACT", FONT57, (232, 220, 192))
    g.rectangle([sx0 + 8, 28, sx1 - 8, 28], fill=(120, 100, 70))
    px_text_c(g, 160, 30, "NO CONSENSUS", FONT57, (224, 82, 68))
    # podium with gold trim, globe on its front, gavel on top
    px0, px1, py0, py1 = 134, 186, 41, 57
    g.polygon([(px0, py1), (px0 + 4, py0), (px1 - 4, py0), (px1, py1)],
              fill=(107, 74, 47))
    g.rectangle([px0 - 3, py0 - 2, px1 + 3, py0], fill=(84, 58, 36))
    g.rectangle([px0 + 2, py0 + 5, px1 - 2, py0 + 5], fill=(201, 168, 106))
    gx, gy = 160, py0 + 11
    g.ellipse([gx - 5, gy - 5, gx + 5, gy + 5], fill=(127, 176, 216),
              outline=(232, 220, 192))
    g.rectangle([gx - 3, gy - 3, gx - 1, gy - 1], fill=(240, 240, 230))
    g.rectangle([gx + 1, gy + 1, gx + 3, gy + 3], fill=(240, 240, 230))
    # gavel: bold gold handle + head on the podium top
    g.rectangle([px0 + 6, py0 - 6, px0 + 22, py0 - 5], fill=(201, 168, 106))
    g.rectangle([px0 + 20, py0 - 9, px0 + 27, py0 - 6], fill=(201, 168, 106))
    g.rectangle([px0 + 8, py0 - 4, px0 + 11, py0 - 2], fill=(84, 58, 36))
    # delegate rows: desks + figures, jittered and varied
    skins = [(198, 164, 132), (172, 128, 96), (214, 182, 150), (150, 108, 82),
             (226, 196, 164)]
    suits = [(30, 44, 66), (52, 52, 56), (44, 62, 48), (86, 42, 44),
             (38, 38, 44), (66, 54, 40), (70, 60, 90)]
    hairs = [(30, 22, 16), (70, 70, 70), (160, 160, 160), (20, 20, 20)]
    for ri, (dy, n) in enumerate([(58, 7), (72, 8), (88, 9)]):
        g.rectangle([12, dy, 308, dy + 4], fill=(58, 44, 32))
        g.rectangle([12, dy, 308, dy], fill=(120, 96, 66))
        for i in range(n):
            jx = (i * 13 + ri * 7) % 5 - 2
            fx = int(12 + (i + 0.5) * 296 / n) + jx
            k = (ri * 7 + i * 3) % 5
            top = dy - 8
            px_person(g, fx, top, skins[k], suits[(ri * 5 + i) % 7],
                      hairs[(ri + i) % 4], bald=((ri + i) % 6 == 0))
            if (ri * 3 + i) % 5 == 0:
                g.rectangle([fx + 5, top + 2, fx + 6, top + 6], fill=skins[k])
                g.rectangle([fx + 5, top - 1, fx + 7, top + 1], fill=skins[k])
            m = (ri + i) % 4
            if m == 0:
                g.rectangle([fx - 5, dy + 1, fx - 2, dy + 3], fill=(238, 232, 214))
                g.rectangle([fx + 1, dy + 1, fx + 5, dy + 3], fill=(150, 190, 210))
            elif m == 1:
                g.rectangle([fx - 5, dy + 1, fx - 2, dy + 3], fill=(238, 232, 214))
                g.rectangle([fx + 2, dy + 1, fx + 4, dy + 3], fill=(200, 220, 235))
            elif m == 2:
                g.rectangle([fx + 5, dy - 4, fx + 8, dy - 1], fill=(43, 94, 167))
                g.rectangle([fx + 6, dy - 3, fx + 7, dy - 2], fill=(255, 217, 0))
            else:
                g.rectangle([fx - 6, dy + 1, fx - 3, dy + 3], fill=(150, 190, 210))
                g.rectangle([fx, dy + 1, fx + 4, dy + 3], fill=(238, 232, 214))
    # two standing objectors at the edges, arms raised
    for sx, flip, suit in ((16, 1, (30, 44, 66)), (304, -1, (86, 42, 44))):
        by = 92
        g.rectangle([sx - 2, by - 16, sx + 2, by - 12], fill=(198, 164, 132))
        g.rectangle([sx - 2, by - 16, sx + 2, by - 15], fill=(30, 22, 16))
        g.rectangle([sx - 4, by - 11, sx + 4, by], fill=suit)
        ax0, ax1 = sorted((sx + flip * 4, sx + flip * 5))
        g.rectangle([ax0, by - 19, ax1, by - 11], fill=(198, 164, 132))
        hx0, hx1 = sorted((sx + flip * 4, sx + flip * 6))
        g.rectangle([hx0, by - 20, hx1, by - 19], fill=(198, 164, 132))
    # floor strip, then warm reflection dots on it under the podium
    g.rectangle([0, 97, 320, 103], fill=(58, 42, 28))
    g.rectangle([0, 97, 320, 97], fill=(140, 112, 78))
    px_glow(g, 130, 98, 190, 102, (255, 190, 110))
    # NO DEAL chip, top right (pixel chip, same 18px height as the rest)
    px_chip(g, 320 - 8 - (px_text_w("NO DEAL", FONT35) + 7), 8, "NO DEAL", RED)
    px_paste(d, box, im)


def paint_drones(d, box):
    """Night over Ukraine: drones, bursts, a burning block — pixel art."""
    im, g = px_canvas(172, 24, (13, 27, 46))
    g.rectangle([0, 9, 172, 17], fill=(26, 51, 72))
    g.rectangle([0, 18, 172, 18], fill=(39, 75, 99))
    # stars
    for sx, sy in [(14, 4), (38, 2), (77, 3), (107, 2), (134, 5), (155, 2),
                   (57, 6), (95, 7)]:
        g.point((sx, sy), fill=(220, 225, 235))
    # crescent moon
    mx, my = 151, 5
    g.ellipse([mx - 3, my - 3, mx + 3, my + 3], fill=(232, 228, 205))
    g.ellipse([mx - 1, my - 3, mx + 4, my + 3], fill=(13, 27, 46))
    # drones: 3x3 X with red + green lights
    for dx, dy in [(28, 7), (72, 5), (114, 9), (145, 12)]:
        g.point((dx - 1, dy - 1), fill=(200, 205, 215))
        g.point((dx + 1, dy - 1), fill=(200, 205, 215))
        g.point((dx, dy), fill=(230, 230, 230))
        g.point((dx - 1, dy + 1), fill=(200, 205, 215))
        g.point((dx + 1, dy + 1), fill=(200, 205, 215))
        g.point((dx - 2, dy - 1), fill=(255, 60, 50))
        g.point((dx + 2, dy + 1), fill=(80, 220, 120))
    # interception bursts
    for bx, by in [(52, 13), (124, 15)]:
        px_glow(g, bx - 4, by - 4, bx + 5, by + 5, (255, 170, 60))
        for ox, oy in [(0, -3), (0, 3), (-3, 0), (3, 0), (-2, -2), (2, -2),
                       (-2, 2), (2, 2)]:
            g.point((bx + ox, by + oy), fill=(255, 205, 90))
        g.rectangle([bx - 1, by - 1, bx + 1, by + 1], fill=(255, 230, 150))
    # ground: city silhouette + burning block
    g.rectangle([0, 19, 172, 24], fill=(10, 16, 26))
    for bx, bw, bh in [(3, 17, 3), (24, 14, 2), (41, 21, 4), (89, 16, 3),
                       (108, 19, 4), (151, 17, 3)]:
        g.rectangle([bx, 19 - bh, bx + bw, 19], fill=(16, 26, 40))
        for wy in range(2):
            for wx in range(3):
                g.point((bx + 3 + wx * 5, 19 - bh + 1 + wy * 2),
                        fill=(255, 205, 110))
    # the Dymer block, hit and burning
    g.rectangle([65, 14, 82, 19], fill=(24, 34, 50))
    px_glow(g, 67, 11, 81, 15, (255, 120, 40))
    g.point((70, 12), fill=(255, 150, 50))
    g.point((74, 11), fill=(255, 220, 90))
    g.point((77, 12), fill=(255, 150, 50))
    px_paste(d, box, im)


def paint_bahrain(d, box):
    """The Gulf: Bahrain, two radar dishes, claim vs denial — pixel art."""
    im, g = px_canvas(172, 23, (185, 210, 226))
    im.paste(px_map(172, 23, 47, 57, 24, 30, (185, 210, 226), (224, 211, 178)),
             (0, 0))
    # Bahrain island marker
    bx, by = 62, 15
    g.ellipse([bx - 4, by - 4, bx + 4, by + 4], outline=RED)
    g.rectangle([bx - 1, by - 1, bx + 1, by + 1], fill=RED)
    # radar dishes at al-Riffa and Awali
    for dx, dy in [(107, 10), (134, 13)]:
        g.rectangle([dx, dy + 1, dx, dy + 5], fill=(240, 240, 235))
        g.rectangle([dx - 3, dy + 5, dx + 3, dy + 5], fill=(240, 240, 235))
        g.rectangle([dx - 4, dy - 3, dx + 4, dy - 1], fill=(245, 245, 240))
        g.rectangle([dx - 2, dy - 4, dx + 2, dy - 3], fill=(245, 245, 240))
        g.rectangle([dx - 4, dy - 1, dx + 4, dy - 1], fill=(120, 120, 115))
    # claimed strike: dashed red line to a burst
    ex, ey = 120, 7
    for t in range(0, 10, 2):
        px = int(bx + (ex - bx) * t / 10)
        py = int(by + (ey - by) * t / 10)
        g.rectangle([px, py, px + 1, py + 1], fill=RED)
    for ox, oy in [(0, -3), (0, 3), (-3, 0), (3, 0), (-2, -2), (2, -2),
                   (-2, 2), (2, 2)]:
        g.point((ex + ox, ey + oy), fill=(255, 180, 80))
    g.rectangle([ex - 1, ey - 1, ex + 1, ey + 1], fill=(255, 230, 150))
    # chip top-left: the pixel chip is wider than the old smooth one, so it
    # moves up here to keep clear of the Bahrain marker ring.
    px_chip(g, 19, 2, "CLAIM VS DENIAL", RED)
    px_paste(d, box, im)


def paint_hk(d, box):
    """Hong Kong at dusk: skyline, water, ballot box — pixel art."""
    im, g = px_canvas(96, 27, (255, 176, 110))
    # dusk bands: orange, checkerboard seam, purple, water
    for yy in range(8, 14):
        for xx in range(96):
            if (xx + yy) % 2 == 0:
                g.point((xx, yy), fill=(74, 52, 104))
    g.rectangle([0, 14, 96, 18], fill=(74, 52, 104))
    g.rectangle([0, 19, 96, 27], fill=(46, 64, 96))
    # sun, top right
    g.rectangle([79, 3, 83, 7], fill=(255, 214, 140))
    # skyline silhouettes
    for fx, fh, fw in [(0, 9, 10), (11, 11, 9), (21, 8, 10), (32, 15, 9),
                       (42, 10, 9), (52, 12, 10), (63, 9, 9), (73, 11, 10),
                       (84, 8, 12)]:
        g.rectangle([fx, 19 - fh, fx + fw, 19], fill=(42, 36, 56))
    # Bank of China: triangular top
    g.polygon([(38, 15), (43, 4), (48, 15)], fill=(42, 36, 56))
    g.rectangle([43, 4, 43, 15], fill=(255, 214, 140))
    # lit windows
    for wx, wy in [(5, 12), (14, 10), (24, 13), (35, 9), (46, 12), (56, 10),
                   (66, 13), (76, 11), (88, 12), (18, 15), (58, 15), (80, 15)]:
        g.point((wx, wy), fill=(255, 214, 140))
    # water glints
    for wx in (10, 34, 58, 82):
        g.rectangle([wx, 25, wx + 7, 25], fill=(255, 214, 140))
    # ballot box, front right
    g.rectangle([69, 15, 82, 24], fill=(245, 242, 235), outline=(120, 110, 95))
    g.rectangle([72, 16, 79, 16], fill=INK)
    for i in range(8):
        g.point((77 + i, 8 + i), fill=RED)
    for i in range(10):
        g.point((82 + i, 15 - i), fill=RED)
    # turnout chip
    px_chip(g, 15, 2, "98.79%", (20, 20, 31))
    px_paste(d, box, im)


def paint_cricket(d, box):
    """Wellington: green outfield, pitch, stumps, bat and ball — pixel art."""
    im, g = px_canvas(96, 27, (58, 122, 66))
    g.ellipse([-10, -15, 106, 42], outline=(230, 235, 220))
    # pitch strip
    g.rectangle([29, 2, 67, 25], fill=(196, 172, 120))
    g.rectangle([29, 2, 29, 25], fill=(245, 242, 235))
    g.rectangle([67, 2, 67, 25], fill=(245, 242, 235))
    # stumps + bails
    for dx in (0, 2, 4):
        g.rectangle([35 + dx, 6, 35 + dx, 13], fill=(240, 210, 90))
    g.rectangle([35, 5, 39, 5], fill=(240, 210, 90))
    # bat + ball
    g.polygon([(50, 9), (54, 8), (60, 17), (56, 18)], fill=(150, 105, 60))
    g.rectangle([51, 4, 52, 9], fill=(150, 105, 60))
    g.rectangle([65, 20, 67, 22], fill=(178, 34, 34))
    g.point((65, 20), fill=(255, 255, 255))
    # scoreboard chip top right
    px_chip(g, 96 - 3 - (px_text_w("720/9", FONT35) + 7), 2, "720/9",
            (20, 20, 31))
    px_text(g, 3, 23, "RECORD TOTAL", FONT35, (235, 235, 225))
    px_paste(d, box, im)


def paint_f1(d, box):
    """Las Vegas at night: Stratosphere, hotel blocks, track, car — pixel art."""
    im, g = px_canvas(96, 27, (12, 18, 40))
    g.rectangle([0, 10, 96, 18], fill=(30, 26, 52))
    # Stratosphere needle
    g.polygon([(10, 19), (11, 3), (13, 19)], fill=(30, 26, 52))
    g.rectangle([9, 2, 13, 4], fill=(255, 190, 90))
    # hotel blocks with lit windows
    for fx, fh, fw in [(19, 9, 13), (35, 7, 12), (48, 11, 15), (65, 8, 12),
                       (79, 10, 13)]:
        g.rectangle([fx, 19 - fh, fx + fw, 19], fill=(36, 30, 60))
        for wy in range(3):
            for wx in range(3):
                g.point((fx + 2 + wx * 4, 19 - fh + 2 + wy * 3),
                        fill=(255, 200, 110))
    # track
    g.rectangle([0, 19, 96, 27], fill=(52, 52, 58))
    g.rectangle([0, 23, 96, 23], fill=(240, 240, 235))
    for tx in range(0, 12):
        g.rectangle([tx * 8, 23, tx * 8 + 4, 23], fill=(240, 240, 235))
    # race car
    cx, cy = 50, 21
    g.rectangle([cx - 13, cy - 3, cx + 13, cy + 1], fill=(178, 34, 34))
    g.polygon([(cx - 15, cy - 4), (cx - 11, cy - 4), (cx - 10, cy - 2),
               (cx - 15, cy - 2)], fill=(120, 20, 20))
    g.rectangle([cx - 10, cy, cx - 5, cy + 4], fill=(15, 15, 18))
    g.rectangle([cx + 5, cy, cx + 10, cy + 4], fill=(15, 15, 18))
    g.rectangle([cx - 1, cy - 4, cx + 4, cy - 1], fill=(30, 30, 36))
    # checkered flag (shifted right so the wide pixel chip clears it)
    fx0, fy0 = 85, 3
    for r in range(3):
        for c in range(4):
            if (r + c) % 2 == 0:
                g.rectangle([fx0 + c * 2, fy0 + r * 2,
                             fx0 + c * 2 + 1, fy0 + r * 2 + 1],
                            fill=(20, 20, 20))
    g.rectangle([fx0, fy0, fx0, fy0 + 11], fill=(220, 220, 215))
    # chip
    px_chip(g, 15, 2, "35 LEAD CHANGES", (20, 20, 31))
    px_paste(d, box, im)


def paint_tennis(d, box):
    """Turin: blue court, net, ball, trophy — pixel art."""
    im, g = px_canvas(96, 27, (47, 111, 178))
    g.rectangle([4, 3, 92, 24], outline=(240, 240, 235))
    g.rectangle([4, 13, 92, 13], fill=(240, 240, 235))
    g.rectangle([31, 3, 31, 24], fill=(240, 240, 235))
    g.rectangle([65, 3, 65, 24], fill=(240, 240, 235))
    # net
    g.rectangle([4, 11, 92, 14], fill=(235, 235, 228))
    for nx in range(8, 88, 4):
        g.rectangle([nx, 11, nx, 14], fill=(120, 120, 115))
    g.rectangle([3, 10, 5, 15], fill=(30, 30, 34))
    g.rectangle([91, 10, 93, 15], fill=(30, 30, 34))
    # ball
    g.ellipse([20, 5, 26, 11], fill=(204, 255, 0), outline=(255, 255, 255))
    g.point((23, 5), fill=(255, 255, 255))
    g.point((23, 11), fill=(255, 255, 255))
    # trophy
    tx, ty = 79, 17
    g.polygon([(tx - 5, ty - 6), (tx + 5, ty - 6), (tx + 3, ty + 1),
               (tx - 3, ty + 1)], fill=(212, 175, 55))
    g.rectangle([tx - 7, ty - 6, tx - 5, ty - 2], fill=(212, 175, 55))
    g.rectangle([tx + 5, ty - 6, tx + 7, ty - 2], fill=(212, 175, 55))
    g.rectangle([tx, ty + 1, tx, ty + 5], fill=(212, 175, 55))
    g.rectangle([tx - 4, ty + 5, tx + 4, ty + 7], fill=(212, 175, 55))
    px_text(g, 3, 23, "MAIDEN TITLE", FONT35, (235, 235, 225))
    px_paste(d, box, im)


def paint_football(d, box):
    """Anfield: green pitch, goal, ball, 4-0 — pixel art."""
    im, g = px_canvas(96, 27, (46, 125, 62))
    g.rectangle([3, 2, 93, 25], outline=(240, 240, 235))
    g.rectangle([48, 2, 48, 25], fill=(240, 240, 235))
    g.ellipse([42, 8, 54, 20], outline=(240, 240, 235))
    g.rectangle([3, 8, 25, 19], outline=(240, 240, 235))
    g.rectangle([71, 8, 93, 19], outline=(240, 240, 235))
    # goal + net
    gx0, gy0 = 75, 8
    g.rectangle([gx0, gy0, gx0 + 15, gy0 + 10], outline=(255, 255, 255))
    for i in range(1, 4):
        g.rectangle([gx0 + i * 4, gy0, gx0 + i * 4, gy0 + 10],
                    fill=(220, 220, 215))
        g.rectangle([gx0, gy0 + i * 3, gx0 + 15, gy0 + i * 3],
                    fill=(220, 220, 215))
    # ball
    g.ellipse([37, 14, 43, 20], fill=(250, 250, 245), outline=(30, 30, 30))
    g.rectangle([39, 16, 41, 18], fill=(30, 30, 30))
    # scoreboard chip
    px_chip(g, 15, 2, "4–0", (20, 20, 31))
    px_paste(d, box, im)


def paint_manipur(d, box):
    """Manipur: pixel map of NE India, Imphal ring, hospital crosses — pixel art."""
    im, g = px_canvas(96, 27, (185, 210, 226))
    # NE India landmass (lon 91-98, lat 22-29), simplified low-res shape
    g.polygon([(8, 4), (30, 2), (60, 5), (88, 3), (93, 12), (85, 20),
               (60, 24), (30, 25), (12, 22), (4, 12)], fill=(224, 211, 178))
    # darker hill patch for texture
    g.polygon([(40, 8), (55, 7), (62, 12), (55, 16), (42, 15)],
              fill=(205, 192, 158))
    # Imphal ring + dot (93.9E, 24.8N)
    g.ellipse([36, 12, 44, 20], outline=RED)
    g.rectangle([39, 15, 40, 16], fill=RED)
    # hospital crosses
    for cx, cy in [(29, 9), (53, 17), (69, 8)]:
        g.rectangle([cx, cy - 2, cx, cy + 2], fill=RED)
        g.rectangle([cx - 2, cy, cx + 2, cy], fill=RED)
    # toll chip
    px_chip(g, 15, 2, "17 DEAD", RED)
    px_paste(d, box, im)


def paint_cikande(d, box):
    """Cikande: factory, sawtooth roof, flames, smoke — pixel art."""
    im, g = px_canvas(96, 27, (200, 195, 185))
    # sky bands: dusk grey top, pale bottom, checkerboard seam
    g.rectangle([0, 0, 96, 12], fill=(140, 150, 165))
    for xx in range(96):
        if xx % 2 == 0:
            g.point((xx, 12), fill=(200, 195, 185))
    # smoke puffs
    for cx, cy, r in [(29, 5, 5), (35, 3, 6), (42, 6, 4), (60, 4, 5), (67, 6, 4)]:
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(110, 112, 118))
        g.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2],
                  fill=(140, 142, 148))
    # factory body + sawtooth roof + chimney
    g.rectangle([4, 13, 92, 24], fill=(138, 141, 144))
    for i in range(5):
        sx = 4 + i * 16
        g.polygon([(sx, 13), (sx + 8, 8), (sx + 16, 13)], fill=(110, 113, 116))
    g.rectangle([79, 5, 83, 24], fill=(100, 102, 105))
    # windows: 3 rows x 6 cols (third row clips below the box, as before)
    for wy in range(3):
        for wx in range(6):
            g.rectangle([8 + wx * 14, 15 + wy * 6, 10 + wx * 14, 17 + wy * 6],
                        fill=(255, 205, 110))
    # flames from the roof
    for cx in (24, 43, 62):
        g.polygon([(cx - 3, 13), (cx, 7), (cx + 2, 12), (cx + 4, 8), (cx + 5, 13)],
                  fill=(255, 150, 50))
        g.polygon([(cx - 1, 13), (cx, 10), (cx + 2, 13)], fill=(255, 220, 90))
    # casualty chip: the string is too long for one pixel line, so it stacks
    px_chip2(g, 17, 2, "3 DEAD", "36 MISSING", RED)
    px_paste(d, box, im)


def paint_sparta(d, box):
    """Sparta II: sea, burning ship, containers, lifeboat — pixel art.

    The old smooth version hid the stern flame and smoke behind the chip
    and the first container; here both sit at the stern, left of the chip,
    so the fire reads."""
    im, g = px_canvas(96, 27, (52, 96, 130))
    g.rectangle([0, 0, 96, 13], fill=(120, 165, 195))
    for xx in range(96):
        if xx % 2 == 0:
            g.point((xx, 13), fill=(52, 96, 130))
    # waves
    for wy in (15, 18, 22, 25):
        for wx in (5, 29, 53, 77):
            g.point((wx - 2, wy), fill=(220, 235, 245))
            g.point((wx - 1, wy + 1), fill=(220, 235, 245))
            g.point((wx, wy + 1), fill=(220, 235, 245))
            g.point((wx + 1, wy + 1), fill=(220, 235, 245))
            g.point((wx + 2, wy), fill=(220, 235, 245))
    # smoke + flame at the stern
    for cx, cy, r in [(11, 5, 4), (14, 2, 4), (9, 2, 3)]:
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(105, 108, 114))
    g.polygon([(10, 15), (12, 8), (13, 12), (14, 9), (15, 15)],
              fill=(255, 150, 50))
    g.polygon([(11, 15), (12, 11), (14, 15)], fill=(255, 220, 90))
    # hull + name + containers + bridge
    g.polygon([(8, 17), (88, 17), (83, 22), (13, 22)], fill=(40, 44, 52))
    px_text(g, 31, 18, "SPARTA II", FONT35, (240, 240, 235))
    for i, col in enumerate([(178, 84, 44), (52, 96, 150), (90, 140, 70),
                             (178, 84, 44)]):
        g.rectangle([15 + i * 16, 10, 28 + i * 16, 16], fill=col,
                    outline=(30, 30, 34))
    g.rectangle([79, 4, 86, 16], fill=(235, 235, 230))
    g.rectangle([81, 1, 84, 4], fill=(178, 34, 34))
    # lifeboat
    g.polygon([(55, 23), (64, 23), (63, 25), (56, 25)], fill=(255, 140, 40))
    # chip
    px_chip(g, 15, 2, "16 SAFE", (46, 139, 87))
    px_paste(d, box, im)


def paint_tehran(d, box):
    """Tehran at dusk: Milad Tower, skyline, lightbulb — pixel art."""
    im, g = px_canvas(96, 27, (255, 150, 80))
    # dusk bands: purple top, orange bottom, checkerboard seam
    g.rectangle([0, 0, 96, 12], fill=(88, 66, 122))
    for xx in range(96):
        if xx % 2 == 0:
            g.point((xx, 12), fill=(255, 150, 80))
    # Milad Tower
    g.polygon([(60, 24), (64, 4), (66, 4), (70, 24)], fill=(52, 44, 66))
    g.ellipse([58, 5, 72, 11], fill=(72, 60, 88))
    g.rectangle([63, 2, 67, 4], fill=(255, 190, 90))
    # skyline
    for fx, fh, fw in [(0, 8, 12), (12, 11, 10), (23, 9, 12), (36, 13, 12),
                       (50, 10, 10), (75, 12, 12), (86, 9, 10)]:
        g.rectangle([fx, 24 - fh, fx + fw, 24], fill=(48, 40, 60))
    # one lit window
    g.rectangle([38, 15, 40, 16], fill=(255, 210, 110))
    # lightbulb, top left
    bx, by = 13, 6
    g.ellipse([bx - 3, by - 4, bx + 3, by + 3], outline=(255, 235, 180))
    g.rectangle([bx - 1, by + 3, bx + 1, by + 4], fill=(255, 235, 180))
    g.rectangle([bx - 1, by + 5, bx + 1, by + 5], fill=(255, 235, 180))
    g.point((bx - 3, by - 6), fill=(255, 235, 180))
    g.point((bx + 3, by - 6), fill=(255, 235, 180))
    g.point((bx, by - 7), fill=(255, 235, 180))
    # chip (starts at 43: the pixel chip is wider than the old smooth one)
    px_chip(g, 43, 2, "UP TO 2 HRS", (20, 20, 31))
    px_paste(d, box, im)


def paint_gaza(d, box):
    """Gaza coast: sea, sand, strip outline, aid truck — pixel art."""
    im, g = px_canvas(96, 27, (224, 211, 178))
    # sea left, coastline diagonal
    g.polygon([(0, 0), (40, 0), (29, 27), (0, 27)], fill=(146, 186, 214))
    g.line([(40, 0), (29, 27)], fill=(240, 240, 235), width=1)
    # Gaza strip outline (thin coastal strip)
    g.polygon([(42, 2), (54, 2), (48, 25), (37, 25)], outline=RED)
    px_text(g, 56, 3, "GAZA", FONT35, INK_SOFT)
    # aid truck on the road
    tx, ty = 50, 18
    g.rectangle([tx, ty - 6, tx + 17, ty + 1], fill=(245, 245, 240),
                outline=(120, 120, 115))
    g.rectangle([tx + 17, ty - 4, tx + 22, ty + 1], fill=(200, 205, 210),
                outline=(120, 120, 115))
    g.rectangle([tx + 7, ty - 5, tx + 10, ty - 2], fill=RED)
    g.rectangle([tx + 8, ty - 6, tx + 9, ty - 1], fill=RED)
    g.rectangle([tx + 3, ty, tx + 5, ty + 3], fill=(20, 20, 24))
    g.rectangle([tx + 13, ty, tx + 15, ty + 3], fill=(20, 20, 24))
    g.rectangle([tx + 19, ty, tx + 21, ty + 3], fill=(20, 20, 24))
    # chip
    px_chip(g, 15, 2, "3 KILLED", RED)
    px_paste(d, box, im)


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
    # region bar
    labels = []
    for name, n, col in REGIONS:
        labels.append((name, n, col, tracked_w(d, "%s %d" % (name, n), IN(9), 1.0) + 14))
    total = 992
    raw = [max(lw, total * n / 42.0) for _, n, _, lw in labels]
    scale = total / sum(raw)
    widths = [r * scale for r in raw]
    x = 16
    for (name, n, col, _), wd in zip(labels, widths):
        d.rectangle([x, 122, x + wd, 142], fill=col)
        draw_tracked_c(d, x + wd / 2, 128, "%s %d" % (name, n), IN(9),
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
    # map + index header
    draw_tracked(d, 16, 800, "ALSO ON SUNDAY 22 NOVEMBER", IN(11), INK, 1.2)
    rw = tracked_w(d, "29 MORE STORIES · NUMBERS 14–42 · DOTS ON THE MAP", IN(8), 0.8)
    draw_tracked(d, 1008 - rw, 801, "29 MORE STORIES · NUMBERS 14–42 · DOTS ON THE MAP",
                 IN(8), GREY, 0.8)
    # map
    mapbox = (16, 816, 396, 954)
    d.rectangle(mapbox, fill=SEA)
    # project with lat range -60..85 so Antarctica stays out
    def proj2(lon, lat):
        x0, y0, x1, y1 = mapbox
        return (x0 + (lon + 180.0) / 360.0 * (x1 - x0),
                y0 + (85.0 - lat) / 145.0 * (y1 - y0))
    for ring in POLYS:
        pts = []
        prev_lon = None
        for lon, lat in ring:
            if prev_lon is not None and abs(lon - prev_lon) > 180:
                if len(pts) >= 3:
                    d.polygon(pts, fill=LAND)
                pts = []
            pts.append(proj2(lon, lat))
            prev_lon = lon
        if len(pts) >= 3:
            d.polygon(pts, fill=LAND)
    d.rectangle(mapbox, outline=INK, width=1)
    # pins: cards 1-13 big, index 14-42 small
    pins = []
    pins.append((1, LEAD["lon"], LEAD["lat"], RCOL[LEAD["region"]], True))
    for s in CARDS:
        pins.append((s["num"], s["lon"], s["lat"], RCOL[s["region"]], True))
    for num, city, region, head, src, lon, lat in INDEX:
        pins.append((num, lon, lat, RCOL[region], False))
    # de-collision in projected space
    placed, final = [], []
    for num, lon, lat, col, big in pins:
        x, y = proj2(lon, lat)
        r = 7 if big else 5
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
        r = 7 if big else 5
        num_disc(d, x, y, r, col, num, 8 if big else 7)
    d.text((20, 938), "Big dots 1–13 · small dots 14–42", font=PT(8, "Italic"),
           fill=(60, 70, 80))
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
