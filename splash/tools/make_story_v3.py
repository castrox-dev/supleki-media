#!/usr/bin/env python3
"""Story 1080x1920 no estilo das artes oficiais Splash (v3).
Fundo céu claro + onda azul, logo oficial no topo, título arredondado (Baloo 2) branco com
contorno azul e sombra 3D rosa, faixa azul de apoio, rodapé rosa com WhatsApp.

Uso: python3 make_story_v3.py "TÍTULO" "linha de apoio" out.jpg [foto.jpg]
Env: STORY_TAG (selo), STORY_SPACE=1 (espaço pra figurinha), STORY_FOOT.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "perfil", "logo_splash_original.png")
BALOO = os.path.join(HERE, "fonts", "Baloo2.ttf")
PINK = (230, 21, 126); PINK_D = (150, 0, 80); BLUE = (0, 112, 205); NAVY = (8, 52, 130); WHITE = (255, 255, 255)


def baloo(size, weight=b"ExtraBold"):
    f = ImageFont.truetype(BALOO, size); f.set_variation_by_name(weight); return f


def background(photo=None):
    if photo:
        im = ImageOps.fit(Image.open(photo).convert("RGB"), (W, H))
    else:
        y = np.linspace(0, 1, H)[:, None, None]
        top = np.array([222, 244, 255]); mid = np.array([150, 215, 250])
        im = Image.fromarray(np.broadcast_to(top * (1 - y) + mid * y, (H, W, 3)).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # ondas no estilo do logo (azul claro + azul)
    for amp, base, col in ((40, 1390, (90, 190, 245)), (36, 1440, BLUE)):
        pts = [(x, base + amp * math.sin(x / 150.0 + base)) for x in range(0, W + 10, 10)]
        d.polygon(pts + [(W, H), (0, H)], fill=col)
    return im.convert("RGBA")


def logo(h):
    lg = Image.open(LOGO).convert("RGBA")
    a = np.array(lg); a[(a[..., :3] > 235).all(-1), 3] = 0
    lg = Image.fromarray(a); lg = lg.crop(lg.getbbox())
    return lg.resize((int(lg.width * h / lg.height), h), Image.LANCZOS)


def wrap(d, text, f, mw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= mw: cur = t
        else: out.append(cur); cur = w
    return out + ([cur] if cur else [])


def title(text, size):
    f = baloo(size); d = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines = wrap(d, text.upper().replace("PH", "pH"), f, 920)
    lh = int(size * 0.98)
    lay = Image.new("RGBA", (W, lh * len(lines) + 120), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    for i, ln in enumerate(lines):
        x = (W - dd.textlength(ln, font=f)) / 2; y = 20 + i * lh
        for k in range(14, 0, -2):                      # extrusão 3D rosa
            dd.text((x + k * 0.6, y + k), ln, font=f, fill=PINK_D, stroke_width=14, stroke_fill=PINK_D)
        dd.text((x, y), ln, font=f, fill=WHITE, stroke_width=14, stroke_fill=NAVY)
    return lay.rotate(3, resample=Image.BICUBIC, expand=False)


def main():
    t, sub, out = sys.argv[1], sys.argv[2], sys.argv[3]
    img = background(sys.argv[4] if len(sys.argv) > 4 else None); d = ImageDraw.Draw(img)
    space = bool(os.environ.get("STORY_SPACE"))
    lg = logo(300)
    d.rounded_rectangle(((W - lg.width) / 2 - 40, 120, (W + lg.width) / 2 + 40, 120 + lg.height + 50), 50, fill=WHITE)
    img.alpha_composite(lg, (int((W - lg.width) / 2), 145))
    y = 120 + lg.height + 90
    tag = os.environ.get("STORY_TAG")
    if tag:
        f = baloo(64); tw = d.textlength(tag, font=f) + 100
        d.rounded_rectangle(((W - tw) / 2, y, (W + tw) / 2, y + 100), 50, fill=PINK)
        d.text(((W - tw) / 2 + 50, y + 8), tag, font=f, fill=WHITE); y += 140
    tl = title(t, 130 if space else 150)
    img.alpha_composite(tl, (0, y)); y += tl.height
    if sub:
        f = baloo(54, b"Bold"); lines = wrap(d, sub, f, 840); bh = len(lines) * 66 + 40
        d.rounded_rectangle((90, y, W - 90, y + bh), 40, fill=BLUE)
        for i, ln in enumerate(lines):
            d.text(((W - d.textlength(ln, font=f)) / 2, y + 14 + i * 66), ln, font=f, fill=WHITE)
    foot = os.environ.get("STORY_FOOT", "Splash Itaipuaçu  •  WhatsApp (21) 98395-4914")
    d.rectangle((0, H - 170, W, H), fill=PINK)
    f = baloo(44, b"Bold"); d.text(((W - d.textlength(foot, font=f)) / 2, H - 130), foot, font=f, fill=WHITE)
    img.convert("RGB").save(out, quality=92, subsampling=0); print("ok", out)


if __name__ == "__main__":
    main()
