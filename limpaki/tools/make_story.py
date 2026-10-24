#!/usr/bin/env python3
"""Gera um Story 1080x1920 JPEG de chamada pro post do dia.

Uso: python3 make_story.py "hook do post" "linha de apoio" out.jpg [capa_do_post.jpg]
Tag do topo: env STORY_TAG (padrão "POST NOVO NO PERFIL"); sem capa o texto fica centralizado.
Tema: env STORY_THEME=light inverte (fundo branco, texto turquesa) pra variar entre os dias.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
TURQ = (20, 184, 176)
TURQ_DARK = (12, 140, 134)
INK = (12, 46, 44)
WHITE = (255, 255, 255)
SOFT = (230, 250, 248)
FD = "/usr/share/fonts/opentype/inter/"


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


def main(hook, sub, out, cover=None):
    light = os.environ.get("STORY_THEME") == "light"
    bg, bg2 = (WHITE, SOFT) if light else (TURQ, TURQ_DARK)
    tag_bg, tag_fg = (TURQ, WHITE) if light else (WHITE, TURQ_DARK)
    hook_fg, sub_fg = (TURQ_DARK, INK) if light else (WHITE, SOFT)
    img = Image.new("RGB", (W, H), bg)
    grad = Image.linear_gradient("L").resize((W, H)).rotate(12, expand=False)
    img = Image.composite(Image.new("RGB", (W, H), bg2), img, grad.point(lambda p: int(p * 0.35)))
    d = ImageDraw.Draw(img)
    # tag topo
    ft = ImageFont.truetype(FD + "Inter-Bold.otf", 44)
    tag = os.environ.get("STORY_TAG", "POST NOVO NO PERFIL")
    tw = d.textlength(tag, font=ft) + 80
    d.rounded_rectangle(((W - tw) / 2, 330, (W + tw) / 2, 420), 45, fill=tag_bg)
    d.text(((W - tw) / 2 + 40, 350), tag, font=ft, fill=tag_fg)
    # hook
    fh = ImageFont.truetype(FD + "InterDisplay-Black.otf", 112)
    lines = wrap(d, hook, fh, 920)
    y = centered(d, lines, fh, 520 if cover else 640, hook_fg, 122)
    # capa do post como "card" inclinado
    if cover:
        c = Image.open(cover).convert("RGB")
        # encolhe a capa quando o hook ocupa muitas linhas, pra linha de apoio caber
        max_h = H - 300 - (y + 60)
        cw = max(300, min(500, int(max_h * c.width / c.height / 1.1)))
        c = c.resize((cw, int(cw * c.height / c.width)))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, c.width, c.height), 40, fill=255)
        card = Image.new("RGBA", (c.width + 60, c.height + 60), (0, 0, 0, 0))
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((30, 40, c.width + 30, c.height + 40), 40, fill=(0, 0, 0, 90))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        card.alpha_composite(shadow)
        card.paste(c, (30, 30), mask)
        card = card.rotate(-6, expand=True, resample=Image.BICUBIC)
        img.paste(card, ((W - card.width) // 2, y + 60), card)
        y = y + 60 + card.height
        d = ImageDraw.Draw(img)
    # apoio
    fs = ImageFont.truetype(FD + "Inter-SemiBold.otf", 52)
    sl = wrap(d, sub, fs, 880)
    centered(d, sl, fs, max(y + 40, H - 660) if cover else y + 70, sub_fg, 64)
    img.save(out, quality=92)
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
