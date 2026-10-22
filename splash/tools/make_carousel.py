#!/usr/bin/env python3
"""Gera um carrossel 4:5 (1080x1350) JPEG a partir de um JSON de slides.

Uso: python3 make_carousel.py spec.json pasta_saida/ prefixo
  -> pasta_saida/prefixo_01.jpg, prefixo_02.jpg, ...

Formato do spec:
{
  "slides": [
    {"type": "hook", "title": "...", "sub": "..."},
    {"type": "list", "label": "ENTRA", "icon": "check|x|dot", "items": [["título", "nota"], ...]},
    {"type": "text", "label": "...", "title": "...", "sub": "..."},
    {"type": "cta",  "title": "Comenta CHECKLIST", "sub": "..."}
  ]
}
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
TURQ = (18, 104, 196)
TURQ_DARK = (7, 56, 128)
INK = (8, 28, 64)
GREY = (84, 100, 128)
WHITE = (255, 255, 255)
SOFT = (226, 240, 255)
RED = (214, 69, 69)
FD = "/usr/share/fonts/opentype/inter/"


def font(name, size):
    return ImageFont.truetype(FD + name, size)


F_BLACK = lambda s: font("InterDisplay-Black.otf", s)
F_BOLD = lambda s: font("Inter-Bold.otf", s)
F_SEMI = lambda s: font("Inter-SemiBold.otf", s)
F_MED = lambda s: font("Inter-Medium.otf", s)


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def centered(d, lines, f, y, fill, lh):
    for ln in lines:
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=fill)
        y += lh
    return y


def bg(idx, total):
    img = Image.new("RGB", (W, H), TURQ)
    grad = Image.linear_gradient("L").resize((W, H)).rotate(12, expand=False)
    img = Image.composite(Image.new("RGB", (W, H), TURQ_DARK), img, grad.point(lambda p: int(p * 0.35)))
    d = ImageDraw.Draw(img)
    # indicador de slides (bolinhas) no topo
    n = total; r = 7; gap = 26
    x0 = (W - (n * 2 * r + (n - 1) * gap)) / 2
    for i in range(n):
        x = x0 + i * (2 * r + gap)
        d.ellipse((x, 70, x + 2 * r, 70 + 2 * r), fill=WHITE if i == idx else (255, 255, 255, 90), outline=WHITE, width=2)
    return img


def tag(d, text, y):
    f = F_BOLD(36)
    tw = d.textlength(text, font=f) + 70
    d.rounded_rectangle(((W - tw) / 2, y, (W + tw) / 2, y + 74), 37, fill=WHITE)
    d.text(((W - tw) / 2 + 35, y + 16), text, font=f, fill=TURQ_DARK)
    return y + 74


def icon(d, kind, x, y, s=44):
    if kind == "check":
        d.rounded_rectangle((x, y, x + s, y + s), 12, fill=SOFT)
        d.line([(x + 11, y + s / 2 + 2), (x + s / 2 - 3, y + s - 12), (x + s - 9, y + 11)], fill=TURQ_DARK, width=6, joint="curve")
    elif kind == "x":
        d.rounded_rectangle((x, y, x + s, y + s), 12, fill=(253, 232, 232))
        d.line([(x + 12, y + 12), (x + s - 12, y + s - 12)], fill=RED, width=6)
        d.line([(x + s - 12, y + 12), (x + 12, y + s - 12)], fill=RED, width=6)
    else:
        d.ellipse((x + 12, y + 12, x + s - 12, y + s - 12), fill=TURQ)


def slide_hook(s, idx, total):
    img = bg(idx, total); d = ImageDraw.Draw(img)
    f = F_BLACK(104)
    lines = wrap(d, s["title"], f, 940)
    lh = 112
    y0 = (H - len(lines) * lh) / 2 - 60
    y = centered(d, lines, f, y0, WHITE, lh)
    if s.get("sub"):
        fs = F_SEMI(44)
        tw = d.textlength(s["sub"], font=fs) + 80
        d.rounded_rectangle(((W - tw) / 2, y + 40, (W + tw) / 2, y + 128), 44, fill=WHITE)
        d.text(((W - tw) / 2 + 40, y + 60), s["sub"], font=fs, fill=INK)
    # seta "arrasta"
    fa = F_MED(34)
    d.text(((W - d.textlength("arrasta  →", font=fa)) / 2, H - 130), "arrasta  →", font=fa, fill=SOFT)
    return img


def slide_list(s, idx, total):
    img = bg(idx, total); d = ImageDraw.Draw(img)
    items = s["items"]
    pad = 56
    ft, fn = F_BOLD(46), F_MED(33)
    # mede altura
    rows = []
    for it in items:
        title, note = (it + [""])[:2] if isinstance(it, list) else (it, "")
        tl = wrap(d, title, ft, W - 2 * pad - 2 * 60 - 60)
        nl = wrap(d, note, fn, W - 2 * pad - 2 * 60 - 60) if note else []
        rows.append((tl, nl))
    hrow = lambda r: len(r[0]) * 54 + len(r[1]) * 42 + 36
    total_h = sum(hrow(r) for r in rows) + 2 * pad - 36
    foot_h = 110 if s.get("foot") else 0
    block = 74 + 50 + total_h + foot_h
    y = tag(d, s["label"], max(130, (H - block) / 2))
    top = y + 50
    d.rounded_rectangle((60, top, W - 60, top + total_h), 44, fill=WHITE)
    yy = top + pad
    for r in rows:
        icon(d, s.get("icon", "check"), 60 + pad, yy + 6)
        x = 60 + pad + 44 + 30
        for ln in r[0]:
            d.text((x, yy), ln, font=ft, fill=INK); yy += 54
        for ln in r[1]:
            d.text((x, yy), ln, font=fn, fill=GREY); yy += 42
        yy += 36
    if s.get("foot"):
        ff = F_SEMI(34)
        centered(d, wrap(d, s["foot"], ff, 900), ff, top + total_h + 40, SOFT, 44)
    return img


def slide_text(s, idx, total):
    img = bg(idx, total); d = ImageDraw.Draw(img)
    y = 200
    if s.get("label"):
        y = tag(d, s["label"], 150) + 60
    f = F_BLACK(84)
    lines = wrap(d, s["title"], f, 920)
    y = centered(d, lines, f, max(y, (H - len(lines) * 94) / 2 - 120), WHITE, 94)
    if s.get("sub"):
        fs = F_MED(42)
        centered(d, wrap(d, s["sub"], fs, 880), fs, y + 40, SOFT, 54)
    return img


def slide_cta(s, idx, total):
    img = bg(idx, total); d = ImageDraw.Draw(img)
    f = F_BLACK(110)
    lines = wrap(d, s["title"], f, 940)
    y = centered(d, lines, f, 330, WHITE, 118)
    if s.get("sub"):
        fs = F_MED(44)
        y = centered(d, wrap(d, s["sub"], fs, 860), fs, y + 50, SOFT, 56)
    if s.get("save"):
        fb = F_SEMI(40)
        tw = d.textlength(s["save"], font=fb) + 90
        d.rounded_rectangle(((W - tw) / 2, y + 80, (W + tw) / 2, y + 170), 45, fill=WHITE)
        d.text(((W - tw) / 2 + 45, y + 101), s["save"], font=fb, fill=TURQ_DARK)
    return img


R = {"hook": slide_hook, "list": slide_list, "text": slide_text, "cta": slide_cta}


def main(spec_path, out_dir, prefix):
    spec = json.load(open(spec_path))
    slides = spec["slides"]
    os.makedirs(out_dir, exist_ok=True)
    outs = []
    for i, s in enumerate(slides):
        img = R[s["type"]](s, i, len(slides))
        p = os.path.join(out_dir, f"{prefix}_{i+1:02d}.jpg")
        img.save(p, quality=92, subsampling=0)
        outs.append(p)
    print("\n".join(outs))


if __name__ == "__main__":
    main(*sys.argv[1:4])
