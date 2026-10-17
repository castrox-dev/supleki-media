#!/usr/bin/env python3
"""Reel 9:16 animado (v2): fundo com bolhas em movimento, texto palavra por palavra,
itens de lista entrando um a um com check/X desenhado, transição de "rodo" entre
cenas, CTA pulsando, trilha original sintetizada + efeitos + narração.

Uso: python3 make_reel_v2.py spec.json out.mp4

Spec:
{
  "fps": 30,
  "voice": "../audio/10_voz.mp3",          (opcional)
  "music": true,                            (trilha sintetizada leve; opcional)
  "scenes": [
    {"type": "hook", "title": "...", "sub": "...", "dur": 2.6},
    {"type": "list", "label": "ENTRA", "icon": "check|x|ban", "items": [["título","nota"],...],
     "dur": 5.0, "at": [0.3, 0.9, ...]},     (at = segundo em que cada item entra; opcional)
    {"type": "cta", "pre": "Comenta", "word": "CHECKLIST", "sub": "...", "dur": 3.0}
  ]
}
"""
import json, math, os, subprocess, sys, tempfile, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1080, 1920
TURQ = (20, 184, 176)
TURQ_D = (12, 140, 134)
TURQ_DD = (8, 104, 100)
INK = (12, 46, 44)
GREY = (90, 110, 108)
WHITE = (255, 255, 255)
SOFT = (230, 250, 248)
RED = (214, 69, 69)
YEL = (255, 214, 92)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}


def F(name, s):
    k = (name, int(s))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + name, max(4, int(s)))
    return _fc[k]


BLACK = "InterDisplay-Black.otf"; BOLD = "Inter-Bold.otf"; SEMI = "Inter-SemiBold.otf"; MED = "Inter-Medium.otf"


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t); return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def back_out(t, s=1.9):
    t = clamp(t); t -= 1; return t * t * ((s + 1) * t + s) + 1


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


# ---------- fundo animado ----------
_rng = np.random.default_rng(7)
BUBBLES = [dict(x=_rng.uniform(0, W), y0=_rng.uniform(0, H), r=_rng.uniform(14, 70),
                sp=_rng.uniform(40, 130), ph=_rng.uniform(0, 6.28), a=_rng.uniform(40, 95)) for _ in range(22)]
SPARK = [dict(x=_rng.uniform(80, W - 80), y=_rng.uniform(300, H - 300), ph=_rng.uniform(0, 6.28),
              s=_rng.uniform(14, 30)) for _ in range(9)]
_base = None


def base_bg():
    global _base
    if _base is None:
        img = Image.new("RGB", (W, H), TURQ)
        grad = Image.linear_gradient("L").resize((W, H)).rotate(14)
        img = Image.composite(Image.new("RGB", (W, H), TURQ_D), img, grad.point(lambda p: int(p * 0.5)))
        # brilho radial
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).ellipse((-300, -400, W + 300, 900), fill=70)
        glow = glow.filter(ImageFilter.GaussianBlur(160))
        img = Image.composite(Image.new("RGB", (W, H), (60, 214, 205)), img, glow)
        _base = img
    return _base.copy()


def bg(T, prog):
    img = base_bg().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for b in BUBBLES:
        y = (b["y0"] - T * b["sp"]) % (H + 200) - 100
        x = b["x"] + 26 * math.sin(T * 1.3 + b["ph"])
        r = b["r"]
        d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, int(b["a"])), width=3)
        d.ellipse((x - r * .45, y - r * .6, x - r * .15, y - r * .3), fill=(255, 255, 255, int(b["a"] * 1.2)))
    for s in SPARK:
        k = (math.sin(T * 3 + s["ph"]) + 1) / 2
        if k < .35:
            continue
        sz = s["s"] * k
        star(d, s["x"], s["y"], sz, (255, 255, 255, int(150 * k)))
    # barra de progresso
    d.rounded_rectangle((60, 230, W - 60, 242), 6, fill=(255, 255, 255, 70))
    d.rounded_rectangle((60, 230, 60 + (W - 120) * prog, 242), 6, fill=(255, 255, 255, 255))
    img.alpha_composite(ov)
    return img


