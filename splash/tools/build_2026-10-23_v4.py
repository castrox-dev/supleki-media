#!/usr/bin/env python3
"""Refaz o conteúdo de 23/10/2026 no padrão dos reels oficiais (PRIMAVERA TRADICIONAL / 3 COISAS).
Gera stories/, carrosseis/ e reels/ com sufixo _v4.  python3 tools/build_2026-10-23_v4.py"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from splash_kit import *

R = ROOT
F = lambda p: os.path.join(R, "fotos", p)
FOTO = {"6m": F("site_tradicional_modelo_6m.png"), "8m": F("site_tradicional_modelo_8m.png"),
        "fn01": F("site_tradicional_fn01.png"), "prainha": F("site_tradicional_prainha_fn02.png"),
        "semi": F("site_tradicional_semipastilhada_6m.png")}
WPP = "WhatsApp (21) 98395-4914"


def logo(x, y, h):
    return f'<div class="logo" style="left:{x}px;top:{y}px"><img src="{logo_uri()}" style="height:{h}px"></div>'


def logo_c(y, h, W=1080):
    return f'<div class="c" style="top:{y}px"><div class="logo" style="position:relative"><img src="{logo_uri()}" style="height:{h}px"></div></div>'


def foot(h=150, txt=f"Splash Itaipuaçu  •  {WPP}", fs=44):
    return f'<div class="foot" style="height:{h}px;font-size:{fs}px">{txt}</div>'


def deco(svg, x, y, z=2):
    return f'<div class="deco" style="left:{x}px;top:{y}px;z-index:{z}">{svg}</div>'


def tropical(W, y0, scale=1.0):
    """cluster de sol, boia, folhas, hibisco e respingos atrás/ao redor do título"""
    s = scale
    return (deco(leaf(int(330*s), -40, 0), int(-60*s), y0 + int(10*s), 1) + deco(leaf(int(300*s), 35, 1), W - int(250*s), y0 + int(-10*s), 1)
            + deco(leaf(int(240*s), -75, 2), int(10*s), y0 + int(220*s), 1)
            + deco(sun(int(280*s)), W // 2 - int(140*s), y0 - int(150*s), 1)
            + deco(boia(int(210*s)), W - int(300*s), y0 - int(90*s), 3)
            + deco(hibisco(int(170*s)), int(40*s), y0 + int(330*s), 4)
            + deco(gotas(int(230*s)), W - int(260*s), y0 + int(360*s), 4))


def water_bg(blobs=True):
    b = '<div class="water"></div>'
    if blobs:
        b += ('<div class="blob" style="width:520px;height:520px;left:-260px;top:520px;opacity:.95"></div>'
              '<div class="blob" style="width:420px;height:420px;right:-230px;top:120px;opacity:.95"></div>')
    return b


# ------------------------------------------------------------------ STORIES 1080x1920
def st_bom_dia():
    body = (water_bg() + logo_c(110, 200) + tropical(1080, 560)
            + '<div class="c" style="top:600px;z-index:5">' + bubble("BOM DIA!", 210) + '</div>'
            + '<div class="c" style="top:900px;z-index:5"><div class="pill" style="font-size:66px"><b>HOJE TEM DICA</b></div></div>'
            + '<div class="c" style="top:1040px;z-index:5"><div class="pill" style="font-size:66px"><b>DE PISCINA AQUI</b></div></div>'
            + '<div class="c" style="top:1300px;z-index:5"><div class="card" style="font-size:50px;padding:30px 50px;max-width:880px">Fica de olho nos stories: dica rápida pra deixar sua água cristalina.</div></div>'
            + onda(1080, 260).replace("<svg", '<svg style="position:absolute;left:0;bottom:120px;z-index:1"') + foot())
    return page(1080, 1920, body)


def st_dica_ph():
    body = (water_bg() + logo_c(110, 180) + deco(sun(240), 760, 330) + deco(leaf(280, -30, 0), -70, 360) + deco(gotas(240), 790, 1260, 4)
            + '<div class="c" style="top:420px;z-index:5"><div class="pink" style="font-size:58px">DICA SPLASH</div></div>'
            + '<div class="c" style="top:560px;z-index:5">' + bubble("pH IDEAL", 190) + '</div>'
            + '<div class="c" style="top:810px;z-index:5"><div class="pill" style="font-size:64px"><b>DA ÁGUA DA PISCINA</b></div></div>'
            + '<div class="c" style="top:980px;z-index:5"><div class="card" style="padding:20px 70px 10px">'
            + bubble("7,0 a 7,4", 170, "blu") + '</div></div>'
            + '<div class="c" style="top:1290px;z-index:5"><div class="card" style="font-size:48px;padding:26px 46px;max-width:860px">Fora dessa faixa a água desequilibra e a alga aparece. Dúvida? Chama no direct.</div></div>'
            + onda(1080, 220).replace("<svg", '<svg style="position:absolute;left:0;bottom:120px;z-index:1"') + foot())
    return page(1080, 1920, body)


def st_chamada_foto(photo, l1, giant, l3, sub, focus=0.5, gsize=230):
    """padrão '3 COISAS QUE VOCÊ DEVERIA OBSERVAR': foto real + faixas azuis + palavra gigante"""
    body = (f'<div class="ph" style="inset:0;background-image:url({img_uri(photo,1080,1920,focus)})"></div>'
            '<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,40,110,.25),rgba(0,0,0,0) 30%,rgba(0,0,0,0) 60%,rgba(0,40,110,.55))"></div>'
            + logo_c(110, 170)
            + '<div class="c" style="top:430px"><div class="pink" style="font-size:56px">POST NOVO NO PERFIL</div></div>'
            + f'<div class="c" style="top:640px"><div class="strip" style="font-size:66px">{l1}</div></div>'
            + f'<div class="c" style="top:745px"><div class="giant" style="font-size:{gsize}px">{giant}</div></div>'
            + f'<div class="c" style="top:{745+int(gsize*0.95)}px"><div class="strip" style="font-size:66px">{l3}</div></div>'
            + f'<div class="c" style="top:1420px"><div class="card" style="font-size:46px;padding:24px 44px;max-width:860px">{sub}</div></div>'
            + foot())
    return page(1080, 1920, body)


def st_chamada_festa(top, big, pill2, sub):
    body = (water_bg() + logo_c(110, 170) + tropical(1080, 600, 0.9)
            + '<div class="c" style="top:430px;z-index:5"><div class="pink" style="font-size:56px">POST NOVO NO PERFIL</div></div>'
            + f'<div class="c" style="top:600px;z-index:5"><div class="pill" style="font-size:72px"><b>{top}</b></div></div>'
            + '<div class="c" style="top:750px;z-index:5">' + bubble(big, 200) + '</div>'
            + f'<div class="c" style="top:1000px;z-index:5"><div class="pill" style="font-size:66px"><b>{pill2}</b></div></div>'
            + f'<div class="c" style="top:1320px;z-index:5"><div class="card" style="font-size:48px;padding:26px 46px;max-width:860px">{sub}</div></div>'
            + onda(1080, 220).replace("<svg", '<svg style="position:absolute;left:0;bottom:120px;z-index:1"') + foot())
    return page(1080, 1920, body)


def st_interativo(tag, big, pill2, hint, sticker_space=True):
    body = (water_bg() + logo_c(110, 170) + deco(sun(230), 790, 300) + deco(leaf(280, -30, 1), -80, 330) + deco(boia(180), 60, 1500, 3)
            + f'<div class="c" style="top:420px;z-index:5"><div class="pink" style="font-size:56px">{tag}</div></div>'
            + '<div class="c" style="top:570px;z-index:5">' + bubble(big, 150) + '</div>'
            + f'<div class="c" style="top:{570+150*len(big.split("<br>"))+60}px;z-index:5"><div class="pill" style="font-size:60px"><b>{pill2}</b></div></div>'
            + (f'<div style="position:absolute;left:140px;right:140px;top:1180px;height:330px;border:6px dashed rgba(255,255,255,.8);border-radius:40px;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:700;color:rgba(255,255,255,.95)">{hint}</div>' if sticker_space else "")
            + foot())
    return page(1080, 1920, body)


# ------------------------------------------------------------------ CARROSSEL 1080x1350
def car_hook():
    body = (water_bg() + f'<div class="ph" style="left:60px;right:60px;top:560px;height:640px;border-radius:60px;border:10px solid #fff;background-image:url({img_uri(FOTO["prainha"],960,640,0.55)});box-shadow:0 16px 0 #0a2f86"></div>'
            + deco(sun(220), 800, 20) + deco(leaf(260, -35, 0), -70, 60) + deco(boia(170), 860, 1080, 4) + deco(hibisco(150), 10, 1040, 4)
            + '<div class="c" style="top:70px;z-index:5"><div class="pill" style="font-size:70px"><b>FIBRA OU</b></div></div>'
            + '<div class="c" style="top:190px;z-index:5">' + bubble("ALVENARIA?", 150) + '</div>'
            + '<div class="c" style="top:395px;z-index:5"><div class="pink" style="font-size:54px">5 DIFERENÇAS QUE PESAM NO BOLSO</div></div>'
            + '<div class="c" style="top:1222px"><div class="logo" style="position:relative;padding:10px 22px"><img src="'+logo_uri()+'" style="height:84px"></div></div>')
    return page(1080, 1350, body)


def car_texto(n, label, title, sub, photo, focus=0.5):
    body = (water_bg(False) + f'<div class="ph" style="left:0;right:0;top:0;height:600px;background-image:url({img_uri(photo,1080,600,focus)});border-bottom:10px solid #fff"></div>'
            + '<div class="blob" style="width:300px;height:300px;right:-140px;top:470px"></div>'
            + (f'<div style="position:absolute;left:60px;top:500px;z-index:5">' + bubble(n, 170, "yel") + '</div>' if n else "")
            + f'<div style="position:absolute;left:{250 if n else 60}px;top:{560 if n else 540}px;z-index:5"><div class="pink" style="font-size:50px">{label}</div></div>'
            + f'<div style="position:absolute;left:60px;right:60px;top:720px;font-size:86px;font-weight:800;line-height:1.02;-webkit-text-stroke:14px #0a2f86;paint-order:stroke fill;text-shadow:0 8px 0 #0a2f86">{title}</div>'
            + f'<div class="card" style="position:absolute;left:60px;right:60px;top:1010px;font-size:42px;padding:24px 36px;line-height:1.22">{sub}</div>'
            + deco(gotas(170), 880, 620, 4))
    return page(1080, 1350, body)


def car_cta():
    body = (water_bg() + tropical(1080, 430, 0.85)
            + '<div class="c" style="top:120px;z-index:5"><div class="pill" style="font-size:70px"><b>QUER O PREÇO?</b></div></div>'
            + '<div class="c" style="top:300px;z-index:5"><div class="pill" style="font-size:64px"><b>COMENTA</b></div></div>'
            + '<div class="c" style="top:440px;z-index:5">' + bubble("PISCINA", 190) + '</div>'
            + '<div class="c" style="top:720px;z-index:5"><div class="card" style="font-size:46px;padding:24px 44px;max-width:900px">que a gente te manda os modelos e o preço no direct</div></div>'
            + f'<div class="c" style="top:930px;z-index:5"><div class="pink" style="font-size:46px">ou chama no {WPP}</div></div>'
            + '<div class="c" style="top:1060px;z-index:5"><div style="font-size:40px;font-weight:700;background:rgba(10,47,134,.55);padding:10px 30px;border-radius:30px">Salva pra consultar depois</div></div>'
            + '<div class="c" style="top:1200px"><div class="logo" style="position:relative;padding:10px 22px"><img src="'+logo_uri()+'" style="height:96px"></div></div>')
    return page(1080, 1350, body)


# ------------------------------------------------------------------ REEL 1080x1920 (cards + capa)
def reel_card(i, kicker, big, note, photo, focus=0.5, size=170, green=False):
    tint = 'rgba(40,160,60,.45)' if green else 'rgba(0,0,0,0)'
    num = (f'<div style="position:absolute;left:70px;top:820px;z-index:6">' + bubble(f"{i:02d}", 190, "yel") + '</div>') if i else ""
    body = (water_bg() + f'<div class="ph" style="left:0;right:0;top:0;height:900px;background-image:url({img_uri(photo,1080,900,focus)});border-bottom:12px solid #fff"></div>'
            + f'<div style="position:absolute;left:0;right:0;top:0;height:900px;background:{tint};mix-blend-mode:multiply"></div>'
            + logo(60, 70, 120) + deco(gotas(200), 830, 760, 5) + deco(leaf(240, 30, 1), 900, 1450, 1) + deco(hibisco(150), -20, 1560, 4)
            + num
            + f'<div class="c" style="top:{1000 if not i else 1050}px;z-index:5"><div class="pink" style="font-size:52px">{kicker}</div></div>'
            + f'<div class="c" style="top:{1130 if not i else 1180}px;z-index:5">' + bubble(big, size) + '</div>'
            + f'<div class="c" style="top:{1180+int(size*0.95*len(big.split("<br>")))+ (0 if not i else 50)}px;z-index:5"><div class="card" style="font-size:46px;padding:22px 40px;max-width:900px">{note}</div></div>'
            + foot(130, f"Splash Itaipuaçu  •  {WPP}", 40))
    return page(1080, 1920, body)


def reel_capa():
    body = (f'<div class="ph" style="inset:0;background-image:url({img_uri(FOTO["6m"],1080,1920,0.5)})"></div>'
            '<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,40,110,.35),rgba(0,0,0,0) 25%,rgba(0,0,0,0) 70%,rgba(0,40,110,.5))"></div>'
            + logo_c(110, 160) + deco(gotas(240), 790, 1170, 5) + deco(boia(200), 60, 1250, 5)
            + '<div class="c" style="top:470px"><div class="strip" style="font-size:70px">SUA PISCINA FICOU</div></div>'
            + '<div class="c" style="top:580px;z-index:5">' + bubble("VERDE?", 270, "", None, None, None, "--a:#b8ff8a;--b:#4fd34a;--c:#16962a") + '</div>'
            + '<div class="c" style="top:900px"><div class="strip" style="font-size:66px">QUASE SEMPRE É UM</div></div>'
            + '<div class="c" style="top:990px"><div class="strip" style="font-size:66px">DESSES 4 ERROS</div></div>'
            + foot())
    return page(1080, 1920, body)


def make_reel(cards, out, dur):
    tmp = tempfile.mkdtemp()
    render([{"out": f"{tmp}/c{k}.png", "w": 1080, "h": 1920, "html": h} for k, h in enumerate(cards)])
    xf = 0.35; ins = []; fl = []
    for k, d in enumerate(dur):
        ins += ["-i", f"{tmp}/c{k}.png"]
        fr = int(d * 30)
        fl.append(f"[{k}:v]scale=1188:2112,zoompan=z='1+0.06*on/{fr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s=1080x1920:fps=30,setsar=1[v{k}]")
    last = "v0"; off = 0
    for k in range(1, len(dur)):
        off += dur[k - 1] - xf
        fl.append(f"[{last}][v{k}]xfade=transition=slideleft:duration={xf}:offset={off:.2f}[x{k}]"); last = f"x{k}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fl), "-map", f"[{last}]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    print("ok", out)


if __name__ == "__main__":
    D = "2026-10-23"
    jobs = [
        {"out": f"{R}/stories/{D}_00_bom_dia_v4.jpg", "w": 1080, "h": 1920, "html": st_bom_dia()},
        {"out": f"{R}/stories/{D}_01_dica_ph_v4.jpg", "w": 1080, "h": 1920, "html": st_dica_ph()},
        {"out": f"{R}/stories/{D}_02_post_fibra_x_alvenaria_v4.jpg", "w": 1080, "h": 1920,
         "html": st_chamada_foto(FOTO["prainha"], "FIBRA OU ALVENARIA?", "5 DIFERENÇAS", "QUE PESAM NO BOLSO", "Toca aqui e vê o post completo", 0.5, 148)},
        {"out": f"{R}/stories/{D}_03_post_agua_verde_v4.jpg", "w": 1080, "h": 1920,
         "html": st_chamada_festa("SUA PISCINA FICOU", "VERDE?", "4 ERROS QUE CAUSAM ISSO", "Reel novo no perfil. O 2º quase todo mundo esquece.")},
        {"out": f"{R}/stories/{D}_int1_enquete_fundo_v4.jpg", "w": 1080, "h": 1920,
         "html": st_interativo("ENQUETE", "PISCINA<br>NESSE VERÃO?", "VOCÊ PENSA EM TER?", "figurinha de enquete aqui")},
        {"out": f"{R}/stories/{D}_int2_caixinha_fundo_v4.jpg", "w": 1080, "h": 1920,
         "html": st_interativo("RESPONDE AÍ", "QUAL PISCINA<br>CABE AÍ?", "ME FALA O TAMANHO DO QUINTAL", "caixinha de perguntas aqui")},
        # carrossel fibra x alvenaria v4
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_01.jpg", "w": 1080, "h": 1350, "html": car_hook()},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_02.jpg", "w": 1080, "h": 1350, "html": car_texto("", "RESUMO", "A fibra chega <span style='color:#ff7cc0'>pronta</span>. A alvenaria é construída no local.", "Isso muda o prazo, o acabamento, a limpeza, o gasto com produto e o risco de vazamento.", FOTO["fn01"], 0.6)},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_03.jpg", "w": 1080, "h": 1350, "html": car_texto("1", "PRAZO", "Casco pronto x <span style='color:#ff7cc0'>30 a 45 dias</span> de obra", "Na fibra, o casco já vem pronto de fábrica. Na alvenaria, a piscina inteira é construída no seu quintal.", FOTO["semi"], 0.55)},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_04.jpg", "w": 1080, "h": 1350, "html": car_texto("2", "ACABAMENTO", "Sem azulejo e <span style='color:#ff7cc0'>sem rejunte</span>", "O casco já sai acabado da fábrica. Na alvenaria ainda tem impermeabilização, azulejo e rejunte pra fazer.", FOTO["6m"], 0.6)},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_05.jpg", "w": 1080, "h": 1350, "html": car_texto("3", "LIMPEZA", "Superfície <span style='color:#ff7cc0'>lisa</span>, menos escovação", "Sem rejunte poroso pra alga se esconder: a limpeza do dia a dia fica mais rápida.", FOTO["8m"], 0.55)},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_06.jpg", "w": 1080, "h": 1350, "html": car_texto("4", "PRODUTOS", "Água mais fácil de <span style='color:#ff7cc0'>equilibrar</span>", "Com a superfície lisa, a água costuma pedir menos correção de produto.", FOTO["fn01"], 0.4)},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_07.jpg", "w": 1080, "h": 1350, "html": car_texto("5", "VAZAMENTO", "Peça única, <span style='color:#ff7cc0'>sem rejunte</span> pra trincar", "A fibra é um bloco só. Na alvenaria, uma fissura na estrutura pode virar vazamento.", FOTO["prainha"], 0.35)},
        {"out": f"{R}/carrosseis/{D}_01_fibra_x_alvenaria_v4_08.jpg", "w": 1080, "h": 1350, "html": car_cta()},
        {"out": f"{R}/reels/{D}_02_agua_verde_capa_v4.jpg", "w": 1080, "h": 1920, "html": reel_capa()},
    ]
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    render([j for j in jobs if only in j["out"]])
    if not only or "reel" in only:
        cards = [reel_capa(),
                 reel_card(1, "ERRO 1", "CLORO<br>BAIXO", "sem cloro, a alga cresce rápido no calor", FOTO["semi"]),
                 reel_card(2, "ERRO 2", "ESQUECER<br>DO pH", "o ideal fica entre 7,0 e 7,4", FOTO["fn01"], 0.5, 160),
                 reel_card(3, "ERRO 3", "FILTRO<br>DESLIGADO", "água parada é convite pra alga", FOTO["8m"], 0.5, 150),
                 reel_card(4, "ERRO 4", "FOLHA<br>NO FUNDO", "sujeira vira comida pra alga", FOTO["prainha"], 0.5, 160),
                 reel_card(0, "QUER AJUDA?", "COMENTA<br>PISCINA", f"que a gente te ajuda a acertar a água • {WPP}", FOTO["6m"], 0.5, 170)]
        make_reel(cards, f"{R}/reels/{D}_02_agua_verde_v4.mp4", [3.2, 3.0, 3.4, 3.0, 3.0, 4.2])
