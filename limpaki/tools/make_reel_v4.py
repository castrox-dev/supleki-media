#!/usr/bin/env python3
"""Reel 9:16 (v4) com clipes reais + legenda animada (fade+slide, 2 linhas, palavras destacadas) + zoom suave por cena + card final premium.
Extras no spec: clip.zoom [z0,z1] (punch-in suave), cap.hl ["BH","2026"] (palavras em turquesa), cap.text com \n pra quebrar linha.

Uso: python3 make_reel_v3.py spec.json out.mp4

Spec:
{
  "voice": "../audio/13_voz.mp3",        (opcional)
  "clip_volume": 0.25,                    (som ambiente dos clipes)
  "clips": [
    {"src": "../brutos/13_cena1.mp4", "start": 0, "dur": 8,
     "caps": [{"t": 0.0, "end": 4.5, "text": "Sábado de manhã...", "big": true}],
     "overlays": [{"png": "../iscas/17_moldura.png", "t": 0, "end": 99}]}   (opcional: PNG 1080x1920 por cima)
  ],
  "voice_segments": [{"from": 0, "to": 4.5, "at": 0, "tempo": 1.0}],   (opcional: corta a narração em frases e põe cada uma no segundo certo do vídeo final)
  "end": {"pre": "Comenta", "word": "PLANO", "sub": "que eu te mando o plano B no direct", "dur": 3.0}
}
Legendas: caixa branca com texto escuro (Inter), "big" = hook em cima.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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


def caption_png(text, big, path, hl=()):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = F("InterDisplay-Black.otf", 84 if big else 66)
    lines = []
    for part in text.split("\n"):
        lines += wrap(d, part, f, 900)
    lh = 98 if big else 80
    bh = len(lines) * lh + 50
    y0 = 260 if big else H - 560 - bh
    bw = max(d.textlength(l, font=f) for l in lines) + 80
    # sombra suave + caixa
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle(((W - bw) / 2, y0 + 10, (W + bw) / 2, y0 + bh + 10), 34, fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); img.alpha_composite(sh); d = ImageDraw.Draw(img)
    d.rounded_rectangle(((W - bw) / 2, y0, (W + bw) / 2, y0 + bh), 34, fill=(255, 255, 255, 242))
    d.rounded_rectangle(((W - bw) / 2, y0 + bh - 10, (W + bw) / 2, y0 + bh), 5, fill=TURQ + (255,))
    hl = {h.lower() for h in hl}
    y = y0 + 22
    for l in lines:
        x = (W - d.textlength(l, font=f)) / 2
        for i, w in enumerate(l.split()):
            s_ = w + (" " if i < len(l.split()) - 1 else "")
            core = w.strip(".,:!?()")
            col = TURQ_D if ((core.isupper() and len(core) > 1) or core.lower() in hl) else INK
            d.text((x, y), s_, font=f, fill=col); x += d.textlength(s_, font=f)
        y += lh
    img.save(path)


NAVY = (11, 42, 64)


def end_card(e, path):
    img = Image.new("RGB", (W, H), TURQ)
    g = Image.linear_gradient("L").resize((W, H)).rotate(12)
    img = Image.composite(Image.new("RGB", (W, H), TURQ_D), img, g.point(lambda p: int(p * .35)))
    d = ImageDraw.Draw(img, "RGBA")
    # formas sutis em azul-escuro
    d.ellipse((-320, 1380, 520, 2220), fill=NAVY + (60,))
    d.ellipse((700, -260, 1400, 440), fill=NAVY + (45,))
    d.ellipse((860, 1500, 1180, 1820), fill=(255, 255, 255, 28))
    fp = F("InterDisplay-Black.otf", 110); fw = F("InterDisplay-Black.otf", 250 if len(e["word"]) <= 3 else 150)
    y = 600
    d.text(((W - d.textlength(e["pre"], font=fp)) / 2, y), e["pre"], font=fp, fill=WHITE); y += 150
    bh_ = 300 if len(e["word"]) <= 3 else 200
    tw = d.textlength(e["word"], font=fw) + 120
    d.rounded_rectangle(((W - tw) / 2 + 8, y + 14, (W + tw) / 2 + 8, y + bh_ + 14), 70, fill=NAVY + (90,))
    d.rounded_rectangle(((W - tw) / 2, y, (W + tw) / 2, y + bh_), 70, fill=WHITE)
    d.text(((W - tw) / 2 + 60, y + (18 if bh_ == 200 else 10)), e["word"], font=fw, fill=TURQ_D); y += bh_ + 70
    fs = F("Inter-SemiBold.otf", 58)
    for l in wrap(d, e["sub"], fs, 860):
        d.text(((W - d.textlength(l, font=fs)) / 2, y), l, font=fs, fill=SOFT); y += 72
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
        sp = c.get("speed", 1.0); hold = c.get("hold", 0)
        zm = c.get("zoom")
        zflt = ""
        if zm:
            n = int(round((c["dur"] / sp + hold) * 30))
            zflt = f",zoompan=z='{zm[0]}+({zm[1]}-{zm[0]})*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30"
        flt = (f"[0:v]setpts=PTS/{sp},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30"
               + (f",tpad=stop_mode=clone:stop_duration={hold}" if hold else "") + zflt + "[v0]")
        last = "v0"
        for j, cap in enumerate(c.get("caps", [])):
            png = f"{tmp}/c{i}_{j}.png"; caption_png(cap["text"], cap.get("big"), png, cap.get("hl", ()))
            T, E = cap["t"], cap["end"]; a = 0.28
            inputs += ["-loop", "1", "-t", str(c["dur"] / sp + hold), "-i", png]
            flt += (f";[{j+1}:v]format=rgba,fade=t=in:st={T}:d={a}:alpha=1[ck{j}]"
                    f";[{last}][ck{j}]overlay=0:'40*max(0,({a}-(t-{T}))/{a})':enable='between(t,{T},{E})'[v{j+1}]")
            last = f"v{j+1}"
        for ov in c.get("overlays", []):  # PNGs prontos (ex.: moldura de campanha), mesma regra de t/end
            inputs += ["-i", P(ov["png"])]
            idx = 1 + len(c.get("caps", [])) + len([o for o in c.get("overlays", []) if o is not ov][:c["overlays"].index(ov)])
            flt += f";[{last}][{idx}:v]overlay=0:0:enable='between(t,{ov.get('t', 0)},{ov.get('end', 999)})'[o{idx}]"
            last = f"o{idx}"
        seg = f"{tmp}/s{i}.mp4"
        vol = spec.get("clip_volume", 0.25)
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", flt + f";[0:a]volume={vol},aresample=44100,apad[a]",
             "-map", f"[{last}]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-ar", "44100", "-ac", "2", "-t", str(c["dur"] / sp + hold), seg])
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
        vs = spec.get("voice_segments")
        if vs:
            parts = []
            for k, v in enumerate(vs):
                tempo = v.get("tempo", 1.0)
                parts.append(f"[1:a]atrim={v['from']}:{v['to']},asetpts=PTS-STARTPTS,atempo={tempo},adelay={int(v['at']*1000)}:all=1[p{k}]")
            vflt = ";".join(parts) + ";" + "".join(f"[p{k}]" for k in range(len(vs))) + f"amix=inputs={len(vs)}:normalize=0,volume=1.6,apad[vo]"
        else:
            vflt = "[1:a]volume=1.6,apad[vo]"
        extra, mflt = [], ";[0:a][vo]amix=inputs=2:duration=first:normalize=0[a]"
        if spec.get("music"):
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import wave, numpy as np
            from make_reel_v2 import music, SR
            total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", joined],
                                         capture_output=True, text=True).stdout)
            m = music(total); m = m / max(1e-9, np.max(np.abs(m))) * 0.9
            mw = f"{tmp}/m.wav"
            with wave.open(mw, "w") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((m * 32767).astype(np.int16).tobytes())
            extra = ["-i", mw]
            mv = spec.get("music_vol", 0.12)
            mflt = (f";[2:a]volume={mv}[mu];[mu][vo]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[mud];"
                    "[0:a][vo][mud]amix=inputs=3:duration=first:normalize=0[a]")
            vflt = vflt.replace("apad[vo]", "apad,asplit=2[vo][vsc]").replace("[mu][vo]side", "[mu][vsc]side")
            mflt = mflt.replace("[mu][vo]side", "[mu][vsc]side")
        run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-i", P(spec["voice"]), *extra, "-filter_complex",
             vflt + mflt,
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-c", "copy", "-movflags", "+faststart", out])
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
