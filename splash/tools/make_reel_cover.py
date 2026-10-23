#!/usr/bin/env python3
"""Capa de Reel 1080x1920 no padrão oficial: foto real de piscina, palavra-chave em
itálico condensado, faixa rosa e logo Splash. Texto principal dentro da área central
(o grid do perfil corta a capa em 3:4).

Uso: FONT_DIR=... python3 make_reel_cover.py foto.png saida.jpg
"""
import asyncio, sys, os, io
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(__file__))
from make_photo_carousel import photo_uri, font_face, b64, ROOT

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;background:linear-gradient(180deg,#0b4aa6 55%,#083a8a);color:#fff}
.ph{position:absolute;left:0;top:0;width:1080px;height:1120px}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,47,116,.15) 0%,rgba(6,47,116,0) 28%,rgba(8,58,138,.35) 40%,#0b4aa6 58%,#083a8a 100%)}
.box{position:absolute;left:72px;right:72px;top:930px}
.tag{display:inline-block;background:#E6157E;font-family:'BarlowC';font-weight:800;font-size:44px;letter-spacing:2px;padding:10px 32px 8px;border-radius:40px;box-shadow:0 6px 0 rgba(0,0,0,.18)}
.n{font-family:'Anton';font-size:150px;line-height:1;margin-top:26px;text-transform:uppercase;-webkit-text-stroke:3px #062f74;paint-order:stroke fill;text-shadow:0 7px 0 #062f74}
.kw{font-family:'Anton';font-size:250px;line-height:.95;text-transform:uppercase;font-style:italic;transform:skewX(-8deg);transform-origin:left;
 color:#ff5fb0;-webkit-text-stroke:4px #062f74;paint-order:stroke fill;text-shadow:0 9px 0 #062f74}
.s{font-family:'BarlowC6';font-size:52px;margin-top:24px;color:#e3efff}
.logo{position:absolute;right:56px;bottom:110px;background:#fff;border-radius:28px;padding:12px 20px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.logo img{height:110px;display:block}
.loc{position:absolute;left:72px;bottom:140px;font-family:'BarlowC6';font-size:40px;color:#cfe2ff}
.bar{position:absolute;left:0;right:0;bottom:0;height:36px;background:#E6157E}
"""


async def main(photo, out):
    ff = font_face()
    logo = b64(os.path.join(ROOT, "perfil/logo_splash_original.png"), crop=(80, 150, 1180, 1110), size=(330, 288), fmt="PNG")
    ph = photo_uri(photo, 1080, 1120, 0.5)
    html = f"""<html><head><meta charset="utf-8"><style>{ff}{CSS}</style></head><body>
<img class="ph" src="{ph}"><div class="shade"></div>
<div class="box"><div class="tag">DICA DE TRATAMENTO</div>
<div class="n">4 erros que deixam a água</div><div class="kw">verde</div>
<div class="s">o 2º quase todo mundo esquece</div></div>
<div class="loc">Itaipuaçu | Maricá</div><div class="logo"><img src="{logo}"></div><div class="bar"></div></body></html>"""
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1920})
        await pg.set_content(html)
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(150)
        png = await pg.screenshot(type="png")
        Image.open(io.BytesIO(png)).convert("RGB").save(out, quality=92)
        await br.close()

asyncio.run(main(sys.argv[1], sys.argv[2]))
