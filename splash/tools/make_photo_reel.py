#!/usr/bin/env python3
"""Reel 1080x1920 no padrão oficial: cada card tem foto real de piscina em movimento
(pan/zoom lento) no topo, painel azul com texto condensado, faixa rosa e logo Splash.

Uso: FONT_DIR=... python3 make_photo_reel.py spec.json saida.mp4 [audio.mp3]
Cada card do spec ganha "photo" (relativo a splash/). Tipos: hook, data, cta.
"""
import asyncio, json, os, subprocess, sys, io, tempfile
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(__file__))
from make_photo_carousel import font_face, b64, ROOT

PH_H = 1120
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:transparent}
body{width:1080px;height:1920px;overflow:hidden;position:relative;color:#fff}
.shade{position:absolute;left:0;right:0;top:0;height:1130px;background:linear-gradient(180deg,rgba(6,47,116,.25) 0%,rgba(6,47,116,0) 22%,rgba(8,58,138,0) 55%,rgba(11,74,166,.85) 88%,#0b4aa6 100%)}
.panel{position:absolute;left:0;right:0;top:1118px;bottom:0;background:linear-gradient(180deg,#0b4aa6,#083a8a)}
.box{position:absolute;left:72px;right:72px;top:960px}
.tag{display:inline-block;background:#E6157E;font-family:'BarlowC';font-weight:800;font-size:46px;letter-spacing:2px;padding:10px 32px 8px;border-radius:40px;box-shadow:0 6px 0 rgba(0,0,0,.18);text-transform:uppercase}
.big{font-family:'Anton';line-height:1.02;margin-top:28px;text-transform:uppercase;-webkit-text-stroke:3px #062f74;paint-order:stroke fill;text-shadow:0 7px 0 #062f74}
.kw{font-family:'Anton';font-size:250px;line-height:.95;text-transform:uppercase;font-style:italic;transform:skewX(-8deg);transform-origin:left;
 color:#ff5fb0;-webkit-text-stroke:4px #062f74;paint-order:stroke fill;text-shadow:0 9px 0 #062f74}
.pk{color:#ff5fb0}
.s{font-family:'BarlowC6';font-size:54px;line-height:1.18;margin-top:26px;color:#e3efff}
.btn{display:inline-block;margin-top:40px;background:#E6157E;font-family:'BarlowC';font-weight:800;font-size:50px;padding:20px 44px 16px;border-radius:60px;box-shadow:0 8px 0 rgba(0,0,0,.2)}
.logo{position:absolute;right:56px;bottom:110px;background:#fff;border-radius:28px;padding:12px 20px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.logo img{height:110px;display:block}
.loc{position:absolute;left:72px;bottom:140px;font-family:'BarlowC6';font-size:40px;color:#cfe2ff}
.bar{position:absolute;left:0;right:0;bottom:0;height:36px;background:#E6157E}
"""


def card_body(c):
    if c["type"] == "hook":
        return (f'<div class="tag">{c.get("label","Dica de tratamento")}</div>'
                f'<div class="big" style="font-size:150px">{c["title"]}</div><div class="kw">{c["kw"]}</div>'
                f'<div class="s">{c["sub"]}</div>')
    if c["type"] == "cta":
        return (f'<div class="big" style="font-size:150px;margin-top:0">{c["title"]}</div>'
                f'<div class="s">{c["sub"]}</div><div class="btn">{c["btn"]}</div>')
    return (f'<div class="tag">{c["label"]}</div><div class="big" style="font-size:{c.get("size",140)}px">{c["value"]}</div>'
            f'<div class="s">{c["note"]}</div>')


async def overlays(cards, tmp):
    ff = font_face()
    logo = b64(os.path.join(ROOT, "perfil/logo_splash_original.png"), crop=(80, 150, 1180, 1110), size=(330, 288), fmt="PNG")
    paths = []
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1920})
        for i, c in enumerate(cards):
            top = c.get("top", 960)
            html = (f'<html><head><meta charset="utf-8"><style>{ff}{CSS}</style></head><body>'
                    f'<div class="shade"></div><div class="panel"></div>'
                    f'<div class="box" style="top:{top}px">{card_body(c)}</div>'
                    f'<div class="loc">Itaipuaçu | Maricá</div><div class="logo"><img src="{logo}"></div><div class="bar"></div></body></html>')
            await pg.set_content(html)
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(120)
            out = os.path.join(tmp, f"ov{i}.png")
            await pg.screenshot(path=out, omit_background=True)
            paths.append(out)
        await br.close()
    return paths


def main(spec, out, audio=None):
    sp = json.load(open(spec))
    fps = sp.get("fps", 30)
    cards = sp["cards"]
    tmp = tempfile.mkdtemp()
    ovs = asyncio.run(overlays(cards, tmp))
    segs = []
    for i, (c, ov) in enumerate(zip(cards, ovs)):
        d = c["dur"]
        n = int(round(d * fps))
        # foto 1.18x maior que a janela; zoom lento + pan alternando o lado
        ph = os.path.join(ROOT, c["photo"])
        im = Image.open(ph)
        sw = 1080 * 1.18
        sh = max(PH_H * 1.18, im.height * sw / im.width)
        sw = im.width * sh / im.height
        W, H = int(sw) // 2 * 2, int(sh) // 2 * 2
        dirx = "1" if i % 2 == 0 else "-1"
        z = f"1+0.06*on/{n}"
        x = f"(iw-iw/zoom)/2+{dirx}*(iw-iw/zoom)/2*(on/{n}-0.5)"
        vf = (f"[0:v]scale={W}:{H},zoompan=z='{z}':x='{x}':y='(ih-ih/zoom)/2':d={n}:s=1080x{PH_H}:fps={fps},"
              f"pad=1080:1920:0:0:color=0x0b4aa6[bg];[bg][1:v]overlay=0:0,format=yuv420p")
        seg = os.path.join(tmp, f"s{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", ph, "-i", ov,
                        "-filter_complex", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium",
                        "-crf", "19", "-r", str(fps), seg], check=True)
        segs.append(seg)
    lst = os.path.join(tmp, "l.txt")
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
    if audio:
        cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main(*sys.argv[1:4])
