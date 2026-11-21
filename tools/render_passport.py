#!/usr/bin/env python3
"""Render the Meridia passport spread (1024x1024 PNG) with Pillow.

The entry program (main.py, stdlib only) copies the rendered PNG to
/output/entry.png. This renderer is a build-time tool; it runs on the
builder machine, never in the grading sandbox.

Design: an open passport of the invented Republic of Meridia.
Left page = data page (photo, personal data, MRZ with real check digits).
Right page = visa sticker + six entry/exit stamps + a quarantine notice.
Every date is internally consistent: passport issued 12 MAR 2024, all
stamps after that, visa issued 18 JAN 2025, expiry 12 MAR 2034.
Deterministic: no randomness, no clock, no network.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "assets", "passport.png")

W = H = 1024

# ---------- palette ----------
INK = (26, 42, 58)          # deep navy ink
NAVY = (31, 58, 86)
GOLD = (176, 141, 62)
IVORY = (246, 241, 229)
PAGE_R = (220, 235, 230)    # pale aqua visa page
GREY = (96, 104, 110)
DESK1 = (38, 54, 63)
DESK2 = (24, 36, 44)

FD = "/usr/share/fonts/truetype/dejavu"
FL = "/usr/share/fonts/truetype/liberation"


def font(path, size):
    return ImageFont.truetype(path, size)


SERIF = os.path.join(FD, "DejaVuSerif.ttf")
SERIF_B = os.path.join(FD, "DejaVuSerif-Bold.ttf")
SERIF_I = os.path.join(FL, "LiberationSerif-Italic.ttf")
SANS = os.path.join(FD, "DejaVuSans.ttf")
SANS_B = os.path.join(FD, "DejaVuSans-Bold.ttf")
MONO = os.path.join(FD, "DejaVuSansMono.ttf")
MONO_B = os.path.join(FD, "DejaVuSansMono-Bold.ttf")


def tracked(draw, xy, text, fnt, fill, tracking=0, anchor="la"):
    """Draw text with letter tracking (px added between glyphs)."""
    x, y = xy
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if anchor in ("ma", "mm", "mt"):
        x -= total / 2
    elif anchor in ("ra", "rm", "rt"):
        x -= total
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total


def text_c(draw, cx, y, text, fnt, fill, tracking=0):
    tracked(draw, (cx, y), text, fnt, fill, tracking, anchor="ma")


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------- MRZ (ICAO Doc 9303, real check digits) ----------
def cd_value(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55  # A=10 .. Z=35


def check_digit(s):
    weights = (7, 3, 1)
    return str(sum(cd_value(c) * weights[i % 3] for i, c in enumerate(s)) % 10)


def mrz_lines():
    doc = "MD8472916"
    dob = "960614"   # 14 JUN 1996
    exp = "340312"   # 12 MAR 2034
    line1 = "P<MDIVOSS<<ELARA<MIREN"
    line1 = line1 + "<" * (44 - len(line1))
    opt = "<" * 15
    core = doc + check_digit(doc) + "MDI" + dob + check_digit(dob) + "F" + exp + check_digit(exp)
    line2 = core + opt
    line2 += check_digit(doc + check_digit(doc) + dob + check_digit(dob)
                         + exp + check_digit(exp) + opt)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# ---------- guilloche ----------
def guilloche(draw, box, color, amp=5, step=9, waves=2):
    x0, y0, x1, y1 = box
    for k in range(waves):
        pts = []
        y = y0 + 8 + k * ((y1 - y0 - 16) // max(waves - 1, 1)) if waves > 1 else (y0 + y1) // 2
        for x in range(x0, x1 + 1, 4):
            pts.append((x, y + amp * math.sin((x - x0) / 26.0 + k * 1.7)))
        draw.line(pts, fill=color, width=1)
    for k in range(waves):
        pts = []
        x = x0 + 8 + k * ((x1 - x0 - 16) // max(waves - 1, 1)) if waves > 1 else (x0 + x1) // 2
        for y in range(y0, y1 + 1, 4):
            pts.append((x + amp * math.sin((y - y0) / 26.0 + k * 1.7), y))
        draw.line(pts, fill=color, width=1)


# ---------- emblem: lighthouse in a compass ring ----------
def emblem(draw, cx, cy, r, color, width=3):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)
    draw.ellipse([cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7], outline=color, width=1)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        x0 = cx + (r - 12) * math.cos(a)
        y0 = cy + (r - 12) * math.sin(a)
        x1 = cx + (r - 4) * math.cos(a)
        y1 = cy + (r - 4) * math.sin(a)
        draw.line([x0, y0, x1, y1], fill=color, width=2)
    # lighthouse tower
    tw = r * 0.30
    draw.polygon([(cx - tw, cy + r * 0.55), (cx - tw * 0.62, cy - r * 0.28),
                  (cx + tw * 0.62, cy - r * 0.28), (cx + tw, cy + r * 0.55)],
                 outline=color, width=2)
    draw.line([cx - tw * 0.62, cy - r * 0.05, cx + tw * 0.62, cy - r * 0.05], fill=color, width=2)
    draw.line([cx - tw * 0.62, cy + r * 0.22, cx + tw * 0.62, cy + r * 0.22], fill=color, width=2)
    # lamp room + light rays
    draw.rectangle([cx - tw * 0.42, cy - r * 0.52, cx + tw * 0.42, cy - r * 0.28],
                   outline=color, width=2)
    draw.line([cx - tw * 0.42, cy - r * 0.62, cx + tw * 0.42, cy - r * 0.62], fill=color, width=2)
    for s in (-1, 1):
        draw.line([cx + s * tw * 0.5, cy - r * 0.40, cx + s * (r - 10), cy - r * 0.52],
                  fill=color, width=1)
    # waves
    for k, wy in enumerate((r * 0.62, r * 0.76)):
        pts = [(cx - r * 0.72 + i * 3, cy + wy + 3 * math.sin(i / 3.0 + k))
               for i in range(int(r * 0.48))]
        draw.line(pts, fill=color, width=2)


# ---------- flat portrait ----------
def portrait(size):
    w, h = size
    img = Image.new("RGB", (w, h), (94, 138, 130))
    d = ImageDraw.Draw(img)
    # backdrop halo
    d.ellipse([w * 0.12, h * 0.04, w * 0.88, h * 0.78], fill=(126, 168, 160))
    d.ellipse([w * 0.20, h * 0.10, w * 0.80, h * 0.70], fill=(148, 186, 178))
    skin = (232, 184, 143)
    skin_d = (214, 164, 122)
    hair = (58, 42, 34)
    # shoulders / jacket
    d.polygon([(w * 0.06, h), (w * 0.16, h * 0.82), (w * 0.38, h * 0.72),
               (w * 0.62, h * 0.72), (w * 0.84, h * 0.82), (w * 0.94, h)],
              fill=(38, 54, 74))
    # shirt + collar
    d.polygon([(w * 0.42, h * 0.74), (w * 0.50, h * 0.84), (w * 0.58, h * 0.74),
               (w * 0.56, h), (w * 0.44, h)], fill=(240, 236, 224))
    d.polygon([(w * 0.42, h * 0.74), (w * 0.50, h * 0.80), (w * 0.44, h * 0.86)],
              fill=(214, 208, 192))
    d.polygon([(w * 0.58, h * 0.74), (w * 0.50, h * 0.80), (w * 0.56, h * 0.86)],
              fill=(214, 208, 192))
    # neck
    d.rectangle([w * 0.44, h * 0.60, w * 0.56, h * 0.76], fill=skin_d)
    # hair back (ends above the chin so it never reads as a beard)
    d.ellipse([w * 0.25, h * 0.05, w * 0.75, h * 0.56], fill=hair)
    # face (narrower than the hair mass)
    d.ellipse([w * 0.34, h * 0.13, w * 0.66, h * 0.60], fill=skin)
    # fringe + side strands
    d.pieslice([w * 0.30, h * 0.07, w * 0.70, h * 0.40], 180, 360, fill=hair)
    d.polygon([(w * 0.335, h * 0.22), (w * 0.375, h * 0.14), (w * 0.385, h * 0.30)],
              fill=hair)
    d.polygon([(w * 0.31, h * 0.30), (w * 0.345, h * 0.28), (w * 0.345, h * 0.52),
               (w * 0.325, h * 0.55)], fill=hair)
    d.polygon([(w * 0.69, h * 0.30), (w * 0.655, h * 0.28), (w * 0.655, h * 0.52),
               (w * 0.675, h * 0.55)], fill=hair)
    # brows
    d.line([w * 0.40, h * 0.335, w * 0.46, h * 0.328], fill=hair, width=3)
    d.line([w * 0.54, h * 0.328, w * 0.60, h * 0.335], fill=hair, width=3)
    # eyes (smaller, calmer)
    for ex in (0.43, 0.57):
        d.ellipse([w * (ex - 0.018), h * 0.355, w * (ex + 0.018), h * 0.378],
                  fill=(255, 255, 255))
        d.ellipse([w * (ex - 0.010), h * 0.360, w * (ex + 0.010), h * 0.376],
                  fill=(40, 32, 28))
    # nose
    d.line([w * 0.50, h * 0.395, w * 0.496, h * 0.465, w * 0.514, h * 0.470],
           fill=skin_d, width=2)
    # lips
    d.polygon([(w * 0.468, h * 0.515), (w * 0.50, h * 0.506), (w * 0.532, h * 0.515),
               (w * 0.50, h * 0.534)], fill=(176, 96, 84))
    d.line([w * 0.472, h * 0.518, w * 0.528, h * 0.518], fill=(140, 70, 60), width=1)
    # earring
    d.ellipse([w * 0.325, h * 0.485, w * 0.342, h * 0.502], fill=(212, 175, 105))
    return img


# ---------- entry/exit stamp ----------
def stamp(kind, place, date, color, angle):
    """One ink entry/exit stamp on its own layer, rotated."""
    w, h = 200, 92
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = 20, 20, 20 + w, 20 + h
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=color, width=3)
    d.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=6, outline=color, width=1)
    text_c(d, (x0 + x1) // 2, y0 + 8, kind, font(SANS_B, 17), color, tracking=3)
    text_c(d, (x0 + x1) // 2, y0 + 32, place, font(SERIF_B, 15), color, tracking=1)
    text_c(d, (x0 + x1) // 2, y0 + 58, date, font(SANS_B, 14), color, tracking=2)
    # small star
    cx, cy = x0 + 16, y0 + 16
    d.text((cx - 5, cy - 8), "\u2605", font=font(SANS, 13), fill=color)
    return layer.rotate(angle, resample=Image.BICUBIC, expand=False)


def circular_stamp(text_top, text_mid, text_bot, color, angle, size=92):
    layer = Image.new("RGBA", (size + 30, size + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = cy = (size + 30) // 2
    r = size // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], outline=color, width=1)
    text_c(d, cx, cy - r + 12, text_top, font(SANS_B, 10), color, tracking=1)
    text_c(d, cx, cy - 8, text_mid, font(SERIF_B, 15), color)
    text_c(d, cx, cy + r - 24, text_bot, font(SANS_B, 10), color, tracking=1)
    return layer.rotate(angle, resample=Image.BICUBIC, expand=False)


# ---------- visa sticker ----------
def visa_sticker():
    w, h = 372, 168
    layer = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = 15, 15, 15 + w, 15 + h
    d.rectangle([x0, y0, x1, y1], fill=(250, 246, 220), outline=(46, 110, 72), width=3)
    d.rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], outline=(46, 110, 72), width=1)
    d.rectangle([x0, y0, x1, y0 + 34], fill=(46, 110, 72))
    text_c(d, (x0 + x1) // 2, y0 + 8, "KESTREL ISLES  \u2014  VISITOR VISA",
           font(SANS_B, 15), (250, 246, 220), tracking=1)
    f_lab = font(SANS, 11)
    f_val = font(SANS_B, 13)
    rows = [("TYPE", "SINGLE ENTRY \u2014 30 DAYS"),
            ("ISSUED", "18 JAN 2025 \u00b7 PORT AURELINE"),
            ("VISA No.", "KI-2025-0117")]
    y = y0 + 46
    for lab, val in rows:
        d.text((x0 + 14, y), lab, font=f_lab, fill=(96, 104, 110))
        d.text((x0 + 96, y - 1), val, font=f_val, fill=(26, 42, 58))
        y += 24
    d.text((x0 + 14, y + 2), "CONDITION: NO FISHING IN PROTECTED WATERS.",
           font=font(SANS, 10), fill=(140, 60, 50))
    # small seal
    d.ellipse([x1 - 66, y1 - 62, x1 - 16, y1 - 12], outline=(46, 110, 72), width=2)
    text_c(d, x1 - 41, y1 - 52, "KI", font(SERIF_B, 15), (46, 110, 72))
    return layer.rotate(-3, resample=Image.BICUBIC, expand=False)


# ---------- pages ----------
def build():
    img = Image.new("RGB", (W, H), DESK2)
    d = ImageDraw.Draw(img, "RGBA")
    # desk gradient
    for y in range(H):
        t = y / H
        c = tuple(int(DESK1[i] + (DESK2[i] - DESK1[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    # faint desk speckles (fixed pattern, deterministic)
    for i in range(240):
        x = (i * 379) % W
        y = (i * 613) % H
        d.ellipse([x, y, x + 2, y + 2], fill=(255, 255, 255, 6))

    # soft shadow under the spread
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([60, 184, 978, 864], radius=8, fill=(0, 0, 0, 130))
    img.paste(Image.alpha_composite(img.convert("RGBA"),
                                    shadow.filter(ImageFilter.GaussianBlur(10)).convert("RGBA")).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # pages
    left = Image.new("RGB", (460, 680), IVORY)
    right = Image.new("RGB", (460, 680), PAGE_R)
    ld, rd = ImageDraw.Draw(left, "RGBA"), ImageDraw.Draw(right, "RGBA")

    # ===== LEFT PAGE: data page =====
    guilloche(ld, (24, 240, 436, 656), (120, 140, 160, 26))
    ld.rectangle([14, 14, 446, 666], outline=GOLD, width=2)
    ld.rectangle([20, 20, 440, 660], outline=(176, 141, 62, 120), width=1)
    emblem(ld, 230, 72, 48, NAVY)
    text_c(ld, 230, 132, "REPUBLIC OF MERIDIA", font(SERIF_B, 25), NAVY, tracking=3)
    text_c(ld, 230, 164, "PASSPORT", font(SERIF_B, 42), INK, tracking=8)
    text_c(ld, 230, 212, "PASPORTA MERIDIANA", font(SANS, 12), GREY, tracking=5)
    ld.line([90, 238, 370, 238], fill=GOLD, width=2)
    ld.polygon([(230, 230), (238, 238), (230, 246), (222, 238)], fill=GOLD)

    f_lab = font(SANS, 10)
    f_val = font(SANS_B, 16)
    fields = [
        ("SURNAME", "VOSS"),
        ("GIVEN NAMES", "ELARA MIREN"),
        ("NATIONALITY", "MERIDIAN"),
        ("DATE OF BIRTH", "14 JUN 1996"),
        ("PLACE OF BIRTH", "AURELINE"),
    ]
    y = 258
    for lab, val in fields:
        ld.text((34, y), lab, font=f_lab, fill=GREY)
        ld.text((34, y + 13), val, font=f_val, fill=INK)
        y += 34
    # portrait
    ph = portrait((150, 196))
    left.paste(ph, (288, 258))
    ld.rectangle([288, 258, 438, 454], outline=NAVY, width=2)
    text_c(ld, 363, 458, "PHOTOGRAPH", font(SANS, 9), GREY, tracking=3)

    y = 478
    ld.text((34, y), "SEX", font=f_lab, fill=GREY)
    ld.text((34, y + 13), "F", font=f_val, fill=INK)
    ld.text((120, y), "DATE OF ISSUE", font=f_lab, fill=GREY)
    ld.text((120, y + 13), "12 MAR 2024", font=f_val, fill=INK)
    ld.text((288, y), "DATE OF EXPIRY", font=f_lab, fill=GREY)
    ld.text((288, y + 13), "12 MAR 2034", font=f_val, fill=INK)
    y = 526
    ld.text((34, y), "AUTHORITY", font=f_lab, fill=GREY)
    ld.text((34, y + 13), "PORT AURELINE", font=f_val, fill=INK)
    ld.text((288, y), "PASSPORT No.", font=f_lab, fill=GREY)
    ld.text((288, y + 13), "MD 847 2916", font=f_val, fill=INK)
    # signature
    ld.text((34, 574), "HOLDER'S SIGNATURE", font=f_lab, fill=GREY)
    ld.text((34, 584), "Elara Voss", font=font(SERIF_I, 20), fill=(40, 60, 90))
    ld.line([34, 606, 220, 606], fill=(120, 120, 120), width=1)

    # MRZ
    l1, l2 = mrz_lines()
    ld.rectangle([24, 614, 436, 656], fill=(232, 226, 210))
    ld.text((30, 620), l1, font=font(MONO, 12), fill=INK)
    ld.text((30, 637), l2, font=font(MONO, 12), fill=INK)

    # ===== RIGHT PAGE: visas & stamps =====
    guilloche(rd, (24, 210, 436, 656), (90, 120, 110, 22))
    rd.rectangle([14, 14, 446, 666], outline=NAVY, width=2)
    rd.rectangle([20, 20, 440, 660], outline=(31, 58, 86, 110), width=1)
    text_c(rd, 230, 34, "VISAS", font(SERIF_B, 24), NAVY, tracking=6)
    text_c(rd, 230, 64, "VISA \u00b7 ENTRY \u00b7 EXIT STAMPS", font(SANS, 10), GREY, tracking=3)
    rd.line([90, 88, 370, 88], fill=GOLD, width=2)

    # visa sticker
    vs = visa_sticker()
    right.paste(vs, (44, 96), vs)

    # stamps (all after issue 12 MAR 2024; travel history in order)
    BLUE = (38, 84, 150, 235)
    PURPLE = (104, 70, 140, 235)
    REDBR = (150, 64, 48, 235)
    GREEN = (40, 110, 70, 235)
    stamps = [
        ("ARRIVAL", "DUNHARROW", "03 SEP 2024", BLUE, -7, (30, 296)),
        ("DEPARTURE", "DUNHARROW", "17 SEP 2024", BLUE, 6, (238, 296)),
        ("ARRIVAL", "KESTREL ISLES", "22 JAN 2025", PURPLE, 5, (30, 392)),
        ("ARRIVAL", "PORT OF SABLE", "09 JUN 2025", REDBR, -5, (238, 392)),
        ("DEPARTURE", "PORT OF SABLE", "24 JUN 2025", REDBR, 7, (30, 488)),
        ("ARRIVAL", "MERIDIA \u00b7 AURELINE", "25 JUN 2025", GREEN, -6, (238, 488)),
    ]
    for kind, place, date, color, ang, pos in stamps:
        st = stamp(kind, place, date, color, ang)
        right.paste(st, pos, st)

    # harbour-tax circular stamp in the freed bottom-right corner
    cs = circular_stamp("HARBOUR", "12 AUR", "TAX PAID", (150, 64, 48, 235), -12, size=84)
    right.paste(cs, (352, 570), cs)

    # notice: the telling detail (narrowed so the tax stamp has its own corner)
    rd.rectangle([30, 606, 330, 652], outline=(140, 60, 50), width=2)
    rd.rectangle([34, 610, 326, 648], outline=(140, 60, 50, 120), width=1)
    f_note = font(SANS, 10)
    note = ("NOTICE \u2014 This passport is not valid for travel to the Silent "
            "Isles. Quarantine in force since 2019.")
    for i, ln in enumerate(wrap(rd, note, f_note, 280)):
        rd.text((40, 614 + i * 13), ln, font=f_note, fill=(140, 60, 50))

    # paste pages onto desk
    img.paste(left, (52, 172))
    img.paste(right, (512, 172))
    # gutter shadow
    d.rectangle([508, 172, 516, 852], fill=(0, 0, 0, 60))
    d.line([510, 172, 510, 852], fill=(0, 0, 0, 90), width=2)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
