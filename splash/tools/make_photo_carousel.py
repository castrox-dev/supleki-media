#!/usr/bin/env python3
"""Carrossel 4:5 (1080x1350) no padrão oficial: foto real de piscina no topo,
painel azul com texto condensado pesado, etiquetas e faixa rosa, logo Splash.

Uso: python3 make_photo_carousel.py spec.json pasta_saida/ prefixo
Cada slide do spec ganha "photo" (caminho relativo a splash/) e opcional "focus" (0-1, recorte vertical).
Fontes: Anton e Barlow Condensed (npm @fontsource), caminho em FONT_DIR.
"""
import asyncio, base64, json, os, sys, io
from PIL import Image
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.environ.get("FONT_DIR", "")


def b64(path, crop=None, size=None, fmt="JPEG"):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    if size:
        im = im.resize(size, Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, fmt, quality=90)
    return f"data:image/{'jpeg' if fmt=='JPEG' else 'png'};base64," + base64.b64encode(buf.getvalue()).decode()


def photo_uri(path, w, h, focus=0.5):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = round((im.height - h) * focus)
    im = im.crop((x, y, x + w, y + h))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def font_face():
    def f(name, file):
        p = os.path.join(FONT_DIR, file)
        data = base64.b64encode(open(p, "rb").read()).decode()
        return f"@font-face{{font-family:'{name}';src:url(data:font/woff2;base64,{data}) format('woff2')}}"
    return (f("Anton", "anton-latin-400-normal.woff2")
            + f("BarlowC", "barlow-condensed-latin-800-normal.woff2").replace("}", ";font-weight:800}", 1)
            + f("BarlowC6", "barlow-condensed-latin-600-normal.woff2"))


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;position:relative;background:#0b4aa6;font-family:'BarlowC',sans-serif;color:#fff}
.ph{position:absolute;left:0;top:0;width:1080px;height:640px;object-fit:cover}
.ph.tall{height:760px}
.fade{position:absolute;left:0;right:0;top:420px;height:240px;background:linear-gradient(to bottom,rgba(11,74,166,0),#0b4aa6 92%)}
.tall+.fade{top:540px}
.panel{position:absolute;left:0;right:0;top:640px;bottom:0;background:linear-gradient(180deg,#0b4aa6,#083a8a)}
.dots{position:absolute;top:40px;left:0;right:0;display:flex;justify-content:center;gap:14px}
.dots i{width:16px;height:16px;border-radius:50%;background:rgba(255,255,255,.55);border:2px solid #fff}
.dots i.on{background:#E6157E}
.content{position:absolute;left:72px;right:72px;top:600px;display:flex;flex-direction:column;align-items:flex-start}
.tag{background:#E6157E;color:#fff;font-weight:800;font-size:40px;letter-spacing:2px;padding:10px 30px 8px;border-radius:40px;
 text-transform:uppercase;box-shadow:0 6px 0 rgba(0,0,0,.18)}
h1{font-family:'Anton';font-weight:400;text-transform:uppercase;line-height:1.02;margin-top:30px;
 -webkit-text-stroke:3px #062f74;paint-order:stroke fill;text-shadow:0 6px 0 #062f74}
p{font-family:'BarlowC6';font-size:44px;line-height:1.18;margin-top:26px;color:#e3efff}
.pk{color:#ff5fb0}
.bar{position:absolute;left:0;right:0;bottom:0;height:30px;background:#E6157E}
.logo{position:absolute;right:56px;bottom:62px;background:#fff;border-radius:26px;padding:10px 18px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.logo img{height:96px;display:block}
.loc{position:absolute;left:72px;bottom:84px;font-family:'BarlowC6';font-size:34px;letter-spacing:1px;color:#cfe2ff}
ul{list-style:none;margin-top:30px;width:100%}
li{display:flex;gap:24px;align-items:flex-start;margin-bottom:26px}
li b{flex:none;width:58px;height:58px;border-radius:50%;background:#E6157E;display:flex;align-items:center;justify-content:center;margin-top:4px}
li b svg{width:32px;height:32px}
li div{font-family:'Anton';font-size:52px;text-transform:uppercase;line-height:1.02}
li div span{display:block;font-family:'BarlowC6';text-transform:none;font-size:38px;color:#e3efff;margin-top:6px}
.btn{margin-top:40px;background:#E6157E;font-weight:800;font-size:46px;padding:20px 44px 16px;border-radius:60px;box-shadow:0 8px 0 rgba(0,0,0,.2)}
.arr{position:absolute;right:72px;bottom:190px;font-family:'BarlowC6';font-size:36px;color:#cfe2ff}
"""
CHECK = '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def slide_html(s, i, n, ff, logo):
    tall = s["type"] in ("hook", "cta")
    ph = photo_uri(os.path.join(ROOT, s["photo"]), 1080, 760 if tall else 640, s.get("focus", 0.5))
    dots = "".join(f'<i class="{"on" if k == i else ""}"></i>' for k in range(n))
    top = 690 if tall else 600
    body = ""
    if s["type"] == "hook":
        body = f'<h1 style="font-size:118px;margin-top:0">{s["title"]}</h1><p>{esc(s["sub"])}</p>'
    elif s["type"] == "cta":
        body = f'<h1 style="font-size:128px;margin-top:0">{s["title"]}</h1><p>{esc(s["sub"])}</p><div class="btn">{esc(s["save"])}</div>'
    elif s["type"] == "list":
        items = "".join(f'<li><b>{CHECK}</b><div>{esc(a)}<span>{esc(b)}</span></div></li>' for a, b in s["items"])
        body = f'<div class="tag">{esc(s["label"])}</div><ul>{items}</ul>'
    else:
        body = f'<div class="tag">{esc(s["label"])}</div><h1 style="font-size:{s.get("size", 96)}px">{s["title"]}</h1><p>{esc(s["sub"])}</p>'
    arr = '<div class="arr">arrasta &rarr;</div>' if i == 0 else ""
    return f"""<html><head><meta charset="utf-8"><style>{ff}{CSS}</style></head><body>
<img class="ph{' tall' if tall else ''}" src="{ph}"><div class="fade"></div>
<div class="panel" style="top:{760 if tall else 640}px"></div>
<div class="dots">{dots}</div>
<div class="content" style="top:{top}px">{body}</div>{arr}
<div class="loc">Itaipuaçu | Maricá</div>
<div class="logo"><img src="{logo}"></div><div class="bar"></div></body></html>"""


async def main(spec, out, prefix):
    sp = json.load(open(spec))["slides"]
    ff = font_face()
    logo = b64(os.path.join(ROOT, "perfil/logo_splash_original.png"), crop=(80, 150, 1180, 1110), size=(330, 288), fmt="PNG")
    os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(sp):
            await pg.set_content(slide_html(s, i, len(sp), ff, logo))
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(150)
            png = await pg.screenshot(type="png")
            Image.open(io.BytesIO(png)).convert("RGB").save(f"{out}/{prefix}_{i+1:02d}.jpg", quality=92)
        await br.close()


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:4]))
