#!/usr/bin/env python3
"""Story 1080x1920 no PADRÃO OFICIAL Splash (v2): fundo de água de piscina,
título grande condensado itálico branco com contorno azul, selo rosa, rodapé branco com logo Splash+iGUi.

Uso: python3 make_story_v2.py "TÍTULO" "linha de apoio" out.jpg [foto_de_fundo.jpg]
Env: STORY_TAG (selo rosa), STORY_FOOT (texto do rodapé; padrão Itaipuaçu + WhatsApp), STORY_SPACE=1 deixa espaço pra figurinha.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "perfil", "logo_splash_original.png")
ANTON = os.path.join(HERE, "fonts", "Anton-Regular.ttf")
INTER = "/usr/share/fonts/opentype/inter/"
PINK = (230, 21, 126); NAVY = (10, 45, 120); BLUE = (0, 120, 215); WHITE = (255, 255, 255)


def water_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(7)
    c = np.zeros((H, W), np.float32)
    for _ in range(9):
        fx, fy = rng.uniform(0.004, 0.012, 2); ph = rng.uniform(0, 6.28, 2)
        c += np.sin(x * fx + np.sin(y * fy * 0.7 + ph[0]) * 2.2 + ph[1])
    c = np.abs(c / 9.0)
    caust = np.clip(1.0 - c * 6.0, 0, 1) ** 3          # linhas claras de cáustica
    t = (y / H)
    base_top = np.array([120, 215, 245], np.float32); base_bot = np.array([0, 140, 210], np.float32)
    img = base_top * (1 - t[..., None]) + base_bot * t[..., None]
    img += caust[..., None] * np.array([110, 60, 30], np.float32)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


def photo_bg(p):
    im = ImageOps.fit(Image.open(p).convert("RGB"), (W, H))
    grad = Image.linear_gradient("L").resize((W, H))
    dark = Image.new("RGB", (W, H), (0, 40, 90))
    return Image.composite(dark, im, grad.point(lambda v: int(v * 0.55)))


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def title_layer(text, max_w=900, size=190):
    while True:
        f = ImageFont.truetype(ANTON, size)
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        lines = wrap(d, text.upper().replace("PH", "pH"), f, max_w)
        if len(lines) <= 4 or size < 110: break
        size -= 10
    lh = int(size * 1.08)
    layer = Image.new("RGBA", (W + 200, lh * len(lines) + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f); xx = (layer.width - tw) / 2; yy = 30 + i * lh
        d.text((xx + 10, yy + 14), ln, font=f, fill=(0, 30, 80, 150))           # sombra
        d.text((xx, yy), ln, font=f, fill=WHITE, stroke_width=12, stroke_fill=NAVY)
    shear = 0.18                                                               # itálico
    layer = layer.transform(layer.size, Image.AFFINE, (1, shear, -shear * layer.height / 2, 0, 1, 0), Image.BICUBIC)
    return layer


def logo_img(h):
    lg = Image.open(LOGO).convert("RGBA")
    a = np.array(lg); white = (a[..., :3] > 235).all(-1); a[white, 3] = 0
    lg = Image.fromarray(a); lg = lg.crop(lg.getbbox())
    return lg.resize((int(lg.width * h / lg.height), h), Image.LANCZOS)


def main():
    title, sub, out = sys.argv[1], sys.argv[2], sys.argv[3]
    bg = photo_bg(sys.argv[4]) if len(sys.argv) > 4 else water_bg()
    img = bg.convert("RGBA"); d = ImageDraw.Draw(img)
    tag = os.environ.get("STORY_TAG", "")
    y = 300
    if tag:
        f = ImageFont.truetype(INTER + "Inter-Black.otf", 48)
        tw = d.textlength(tag, font=f) + 90
        d.rounded_rectangle(((W - tw) / 2 + 8, y + 10, (W + tw) / 2 + 8, y + 104), 47, fill=(120, 0, 60))
        d.rounded_rectangle(((W - tw) / 2, y, (W + tw) / 2, y + 94), 47, fill=PINK)
        d.text(((W - tw) / 2 + 45, y + 18), tag, font=f, fill=WHITE)
        y += 150
    space = bool(os.environ.get("STORY_SPACE"))
    tl = title_layer(title, size=140 if space else 190)
    img.alpha_composite(tl, (int((W - tl.width) / 2), y)); y += tl.height + 10
    if sub:
        f = ImageFont.truetype(INTER + "Inter-ExtraBold.otf", 50)
        lines = wrap(d, sub, f, 860)
        bh = len(lines) * 64 + 50
        d.rounded_rectangle((80, y, W - 80, y + bh), 36, fill=(255, 255, 255, 235))
        for i, ln in enumerate(lines):
            d.text(((W - d.textlength(ln, font=f)) / 2, y + 25 + i * 64), ln, font=f, fill=NAVY)
    # rodapé branco com logo
    d.rectangle((0, H - 300, W, H), fill=WHITE)
    d.rectangle((0, H - 312, W, H - 300), fill=PINK)
    lg = logo_img(210); img.alpha_composite(lg, (70, H - 255))
    foot = os.environ.get("STORY_FOOT", "Itaipuaçu · Maricá|WhatsApp (21) 98395-4914").split("|")
    fb = ImageFont.truetype(INTER + "Inter-Black.otf", 46); fm = ImageFont.truetype(INTER + "Inter-Bold.otf", 38)
    x0 = 70 + lg.width + 50
    d.text((x0, H - 215), foot[0], font=fb, fill=NAVY)
    if len(foot) > 1: d.text((x0, H - 150), foot[1], font=fm, fill=PINK)
    img.convert("RGB").save(out, quality=92, subsampling=0)
    print("ok", out)


if __name__ == "__main__":
    main()
