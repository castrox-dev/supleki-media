#!/usr/bin/env python3
"""Gera um Reel 9:16 (1080x1920) estilo motion-graphics a partir de um JSON de cards.

Uso: python3 make_reel.py spec.json out.mp4

Formato do spec:
{
  "fps": 30,
  "cards": [
    {"type": "hook", "title": "...", "sub": "...", "dur": 2.2},
    {"type": "data", "label": "...", "value": "...", "note": "...", "dur": 2.4},
    {"type": "cta",  "title": "...", "sub": "...", "dur": 2.4}
  ]
}
"""
import json, math, os, struct, subprocess, sys, tempfile, wave
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W, H = 1080, 1920
TURQ = (20, 184, 176)
TURQ_DARK = (12, 140, 134)
INK = (12, 46, 44)
WHITE = (255, 255, 255)
SOFT = (230, 250, 248)
FONT_DIR = "/usr/share/fonts/opentype/inter/"


def font(name, size):
    return ImageFont.truetype(FONT_DIR + name, size)


F_BLACK = lambda s: font("InterDisplay-Black.otf", s) if os.path.exists(FONT_DIR + "InterDisplay-Black.otf") else font("Inter-Black.otf", s)
F_BOLD = lambda s: font("Inter-Bold.otf", s)
F_SEMI = lambda s: font("Inter-SemiBold.otf", s)
F_MED = lambda s: font("Inter-Medium.otf", s)


def ease_out(t):
    return 1 - (1 - t) ** 3


def wrap(draw, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=f) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_centered(draw, lines, f, y, fill, lh):
    for ln in lines:
        tw = draw.textlength(ln, font=f)
        draw.text(((W - tw) / 2, y), ln, font=f, fill=fill)
        y += lh
    return y


def bg(progress_frac):
    img = Image.new("RGB", (W, H), TURQ)
    d = ImageDraw.Draw(img)
    # sutil gradiente diagonal
    grad = Image.linear_gradient("L").resize((W, H)).rotate(12, expand=False)
    over = Image.new("RGB", (W, H), TURQ_DARK)
    img = Image.composite(over, img, grad.point(lambda p: int(p * 0.35)))
    d = ImageDraw.Draw(img)
    # barra de progresso (topo, dentro da zona segura)
    d.rounded_rectangle((60, 230, W - 60, 242), 6, fill=(255, 255, 255, 80))
    d.rounded_rectangle((60, 230, 60 + (W - 120) * progress_frac, 242), 6, fill=WHITE)
    return img


def render_hook(card, t, prog):
    img = bg(prog)
    d = ImageDraw.Draw(img)
    a = ease_out(min(1, t / 0.45))
    f = F_BLACK(118)
    lines = wrap(d, card["title"], f, 940)
    lh = 128
    total = len(lines) * lh
    y = (H - total) / 2 - 120 + (1 - a) * 80
    y_end = draw_centered(d, lines, f, y, WHITE, lh)
    if card.get("sub") and t > 0.55:
        b = ease_out(min(1, (t - 0.55) / 0.35))
        fs = F_SEMI(60)
        pill_w = d.textlength(card["sub"], font=fs) + 90
        px = (W - pill_w) / 2
        py = y_end + 50 + (1 - b) * 40
        d.rounded_rectangle((px, py, px + pill_w, py + 110), 55, fill=WHITE)
        d.text((px + 45, py + 22), card["sub"], font=fs, fill=INK)
    return img


def render_data(card, t, prog, idx):
    img = bg(prog)
    d = ImageDraw.Draw(img)
    a = ease_out(min(1, t / 0.4))
    cw, ch = 940, 800
    cx, cy = (W - cw) / 2, (H - ch) / 2 - 60 + (1 - a) * 120
    d.rounded_rectangle((cx, cy, cx + cw, cy + ch), 56, fill=WHITE)
    # numero do card
    fn = F_BOLD(44)
    d.rounded_rectangle((cx + 60, cy + 60, cx + 170, cy + 130), 35, fill=SOFT)
    d.text((cx + 83, cy + 72), f"{idx:02d}", font=fn, fill=TURQ_DARK)
    # label
    fl = F_SEMI(54)
    d.text((cx + 200, cy + 76), card["label"].upper(), font=fl, fill=TURQ_DARK)
    # valor grande com pop
    b = ease_out(min(1, max(0, t - 0.25) / 0.35))
    # escolhe o maior tamanho em que o valor cabe em 2 linhas
    base = 138
    while base > 80:
        if len(wrap(d, card["value"], F_BLACK(base), cw - 120)) <= 2:
            break
        base -= 8
    size = int(base * (0.6 + 0.4 * b))
    fv = F_BLACK(size)
    vlines = wrap(d, card["value"], fv, cw - 120)
    y = cy + 230
    for ln in vlines:
        tw = d.textlength(ln, font=fv)
        d.text(((W - tw) / 2, y), ln, font=fv, fill=INK)
        y += size + 14
    if card.get("note"):
        fnn = F_MED(48)
        nl = wrap(d, card["note"], fnn, cw - 140)
        draw_centered(d, nl, fnn, cy + ch - 90 - 56 * len(nl), (90, 110, 108), 56)
    return img


