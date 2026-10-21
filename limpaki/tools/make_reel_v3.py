#!/usr/bin/env python3
"""Reel 9:16 com clipes reais (Google Flow) + legenda em português + narração + card final.

Uso: python3 make_reel_v3.py spec.json out.mp4

Spec:
{
  "voice": "../audio/13_voz.mp3",        (opcional)
  "clip_volume": 0.25,                    (som ambiente dos clipes)
  "clips": [
    {"src": "../brutos/13_cena1.mp4", "start": 0, "dur": 8,
     "caps": [{"t": 0.0, "end": 4.5, "text": "Sábado de manhã...", "big": true}]}
  ],
  "end": {"pre": "Comenta", "word": "PLANO", "sub": "que eu te mando o plano B no direct", "dur": 3.0}
}
Legendas: caixa branca com texto escuro (Inter), "big" = hook em cima.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
TURQ = (20, 184, 176); TURQ_D = (12, 140, 134); INK = (12, 46, 44); WHITE = (255, 255, 255); SOFT = (230, 250, 248)
FD = "/usr/share/fonts/opentype/inter/"
F = lambda n, s: ImageFont.truetype(FD + n, s)


def wrap(d, text, f, mw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= mw: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


def caption_png(text, big, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = F("InterDisplay-Black.otf", 84 if big else 62)
    lines = wrap(d, text, f, 900)
    lh = 98 if big else 76
    bh = len(lines) * lh + 50
    y0 = 260 if big else H - 560 - bh
    bw = max(d.textlength(l, font=f) for l in lines) + 80
    d.rounded_rectangle(((W - bw) / 2, y0, (W + bw) / 2, y0 + bh), 34, fill=(255, 255, 255, 240))
    y = y0 + 22
    for l in lines:
        # destaca palavras em CAIXA ALTA em turquesa
        x = (W - d.textlength(l, font=f)) / 2
        for i, w in enumerate(l.split()):
            s = w + (" " if i < len(l.split()) - 1 else "")
            col = TURQ_D if (w.strip(".,:!?").isupper() and len(w.strip(".,:!?")) > 1) else INK
            d.text((x, y), s, font=f, fill=col); x += d.textlength(s, font=f)
        y += lh
    img.save(path)


def end_card(e, path):
    img = Image.new("RGB", (W, H), TURQ)
    g = Image.linear_gradient("L").resize((W, H)).rotate(12)
    img = Image.composite(Image.new("RGB", (W, H), TURQ_D), img, g.point(lambda p: int(p * .35)))
    d = ImageDraw.Draw(img)
    fp = F("InterDisplay-Black.otf", 120); fw = F("InterDisplay-Black.otf", 150)
    y = 640
    d.text(((W - d.textlength(e["pre"], font=fp)) / 2, y), e["pre"], font=fp, fill=WHITE); y += 150
    tw = d.textlength(e["word"], font=fw) + 100
    d.rounded_rectangle(((W - tw) / 2, y, (W + tw) / 2, y + 200), 60, fill=WHITE)
    d.text(((W - tw) / 2 + 50, y + 18), e["word"], font=fw, fill=TURQ_D); y += 260
    fs = F("Inter-SemiBold.otf", 56)
    for l in wrap(d, e["sub"], fs, 860):
        d.text(((W - d.textlength(l, font=fs)) / 2, y), l, font=fs, fill=SOFT); y += 70
    img.save(path, quality=95)


def run(cmd):
    subprocess.run(cmd, check=True)


def main(spec_path, out):
    spec = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    P = lambda p: os.path.normpath(os.path.join(base, p))
    tmp = tempfile.mkdtemp()
    segs = []
    for i, c in enumerate(spec["clips"]):
        inputs = ["-ss", str(c.get("start", 0)), "-t", str(c["dur"]), "-i", P(c["src"])]
        flt = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[v0]"
        last = "v0"
        for j, cap in enumerate(c.get("caps", [])):
            png = f"{tmp}/c{i}_{j}.png"; caption_png(cap["text"], cap.get("big"), png)
            inputs += ["-i", png]
            flt += f";[{last}][{j+1}:v]overlay=0:0:enable='between(t,{cap['t']},{cap['end']})'[v{j+1}]"
            last = f"v{j+1}"
        seg = f"{tmp}/s{i}.mp4"
        vol = spec.get("clip_volume", 0.25)
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", flt + f";[0:a]volume={vol},aresample=44100[a]",
             "-map", f"[{last}]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-ar", "44100", "-ac", "2", seg])
        segs.append(seg)
    if spec.get("end"):
        e = spec["end"]; png = f"{tmp}/end.jpg"; end_card(e, png); seg = f"{tmp}/end.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(e["dur"]), "-i", png, "-f", "lavfi", "-t", str(e["dur"]),
             "-i", "anullsrc=r=44100:cl=stereo", "-vf", "fps=30,format=yuv420p,zoompan=z='min(1+0.0008*on,1.05)':d=1:s=1080x1920:fps=30",
             "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-shortest", seg])
        segs.append(seg)
    lst = f"{tmp}/l.txt"; open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    joined = f"{tmp}/j.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", joined])
    if spec.get("voice"):
        run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-i", P(spec["voice"]), "-filter_complex",
             "[1:a]volume=1.6,apad[vo];[0:a][vo]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-c", "copy", "-movflags", "+faststart", out])
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
