#!/usr/bin/env python3
"""Moldura de "propaganda eleitoral" do Popó (PNG 1080x1920 com transparência) pra usar como overlay no make_reel_v3.

Uso: python3 make_moldura_popo.py out.png
Bandeirinhas no topo + placa de candidato embaixo ("POPÓ 2026 · Vote limpo").
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
TURQ = (20, 184, 176); TURQ_D = (12, 140, 134); INK = (12, 46, 44); WHITE = (255, 255, 255)
FD = "/usr/share/fonts/opentype/inter/"
F = lambda n, s: ImageFont.truetype(FD + n, s)


def main(out):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    # bandeirinhas (triângulos pendurados numa linha)
    y0 = 92; n = 11; w = W / n
    d.line([(0, y0), (W, y0)], fill=(255, 255, 255, 230), width=6)
    for i in range(n):
        x = i * w
        col = (20, 184, 176, 235) if i % 2 == 0 else (255, 255, 255, 235)
        d.polygon([(x + 4, y0), (x + w - 4, y0), (x + w / 2, y0 + 92)], fill=col)
    # faixa inclinada discreta no canto superior direito ("CANDIDATO")
    tag = Image.new("RGBA", (520, 90), (0, 0, 0, 0)); td = ImageDraw.Draw(tag)
    td.rounded_rectangle((0, 0, 520, 90), 24, fill=(255, 255, 255, 240))
    ft = F("InterDisplay-Black.otf", 40); t = "CANDIDATO À FAXINA"
    td.text(((520 - td.textlength(t, font=ft)) / 2, 22), t, font=ft, fill=TURQ_D)
    tag = tag.rotate(-8, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(tag, (W - tag.width - 60, 1415))
    # placa de candidato embaixo
    px0, py0, px1, py1 = 90, 1540, W - 90, 1690
    d.rounded_rectangle((px0 + 8, py0 + 10, px1 + 8, py1 + 10), 40, fill=(0, 0, 0, 70))
    d.rounded_rectangle((px0, py0, px1, py1), 40, fill=(255, 255, 255, 245))
    d.rounded_rectangle((px0, py0, px0 + 26, py1), 40, fill=TURQ)
    fb = F("InterDisplay-Black.otf", 86); fs = F("Inter-SemiBold.otf", 40)
    d.text((px0 + 60, py0 + 18), "POPÓ 2026", font=fb, fill=TURQ_D)
    tw = d.textlength("POPÓ 2026", font=fb)
    d.text((px0 + 60 + tw + 30, py0 + 62), "Vote limpo.", font=fs, fill=INK)
    img.save(out)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1])