def render_cta(card, t, prog):
    img = bg(prog)
    d = ImageDraw.Draw(img)
    a = ease_out(min(1, t / 0.45))
    f = F_BLACK(104)
    lines = wrap(d, card["title"], f, 920)
    lh = 114
    y = (H - len(lines) * lh) / 2 - 140 + (1 - a) * 80
    y = draw_centered(d, lines, f, y, WHITE, lh)
    if card.get("sub"):
        fs = F_SEMI(56)
        sl = wrap(d, card["sub"], fs, 900)
        draw_centered(d, sl, fs, y + 40, SOFT, 68)
    # seta pulsante pra comentarios
    # chevron pulsante apontando pros comentarios
    ay = H - 520 + int(14 * math.sin(t * 6))
    for k in range(2):
        yy = ay + k * 70
        d.line([(W/2 - 90, yy), (W/2, yy + 60), (W/2 + 90, yy)], fill=WHITE, width=22, joint="curve")
    return img


def pop_sound(sr, f0=620, f1=300, dur=0.09, amp=0.55):
    n = int(sr * dur)
    t = np.linspace(0, dur, n, False)
    freq = f0 + (f1 - f0) * (t / dur)
    env = np.exp(-t * 55)
    return amp * env * np.sin(2 * np.pi * freq * t)


def whoosh(sr, dur=0.35, amp=0.18):
    n = int(sr * dur)
    noise = np.random.default_rng(1).normal(0, 1, n)
    k = np.ones(40) / 40
    noise = np.convolve(noise, k, "same")
    env = np.sin(np.linspace(0, math.pi, n)) ** 2
    return amp * env * noise


def main(spec_path, out_path):
    spec = json.load(open(spec_path))
    fps = spec.get("fps", 30)
    cards = spec["cards"]
    total = sum(c["dur"] for c in cards)
    tmp = tempfile.mkdtemp()
    frame_i = 0
    sr = 44100
    audio = np.zeros(int(sr * total) + sr, dtype=np.float32)
    elapsed = 0.0
    data_idx = 0
    for c in cards:
        if c["type"] == "data":
            data_idx += 1
        nfr = int(round(c["dur"] * fps))
        # som na entrada do card
        start = int(elapsed * sr)
        s = whoosh(sr) if c["type"] == "hook" else pop_sound(sr, f0=520 + 40 * data_idx)
        audio[start:start + len(s)] += s
        for k in range(nfr):
            t = k / fps
            prog = (elapsed + t) / total
            if c["type"] == "hook":
                img = render_hook(c, t, prog)
            elif c["type"] == "data":
                img = render_data(c, t, prog, data_idx)
            else:
                img = render_cta(c, t, prog)
            img.save(f"{tmp}/f{frame_i:05d}.jpg", quality=92)
            frame_i += 1
        elapsed += c["dur"]
    # narração externa (spec["voice"]): mixa por cima dos efeitos
    if spec.get("voice"):
        vwav = f"{tmp}/voice.wav"
        vpath = spec["voice"]
        if not os.path.isabs(vpath):
            vpath = os.path.join(os.path.dirname(os.path.abspath(spec_path)), vpath)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vpath, "-ac", "1", "-ar", str(sr), vwav], check=True)
        with wave.open(vwav) as vf:
            v = np.frombuffer(vf.readframes(vf.getnframes()), dtype=np.int16).astype(np.float32) / 32767
        n = min(len(v), len(audio))
        audio[:n] = audio[:n] * 0.35 + v[:n] * 0.95
    wav_path = f"{tmp}/a.wav"
    audio = np.clip(audio, -1, 1)
    with wave.open(wav_path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/f%05d.jpg",
        "-i", wav_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out_path
    ], check=True)
    print(f"ok {out_path} {total:.1f}s {frame_i} frames")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