def star(d, x, y, s, fill):
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else s * .28
        a = i * math.pi / 4
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    d.polygon(pts, fill=fill)


def paste_scaled(dst, layer, sc, cx, cy, alpha=1.0):
    """cola um layer RGBA escalado em torno do centro (cx, cy)."""
    if sc <= 0.01 or alpha <= 0.01:
        return
    w, h = layer.size
    nw, nh = max(1, int(w * sc)), max(1, int(h * sc))
    L = layer.resize((nw, nh), Image.BICUBIC) if abs(sc - 1) > 1e-3 else layer
    if alpha < 1:
        a = L.getchannel("A").point(lambda p: int(p * alpha))
        L = L.copy(); L.putalpha(a)
    dst.alpha_composite(L, (int(cx - nw / 2), int(cy - nh / 2)))


def text_layer(text, font, fill, pad=10):
    """layer com caixa de linha fixa (ascent+descent): palavras ficam na mesma linha de base."""
    asc, desc = font.getmetrics()
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(d0.textlength(text, font=font))
    L = Image.new("RGBA", (w + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((pad, pad), text, font=font, fill=fill)
    return L


def shadow_of(layer, off=10, blur=14, a=70):
    s = Image.new("RGBA", (layer.width + 60, layer.height + 60), (0, 0, 0, 0))
    m = layer.getchannel("A").point(lambda p: int(p * a / 255))
    blk = Image.new("RGBA", layer.size, (8, 60, 58, 255)); blk.putalpha(m)
    s.alpha_composite(blk, (30, 30 + off))
    return s.filter(ImageFilter.GaussianBlur(blur))


# ---------- cenas ----------
def scene_hook(sc, t, T, prog):
    img = bg(T, prog)
    f = F(BLACK, 122)
    d0 = ImageDraw.Draw(img)
    lines = wrap(d0, sc["title"], f, 960)
    lh = 134
    y0 = (H - len(lines) * lh) / 2 - 140
    wi = 0
    per = sc.get("word_step", 0.11)
    for li, ln in enumerate(lines):
        words = ln.split()
        widths = [d0.textlength(w, font=f) for w in words]
        sp = d0.textlength(" ", font=f)
        x = (W - (sum(widths) + sp * (len(words) - 1))) / 2
        for w, ww in zip(words, widths):
            k = (t - 0.05 - wi * per) / 0.32
            if k > 0:
                s = back_out(k)
                L = text_layer(w, f, WHITE)
                paste_scaled(img, shadow_of(L), s, x + ww / 2, y0 + li * lh + 70 + 12)
                paste_scaled(img, L, s, x + ww / 2, y0 + li * lh + 70 + (1 - ease_out(k)) * 50, alpha=clamp(k * 3))
            x += ww + sp
            wi += 1
    yend = y0 + len(lines) * lh
    if sc.get("sub"):
        k = (t - 0.05 - wi * per - 0.1) / 0.35
        if k > 0:
            fs = F(SEMI, 58)
            tw = d0.textlength(sc["sub"], font=fs) + 100
            pill = Image.new("RGBA", (int(tw), 116), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle((0, 0, tw - 1, 115), 58, fill=WHITE)
            pd.text((50, 24), sc["sub"], font=fs, fill=INK)
            paste_scaled(img, pill, back_out(k), W / 2, yend + 110)
    # vassoura de brilho passando no título
    k = (t - 0.9) / 0.6
    if 0 < k < 1:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        x = -300 + k * (W + 600)
        ImageDraw.Draw(ov).polygon([(x, y0 - 40), (x + 90, y0 - 40), (x - 110, yend + 40), (x - 200, yend + 40)],
                                   fill=(255, 255, 255, 60))
        img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(12)))
    return img


def draw_icon(d, kind, x, y, s, k):
    """ícone 64px desenhado progressivamente (k 0..1)."""
    if kind == "check":
        d.rounded_rectangle((x, y, x + s, y + s), 18, fill=SOFT)
        p1, p2, p3 = (x + s * .24, y + s * .52), (x + s * .43, y + s * .72), (x + s * .78, y + s * .30)
        if k > 0:
            a = clamp(k / .45)
            d.line([p1, (p1[0] + (p2[0] - p1[0]) * a, p1[1] + (p2[1] - p1[1]) * a)], fill=TURQ_D, width=9)
        if k > .45:
            b = clamp((k - .45) / .55)
            d.line([p2, (p2[0] + (p3[0] - p2[0]) * b, p2[1] + (p3[1] - p2[1]) * b)], fill=TURQ_D, width=9)
            d.ellipse((p2[0] - 4, p2[1] - 4, p2[0] + 4, p2[1] + 4), fill=TURQ_D)
    else:
        col = RED
        d.rounded_rectangle((x, y, x + s, y + s), 18, fill=(253, 232, 232))
        m = s * .27
        if k > 0:
            a = clamp(k / .5)
            d.line([(x + m, y + m), (x + m + (s - 2 * m) * a, y + m + (s - 2 * m) * a)], fill=col, width=9)
        if k > .5:
            b = clamp((k - .5) / .5)
            d.line([(x + s - m, y + m), (x + s - m - (s - 2 * m) * b, y + m + (s - 2 * m) * b)], fill=col, width=9)


def scene_list(sc, t, T, prog):
    img = bg(T, prog)
    items = sc["items"]
    n = len(items)
    at = sc.get("at") or [0.45 + i * min(0.55, (sc["dur"] * 0.72 - 0.45) / max(1, n)) for i in range(n)]
    # tag cai do topo
    ft = F(BOLD, 50)
    d0 = ImageDraw.Draw(img)
    tw = d0.textlength(sc["label"], font=ft) + 90
    tag = Image.new("RGBA", (int(tw), 100), (0, 0, 0, 0))
    td = ImageDraw.Draw(tag)
    tagfill = WHITE if sc.get("icon", "check") == "check" else (255, 240, 240)
    td.rounded_rectangle((0, 0, tw - 1, 99), 50, fill=tagfill)
    td.text((45, 20), sc["label"], font=ft, fill=TURQ_D if sc.get("icon", "check") == "check" else RED)
    # layout das linhas
    fT, fN = F(BOLD, 64), F(MED, 44)
    cw = 960
    rows = []
    for it in items:
        title, note = (list(it) + [""])[:2]
        tl = wrap(d0, title, fT, cw - 200)
        nl = wrap(d0, note, fN, cw - 200) if note else []
        rows.append((tl, nl, 38 + len(tl) * 76 + len(nl) * 54 + 38))
    gap = 26
    total_h = sum(r[2] for r in rows) + gap * (n - 1)
    top = max(400, (H - total_h) / 2 + 40)
    k = ease_out(t / 0.35)
    tag_y = top - 150 - (1 - back_out(t / 0.45)) * 220
    paste_scaled(img, tag, 1, W / 2, tag_y + 50, alpha=k)
    y = top
    for i, (tl, nl, rh) in enumerate(rows):
        kk = (t - at[i]) / 0.38
        if kk > 0:
            row = Image.new("RGBA", (cw, int(rh)), (0, 0, 0, 0))
            rd = ImageDraw.Draw(row)
            rd.rounded_rectangle((0, 0, cw - 1, rh - 1), 34, fill=WHITE)
            draw_icon(rd, sc.get("icon", "check"), 42, (rh - 84) / 2, 84, clamp((t - at[i] - 0.15) / 0.35))
            yy = 38
            for ln in tl:
                rd.text((160, yy), ln, font=fT, fill=INK); yy += 76
            for ln in nl:
                rd.text((160, yy), ln, font=fN, fill=GREY); yy += 54
            sh = shadow_of(row, off=12, blur=16, a=60)
            xoff = (1 - back_out(kk, 1.4)) * (W + 100)
            s = 1 + 0.06 * math.sin(clamp(kk) * math.pi) * (1 - clamp(kk))
            cx = W / 2 + xoff
            paste_scaled(img, sh, 1, cx, y + rh / 2 + 6)
            paste_scaled(img, row, s, cx, y + rh / 2)
            # brilho no item recém-chegado
            if 0.6 < kk < 2.2 and sc.get("icon", "check") == "check":
                st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                a = math.sin(clamp((kk - .6) / 1.6) * math.pi)
                star(ImageDraw.Draw(st), cx + cw / 2 - 30, y + 6, 26 * a, (255, 255, 255, int(230 * a)))
                img.alpha_composite(st)
        y += rh + gap
    if sc.get("foot"):
        kk = (t - (at[-1] + 0.5)) / 0.4
        if kk > 0:
            ff = F(SEMI, 46)
            L = text_layer(sc["foot"], ff, SOFT)
            paste_scaled(img, L, back_out(kk), W / 2, y + 50, alpha=clamp(kk * 2))
    return img


def scene_cta(sc, t, T, prog):
    img = bg(T, prog)
    d0 = ImageDraw.Draw(img)
    # "Comenta"
    k1 = (t - 0.05) / 0.35
    fp = F(BLACK, 96)
    if k1 > 0:
        L = text_layer(sc.get("pre", "Comenta"), fp, WHITE)
        paste_scaled(img, L, back_out(k1), W / 2, 640)
    # palavra-chave em caixa amarela, letra por letra
    word = sc["word"]
    fw = F(BLACK, 150 if len(word) <= 9 else 128)
    ww = d0.textlength(word, font=fw)
    k2 = (t - 0.35) / 0.4
    if k2 > 0:
        bw, bh = ww + 110, 230
        pulse = 1 + 0.035 * math.sin(max(0, t - 1.2) * 7)
        box = Image.new("RGBA", (int(bw), bh), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle((0, 0, bw - 1, bh - 1), 48, fill=YEL)
        paste_scaled(img, shadow_of(box, off=16, blur=18, a=80), back_out(k2) * pulse, W / 2, 830 + 14)
        paste_scaled(img, box, back_out(k2) * pulse, W / 2, 830)
        x = (W - ww) / 2
        for i, ch in enumerate(word):
            cwid = d0.textlength(ch, font=fw)
            kc = (t - 0.5 - i * 0.05) / 0.3
            if kc > 0:
                bounce = -18 * math.sin(clamp(kc) * math.pi) if kc < 1 else -6 * math.sin((t - i * .08) * 6) * (t > 1.4)
                L = text_layer(ch, fw, INK, pad=6)
                paste_scaled(img, L, back_out(kc) * pulse, x + cwid / 2, 830 + bounce)
            x += cwid
    # balão de comentário balançando
    k3 = (t - 0.8) / 0.4
    if k3 > 0:
        bal = Image.new("RGBA", (200, 190), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bal)
        bd.rounded_rectangle((10, 10, 190, 140), 46, fill=WHITE)
        bd.polygon([(50, 130), (95, 130), (40, 182)], fill=WHITE)
        for j in range(3):
            bd.ellipse((48 + j * 40, 62, 72 + j * 40, 86), fill=TURQ_D)
        ang = 8 * math.sin(t * 5)
        bal = bal.rotate(ang, resample=Image.BICUBIC, expand=True)
        paste_scaled(img, bal, back_out(k3), W - 230, 560)
    if sc.get("sub"):
        k4 = (t - 0.9) / 0.4
        if k4 > 0:
            fs = F(SEMI, 56)
            for j, ln in enumerate(wrap(d0, sc["sub"], fs, 900)):
                L = text_layer(ln, fs, SOFT)
                paste_scaled(img, L, 1, W / 2, 1050 + j * 70 + (1 - ease_out(k4)) * 40, alpha=clamp(k4 * 2))
    # setas pulsando pros comentários
    if t > 1.1:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for j in range(3):
            ph = (t * 2.2 - j * 0.25) % 1
            a = int(255 * math.sin(ph * math.pi))
            yy = 1330 + j * 70
            od.line([(W / 2 - 80, yy), (W / 2, yy + 54), (W / 2 + 80, yy)], fill=(255, 255, 255, a), width=20, joint="curve")
        img.alpha_composite(ov)
    return img


RENDER = {"hook": scene_hook, "list": scene_list, "cta": scene_cta}


def squeegee(a_img, b_img, k):
    """transição: faixa branca diagonal (rodo) varre a tela revelando a próxima cena."""
    k = ease_in_out(k)
    x = -400 + k * (W + 800)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(-400, 0), (x + 200, 0), (x - 200, H), (-400, H)], fill=255)
    out = Image.composite(b_img, a_img, mask)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).polygon([(x + 200, 0), (x + 290, 0), (x - 110, H), (x - 200, H)], fill=(255, 255, 255, 235))
    band = band.filter(ImageFilter.GaussianBlur(6))
    out = out.convert("RGBA"); out.alpha_composite(band)
    return out


