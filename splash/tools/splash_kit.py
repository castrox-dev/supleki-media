#!/usr/bin/env python3
"""Kit visual Splash (v4) — padrão dos reels oficiais @splashpiscinasoficial.

Duas linguagens, tiradas das capas oficiais salvas em referencias/:
  * "festa"  (PRIMAVERA TRADICIONAL): letras 3D tipo bexiga (rosa com borda branca e azul),
    pílulas azuis, sol, boia, folhas, hibisco, respingos, fundo de água turquesa, bolhas rosa.
  * "foto"   (3 COISAS QUE VOCÊ DEVERIA OBSERVAR): foto real de piscina + faixas azuis
    arredondadas com texto branco e uma palavra gigante branca com contorno azul.
Foto real é bem-vinda, mas não obrigatória: o que não pode faltar é a vibe animada.

Uso como biblioteca:  from splash_kit import render, page
Uso direto:          python3 splash_kit.py spec.json   (lista de {"out","w","h","html"})
"""
import asyncio, base64, io, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PINK, PINK_D, BLUE, NAVY, TURQ = "#E6157E", "#9c0057", "#1565d8", "#0a2f86", "#29b6e8"


def _b64file(p):
    return base64.b64encode(open(p, "rb").read()).decode()


def img_uri(path, w=None, h=None, focus=0.5, q=88):
    im = Image.open(path).convert("RGB")
    if w and h:
        s = max(w / im.width, h / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        x = (im.width - w) // 2; y = int((im.height - h) * focus)
        im = im.crop((x, y, x + w, y + h))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


_LOGO = None
def logo_uri():
    global _LOGO
    if _LOGO is None:
        lg = Image.open(os.path.join(ROOT, "perfil", "logo_splash_original.png")).convert("RGBA")
        a = np.array(lg); a[(a[..., :3] > 235).all(-1), 3] = 0
        lg = Image.fromarray(a); lg = lg.crop(lg.getbbox())
        buf = io.BytesIO(); lg.save(buf, "PNG")
        _LOGO = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return _LOGO


def fonts():
    return (f"@font-face{{font-family:'Baloo';src:url(data:font/ttf;base64,{_b64file(os.path.join(HERE,'fonts','Baloo2.ttf'))}) format('truetype');font-weight:400 800}}"
            f"@font-face{{font-family:'Fredoka';src:url(data:font/ttf;base64,{_b64file(os.path.join(HERE,'fonts','Fredoka.ttf'))}) format('truetype');font-weight:300 700}}")


# ---------------------------------------------------------------- decoração (SVG)
def sun(size=260):
    rays = "".join(f'<rect x="92" y="-6" width="36" height="64" rx="18" fill="url(#sr)" stroke="#e08a00" stroke-width="3" transform="rotate({a} 110 110) translate(0 0)"/>'
                   for a in range(0, 360, 30))
    return f'''<svg width="{size}" height="{size}" viewBox="-10 -10 240 240"><defs>
<radialGradient id="sg" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#fff6a8"/><stop offset=".5" stop-color="#ffd21f"/><stop offset="1" stop-color="#ffa800"/></radialGradient>
<linearGradient id="sr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe14d"/><stop offset="1" stop-color="#ffb000"/></linearGradient></defs>
{rays}<circle cx="110" cy="110" r="70" fill="url(#sg)" stroke="#e08a00" stroke-width="4"/>
<ellipse cx="88" cy="82" rx="26" ry="14" fill="#fff" opacity=".55" transform="rotate(-30 88 82)"/></svg>'''


def boia(size=230):
    segs = "".join(f'<circle cx="100" cy="100" r="68" fill="none" stroke="{c}" stroke-width="50" stroke-dasharray="53.4 373.8" stroke-dashoffset="{-i*53.4}" />'
                   for i, c in enumerate(["#ff4fa3", "#fff", "#ff4fa3", "#fff", "#ff4fa3", "#fff", "#ff4fa3", "#fff"]))
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 200 200">{segs}
<circle cx="100" cy="100" r="93" fill="none" stroke="#c4005f" stroke-width="3"/><circle cx="100" cy="100" r="43" fill="none" stroke="#c4005f" stroke-width="3"/>
<path d="M40 70 A70 70 0 0 1 95 32" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" opacity=".7"/></svg>'''


def leaf(size=300, rot=0, tone=0):
    g1, g2 = [("#3fd46b", "#0f8a3a"), ("#7be35a", "#2a9d2a"), ("#2fbf8f", "#0b7a55")][tone % 3]
    cuts = "".join(f'<path d="M150 {y} Q{150+s*70} {y-20} {150+s*120} {y-40}" stroke="#0a6a2c" stroke-width="5" fill="none" opacity=".45"/>'
                   for y in range(90, 260, 34) for s in (-1, 1))
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 300 300" style="transform:rotate({rot}deg)"><defs>
<linearGradient id="lg{tone}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/></linearGradient></defs>
<path d="M150 290 C40 240 10 120 70 40 C110 -5 190 -5 230 40 C290 120 260 240 150 290Z" fill="url(#lg{tone})" stroke="#0a6a2c" stroke-width="4"/>
{cuts}<path d="M150 290 L150 30" stroke="#0a6a2c" stroke-width="6" opacity=".6"/></svg>'''


def hibisco(size=200, c1="#ff4fa3", c2="#e6157e"):
    pet = "".join(f'<ellipse cx="100" cy="52" rx="38" ry="52" fill="url(#hg)" stroke="#b0004f" stroke-width="3" transform="rotate({a} 100 100)"/>' for a in range(0, 360, 72))
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 200 200"><defs><radialGradient id="hg" cx=".5" cy=".9" r="1"><stop offset="0" stop-color="#ffd1e6"/><stop offset=".35" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></radialGradient></defs>
{pet}<circle cx="100" cy="100" r="16" fill="#ffd21f"/><path d="M100 100 L132 52" stroke="#ffd21f" stroke-width="7" stroke-linecap="round"/><circle cx="134" cy="48" r="9" fill="#ff8a00"/></svg>'''


def gotas(size=260):
    ds = [(40, 60, 22), (90, 30, 14), (150, 70, 26), (205, 35, 12), (120, 130, 16), (60, 160, 11), (190, 150, 20)]
    g = "".join(f'<path d="M{x} {y-r*1.5} C{x+r} {y-r*0.2} {x+r} {y+r} {x} {y+r} C{x-r} {y+r} {x-r} {y-r*0.2} {x} {y-r*1.5}Z" fill="url(#wg)" stroke="#0a5fc4" stroke-width="3"/>'
                f'<ellipse cx="{x-r*0.35}" cy="{y-r*0.1}" rx="{r*0.22}" ry="{r*0.4}" fill="#fff" opacity=".75"/>' for x, y, r in ds)
    return f'<svg width="{size}" height="{size*0.75}" viewBox="0 0 240 180"><defs><linearGradient id="wg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fe3ff"/><stop offset="1" stop-color="#1e8fe8"/></linearGradient></defs>{g}</svg>'


def onda(w=1080, h=260, c1="#5fd0ff", c2="#1a7fe0"):
    return f'''<svg width="{w}" height="{h}" viewBox="0 0 1080 260" preserveAspectRatio="none"><defs><linearGradient id="og" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<path d="M0 120 C180 40 300 200 540 110 C760 30 880 190 1080 90 L1080 260 L0 260Z" fill="url(#og)" stroke="#fff" stroke-width="10"/>
<path d="M0 170 C220 110 360 230 560 170 C780 110 900 220 1080 160" fill="none" stroke="#fff" stroke-width="6" opacity=".6"/></svg>'''


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{overflow:hidden;position:relative;font-family:'Baloo';color:#fff}
.water{position:absolute;inset:0;background:
  radial-gradient(ellipse 60% 40% at 20% 15%,rgba(255,255,255,.35),transparent 60%),
  radial-gradient(ellipse 50% 35% at 85% 70%,rgba(255,255,255,.22),transparent 60%),
  linear-gradient(170deg,#7ad8f7 0%,#35b4ec 45%,#1b8ee0 100%)}
.water:after{content:"";position:absolute;inset:0;opacity:.22;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='120'><path d='M0 60 Q55 20 110 60 T220 60' fill='none' stroke='white' stroke-width='5'/><path d='M-20 105 Q35 70 90 105 T200 105' fill='none' stroke='white' stroke-width='3'/></svg>")}
.blob{position:absolute;border-radius:50%;background:#E6157E}
.ph{position:absolute;background-size:cover;background-position:center}
.deco{position:absolute;filter:drop-shadow(0 10px 10px rgba(0,40,110,.28))}
.c{position:absolute;left:0;right:0;display:flex;flex-direction:column;align-items:center;text-align:center}
/* letra 3D tipo bexiga: 3 camadas */
.bub{position:relative;display:inline-block;font-weight:800;line-height:.92;letter-spacing:-1px;white-space:nowrap}
.bub span{display:block}
.bub .l1{position:absolute;inset:0;-webkit-text-stroke:var(--s1,44px) #0a2f86;color:#0a2f86;transform:translateY(var(--d,12px))}
.bub .l2{position:absolute;inset:0;-webkit-text-stroke:var(--s2,22px) #fff;color:#fff}
.bub .l3{position:relative;background:linear-gradient(180deg,var(--a,#ff8cc6) 0%,var(--b,#ff3d9a) 45%,var(--c,#d10f72) 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.bub .l4{position:absolute;inset:0;color:transparent;background:linear-gradient(180deg,rgba(255,255,255,.75) 0%,rgba(255,255,255,0) 38%);-webkit-background-clip:text;background-clip:text}
.bub.wht{--a:#ffffff;--b:#f3f8ff;--c:#d6e6ff}
.bub.blu{--a:#7fd3ff;--b:#2a8ff0;--c:#0d5ccc}
.bub.yel{--a:#fff6a0;--b:#ffd21f;--c:#ffa800}
.pill{display:inline-block;background:linear-gradient(180deg,#2f8ff5,#0d55c9);border:8px solid #fff;border-radius:999px;padding:6px 44px 2px;box-shadow:0 10px 0 #0a2f86,0 16px 26px rgba(0,30,90,.35)}
.pill b{font-weight:800;-webkit-text-stroke:2px #0a2f86;paint-order:stroke fill}
.pink{display:inline-block;background:linear-gradient(180deg,#ff3d9a,#d10f72);border:6px solid #fff;border-radius:999px;padding:8px 40px 4px;font-weight:800;box-shadow:0 8px 0 #9c0057}
.card{background:#fff;color:#0a2f86;border-radius:44px;border:8px solid #0a2f86;box-shadow:0 14px 0 #0a2f86,0 20px 30px rgba(0,30,90,.3);font-weight:700}
.strip{display:inline-block;background:#1f6fe0;border-radius:20px;padding:4px 26px 0;font-weight:800;box-shadow:0 4px 0 #0a3d9e}
.giant{font-weight:800;line-height:.9;color:#fff;-webkit-text-stroke:22px #1557d0;paint-order:stroke fill;filter:drop-shadow(0 8px 0 #0a2f86)}
.logo{position:absolute;background:#fff;border-radius:40px;padding:16px 26px;box-shadow:0 10px 0 rgba(10,47,134,.25),0 14px 30px rgba(0,30,90,.25)}
.logo img{display:block}
.foot{position:absolute;left:0;right:0;bottom:0;background:linear-gradient(180deg,#ff3d9a,#d10f72);border-top:8px solid #fff;font-weight:700;display:flex;align-items:center;justify-content:center}
"""


def bubble(text, size, cls="", s1=None, s2=None, d=None, style=""):
    s1 = s1 or round(size * 0.30); s2 = s2 or round(size * 0.15); d = d or round(size * 0.09)
    t = text
    return (f'<div class="bub {cls}" style="font-size:{size}px;--s1:{s1}px;--s2:{s2}px;--d:{d}px;{style}">'
            f'<span class="l1">{t}</span><span class="l2">{t}</span><span class="l3">{t}</span><span class="l4">{t}</span></div>')


def page(w, h, body):
    return f"<html><head><meta charset='utf-8'><style>{fonts()}{CSS}body{{width:{w}px;height:{h}px}}</style></head><body>{body}</body></html>"


async def _render_all(jobs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for j in jobs:
            pg = await b.new_page(viewport={"width": j["w"], "height": j["h"]})
            await pg.set_content(j["html"]); await pg.wait_for_timeout(250)
            png = await pg.screenshot(type="png")
            im = Image.open(io.BytesIO(png)).convert("RGB")
            out = j["out"]; os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            if out.endswith(".png"): im.save(out)
            else: im.save(out, quality=93, subsampling=0)
            print("ok", out); await pg.close()
        await b.close()


def render(jobs):
    asyncio.run(_render_all(jobs))


if __name__ == "__main__":
    render(json.load(open(sys.argv[1])))
