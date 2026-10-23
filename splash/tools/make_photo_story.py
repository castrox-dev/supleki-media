#!/usr/bin/env python3
"""Story 1080x1920 no TEMPLATE PADRÃO (o mesmo do carrossel v2 aprovado): foto real no topo,
painel azul, etiqueta rosa, título Anton com contorno, texto Barlow Condensed, logo Splash e faixa rosa.

Uso: FONT_DIR=... python3 make_photo_story.py spec.json pasta_saida/
spec: {"stories":[{"name","photo","focus","tag","title","sub","btn"?, "sticker"?: "texto do espaço da figurinha"}]}
"""
import asyncio, io, json, os, sys
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(__file__))
from make_photo_carousel import photo_uri, font_face, b64, ROOT, esc

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;background:#0b4aa6;font-family:'BarlowC',sans-serif;color:#fff}
.ph{position:absolute;left:0;top:0;width:1080px;object-fit:cover}
.fade{position:absolute;left:0;right:0;height:300px;background:linear-gradient(to bottom,rgba(11,74,166,0),#0b4aa6 92%)}
.panel{position:absolute;left:0;right:0;bottom:0;background:linear-gradient(180deg,#0b4aa6,#083a8a)}
.content{position:absolute;left:72px;right:72px;display:flex;flex-direction:column;align-items:flex-start}
.tag{background:#E6157E;color:#fff;font-weight:800;font-size:44px;letter-spacing:2px;padding:10px 32px 8px;border-radius:40px;
 text-transform:uppercase;box-shadow:0 6px 0 rgba(0,0,0,.18)}
h1{font-family:'Anton';font-weight:400;text-transform:uppercase;line-height:1.02;margin-top:30px;
 -webkit-text-stroke:3px #062f74;paint-order:stroke fill;text-shadow:0 6px 0 #062f74}
p{font-family:'BarlowC6';font-size:50px;line-height:1.18;margin-top:28px;color:#e3efff}
.pk{color:#ff5fb0}
.btn{margin-top:44px;background:#E6157E;font-weight:800;font-size:48px;padding:20px 44px 16px;border-radius:60px;box-shadow:0 8px 0 rgba(0,0,0,.2)}
.stk{margin-top:44px;width:100%;height:300px;border:5px dashed rgba(255,255,255,.7);border-radius:36px;display:flex;align-items:center;justify-content:center;
 font-family:'BarlowC6';font-size:38px;color:rgba(255,255,255,.85)}
.bar{position:absolute;left:0;right:0;bottom:0;height:36px;background:#E6157E}
.logo{position:absolute;right:56px;bottom:90px;background:#fff;border-radius:26px;padding:10px 18px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.logo img{height:110px;display:block}
.loc{position:absolute;left:72px;bottom:118px;font-family:'BarlowC6';font-size:38px;letter-spacing:1px;color:#cfe2ff}
"""


def html(s, ff, logo):
    ph_h = s.get("ph_h", 900 if s.get("sticker") else 1000)
    ph = photo_uri(os.path.join(ROOT, s["photo"]), 1080, ph_h, s.get("focus", 0.5))
    top = ph_h - 120
    extra = ""
    if s.get("btn"): extra += f'<div class="btn">{esc(s["btn"])}</div>'
    if s.get("sticker"): extra += f'<div class="stk">{esc(s["sticker"])}</div>'
    sub = f'<p>{esc(s["sub"])}</p>' if s.get("sub") else ""
    return f"""<html><head><meta charset="utf-8"><style>{ff}{CSS}</style></head><body>
<img class="ph" style="height:{ph_h}px" src="{ph}"><div class="fade" style="top:{ph_h-280}px"></div>
<div class="panel" style="top:{ph_h}px"></div>
<div class="content" style="top:{top}px"><div class="tag">{esc(s["tag"])}</div>
<h1 style="font-size:{s.get("size", 120)}px">{s["title"]}</h1>{sub}{extra}</div>
<div class="loc">Itaipuaçu | Maricá</div>
<div class="logo"><img src="{logo}"></div><div class="bar"></div></body></html>"""


async def main(spec, out):
    sp = json.load(open(spec))["stories"]; ff = font_face()
    logo = b64(os.path.join(ROOT, "perfil/logo_splash_original.png"), crop=(80, 150, 1180, 1110), size=(330, 288), fmt="PNG")
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        br = await p.chromium.launch(); pg = await br.new_page(viewport={"width": 1080, "height": 1920})
        for s in sp:
            await pg.set_content(html(s, ff, logo)); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(150)
            Image.open(io.BytesIO(await pg.screenshot(type="png"))).convert("RGB").save(f"{out}/{s['name']}.jpg", quality=92)
            print("ok", s["name"])
        await br.close()


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:3]))