# ---------- áudio ----------
SR = 44100


def pop(f0=700, f1=350, dur=0.08, amp=0.45):
    t = np.linspace(0, dur, int(SR * dur), False)
    return amp * np.exp(-t * 50) * np.sin(2 * np.pi * (f0 + (f1 - f0) * t / dur) * t)


def ding(f=1320, dur=0.35, amp=0.22):
    t = np.linspace(0, dur, int(SR * dur), False)
    return amp * np.exp(-t * 9) * (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.01 * t))


def buzz(dur=0.12, amp=0.25):
    t = np.linspace(0, dur, int(SR * dur), False)
    return amp * np.exp(-t * 22) * np.sign(np.sin(2 * np.pi * 150 * t)) * .6


def whoosh(dur=0.4, amp=0.22):
    n = int(SR * dur)
    x = np.convolve(np.random.default_rng(3).normal(0, 1, n), np.ones(30) / 30, "same")
    return amp * np.sin(np.linspace(0, math.pi, n)) ** 2 * x


def music(total):
    """trilha original: 104 bpm, I–V–vi–IV em Dó, pluck + kick + hat, bem baixa."""
    bpm = 104; beat = 60 / bpm
    out = np.zeros(int(SR * total) + SR)
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    nb = int(total / beat) + 1
    rng = np.random.default_rng(5)
    for b in range(nb):
        st = int(b * beat * SR)
        # kick
        t = np.linspace(0, .18, int(SR * .18), False)
        k = .5 * np.exp(-t * 22) * np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 30)) * t)
        out[st:st + len(k)] += k
        # hat no contratempo
        hs = st + int(beat / 2 * SR)
        hn = int(SR * .04)
        h = .08 * np.exp(-np.linspace(0, .04, hn) * 90) * rng.normal(0, 1, hn)
        out[hs:hs + hn] += h
        # pluck arpejado (4 colcheias por tempo... 2 por tempo)
        ch = chords[(b // 4) % 4]
        for j in range(2):
            m = ch[(b * 2 + j) % 3] + 12
            ps = st + int(j * beat / 2 * SR)
            t = np.linspace(0, .3, int(SR * .3), False)
            p = .16 * np.exp(-t * 11) * (np.sin(2 * np.pi * hz(m) * t) + .3 * np.sin(2 * np.pi * hz(m) * 2 * t))
            out[ps:ps + len(p)] += p
        # baixo na cabeça do compasso
        if b % 4 == 0:
            t = np.linspace(0, beat * 3.5, int(SR * beat * 3.5), False)
            bs = .18 * np.exp(-t * 1.2) * np.sin(2 * np.pi * hz(ch[0] - 24) * t)
            out[st:st + len(bs)] += bs
    # fade in/out
    fi = int(SR * .3); out[:fi] *= np.linspace(0, 1, fi)
    end = int(SR * total); fo = int(SR * .8)
    out[end - fo:end] *= np.linspace(1, 0, fo); out[end:] = 0
    return out


def main(spec_path, out_path):
    spec = json.load(open(spec_path))
    fps = spec.get("fps", 30)
    scenes = spec["scenes"]
    total = sum(s["dur"] for s in scenes)
    tr = spec.get("transition", 0.32)
    tmp = tempfile.mkdtemp()
    audio = np.zeros(int(SR * total) + SR, dtype=np.float64)

    def add(sig, at):
        i = int(at * SR); audio[i:i + len(sig)] += sig[:max(0, len(audio) - i)]

    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc); acc += s["dur"]
    # efeitos
    for si, s in enumerate(scenes):
        st = starts[si]
        if si > 0:
            add(whoosh(), st - tr * .6)
        if s["type"] == "hook":
            add(whoosh(.5, .25), st)
        elif s["type"] == "list":
            n = len(s["items"])
            at = s.get("at") or [0.45 + i * min(0.55, (s["dur"] * 0.72 - 0.45) / max(1, n)) for i in range(n)]
            for i, a in enumerate(at):
                add(pop(620 + 45 * i, 320), st + a)
                add(ding(1320 + 60 * i) if s.get("icon", "check") == "check" else buzz(), st + a + 0.2)
        elif s["type"] == "cta":
            add(pop(500, 260, .12, .5), st + .05)
            add(ding(1568, .6, .25), st + .4)
    nfr = int(round(total * fps))
    for fi in range(nfr):
        T = fi / fps
        si = max(i for i in range(len(scenes)) if starts[i] <= T + 1e-9)
        s = scenes[si]; t = T - starts[si]
        prog = T / total
        img = RENDER[s["type"]](s, t, T, prog)
        # transição pro próximo
        if si + 1 < len(scenes):
            left = starts[si + 1] - T
            if left < tr:
                k = 1 - left / tr
                nxt = RENDER[scenes[si + 1]["type"]](scenes[si + 1], 0.3 * k, T, prog)
                img = squeegee(img.convert("RGBA"), nxt.convert("RGBA"), k)
        # zoom suave contínuo (respira)
        z = 1 + 0.012 * math.sin(T * 1.1)
        if abs(z - 1) > 1e-3:
            nw, nh = int(W * z), int(H * z)
            img = img.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        img.convert("RGB").save(f"{tmp}/f{fi:05d}.jpg", quality=90)
    fx = audio.copy()
    mix = fx * 0.8
    if spec.get("music", True):
        m = music(total)[:len(mix)]
        mix[:len(m)] += m * spec.get("music_vol", 0.5)
    if spec.get("voice"):
        vp = spec["voice"]
        if not os.path.isabs(vp):
            vp = os.path.join(os.path.dirname(os.path.abspath(spec_path)), vp)
        vw = f"{tmp}/v.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vp, "-ac", "1", "-ar", str(SR), vw], check=True)
        with wave.open(vw) as wf:
            v = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32767
        off = int(spec.get("voice_offset", 0) * SR)
        n = min(len(v), len(mix) - off)
        # ducking: abaixa trilha/efeitos onde tem voz
        env = np.convolve(np.abs(v[:n]), np.ones(2205) / 2205, "same")
        duck = 1 - 0.45 * clamp_arr(env * 12)
        mix[off:off + n] = mix[off:off + n] * duck + v[:n] * 1.0
    mix = mix / max(1.0, np.max(np.abs(mix)) / 0.95)
    wp = f"{tmp}/a.wav"
    with wave.open(wp, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/f%05d.jpg", "-i", wp,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "19",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}", "-movflags", "+faststart", out_path], check=True)
    print(f"ok {out_path} {total:.1f}s {nfr} frames")


def clamp_arr(a):
    return np.clip(a, 0, 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
