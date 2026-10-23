#!/usr/bin/env python3
"""Reel animado 1080x1920 (padrão Splash): fundo com foto desfocada em movimento,
foto real em card com ken burns, número gigante, título palavra por palavra,
ícone por cena, barra de progresso, transição com flash e slide, piscina
"ficando verde" no gancho. Renderizado quadro a quadro com Playwright + ffmpeg.

Uso: FONT_DIR=... python3 make_motion_reel.py spec.json saida.mp4 [audio.mp3]
"""
import asyncio, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_photo_carousel import font_face, b64, ROOT
from playwright.async_api import async_playwright

ICONS = {
 "drop": '<path d="M32 6C22 20 14 30 14 40a18 18 0 0 0 36 0C50 30 42 20 32 6z" fill="#fff"/>',
 "ph": '<rect x="22" y="6" width="20" height="52" rx="6" fill="#fff"/><rect x="22" y="38" width="20" height="20" rx="4" fill="#ffd23f"/><rect x="22" y="26" width="20" height="10" fill="#7fe08a"/>',
 "fan": '<circle cx="32" cy="32" r="6" fill="#fff"/><path d="M32 26c0-12 10-18 16-12s-4 14-16 12zM38 32c12 0 18 10 12 16s-14-4-12-16zM32 38c0 12-10 18-16 12s4-14 16-12zM26 32c-12 0-18-10-12-16s14 4 12 16z" fill="#fff"/>',
 "leaf": '<path d="M12 52C12 26 30 10 54 10c0 26-16 42-40 42z" fill="#fff"/><path d="M14 50L44 20" stroke="#E6157E" stroke-width="4" stroke-linecap="round"/>',
 "chat": '<path d="M10 14h44v28H28l-12 10v-10h-6z" fill="#fff"/>',
 "alert": '<path d="M32 6l26 48H6z" fill="#fff"/><rect x="29" y="22" width="6" height="18" rx="3" fill="#E6157E"/><circle cx="32" cy="46" r="3.5" fill="#E6157E"/>',
}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;background:#0b4aa6;color:#fff;font-family:'BarlowC6'}
.bg{position:absolute;inset:-120px;background-size:cover;background-position:center;filter:blur(34px) brightness(.62) saturate(1.2)}
.tint{position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,74,166,.55),rgba(11,74,166,.25) 35%,rgba(8,58,138,.85) 62%,#083a8a 80%)}
.card{position:absolute;left:50px;top:370px;width:980px;height:668px;border-radius:40px;overflow:hidden;border:10px solid #fff;
 box-shadow:0 30px 70px rgba(0,0,0,.45);transform-origin:50% 60%}
.card img{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;transform-origin:center}
.card .green{position:absolute;inset:0;opacity:0;-webkit-mask-image:radial-gradient(ellipse 55% 38% at 50% 72%,#000 55%,transparent 100%)}
.num{position:absolute;left:60px;top:118px;font-family:'Anton';font-size:230px;line-height:1;color:#fff;
 -webkit-text-stroke:5px #062f74;paint-order:stroke fill;opacity:.95;text-shadow:0 8px 0 #062f74}
.num b{color:#E6157E;-webkit-text-stroke:0}
.icon{position:absolute;right:70px;top:300px;width:150px;height:150px;border-radius:50%;background:#E6157E;
 box-shadow:0 12px 0 rgba(0,0,0,.2);display:flex;align-items:center;justify-content:center}
.icon svg{width:84px;height:84px}
.tag{position:absolute;left:72px;top:1090px;background:#E6157E;font-family:'BarlowC';font-weight:800;font-size:48px;letter-spacing:2px;
 padding:10px 34px 8px;border-radius:40px;box-shadow:0 6px 0 rgba(0,0,0,.2);text-transform:uppercase;transform-origin:left center}
.title{position:absolute;left:72px;right:60px;top:1180px;font-family:'Anton';font-size:140px;line-height:1.02;text-transform:uppercase}
.title span{display:inline-block;margin-right:28px;-webkit-text-stroke:3px #062f74;paint-order:stroke fill;text-shadow:0 8px 0 #062f74}
.title span.pk{color:#ff5fb0}
.title span.np{text-transform:none}
.note{position:absolute;left:72px;right:72px;font-family:'BarlowC6';font-size:56px;line-height:1.15;color:#e3efff}
.prog{position:absolute;left:72px;right:72px;top:80px;display:flex;gap:14px}
.prog i{flex:1;height:12px;border-radius:8px;background:rgba(255,255,255,.3);overflow:hidden;position:relative}
.prog i b{position:absolute;left:0;top:0;bottom:0;background:#E6157E;border-radius:8px}
.btn{position:absolute;left:72px;background:#25c766;font-family:'BarlowC';font-weight:800;font-size:56px;padding:24px 46px 20px;border-radius:70px;
 box-shadow:0 10px 0 rgba(0,0,0,.22);transform-origin:left center}
.logo{position:absolute;right:56px;bottom:100px;background:#fff;border-radius:28px;padding:12px 20px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.logo img{height:116px;display:block}
.loc{position:absolute;left:72px;bottom:134px;font-family:'BarlowC6';font-size:42px;color:#cfe2ff}
.bar{position:absolute;left:0;right:0;bottom:0;height:36px;background:#E6157E}
.flash{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none}
"""

JS = r"""
const S = window.SPEC; const T = S.cards.reduce((a,c)=>a+c.dur,0);
const $ = s => document.querySelector(s);
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const eo=x=>1-Math.pow(1-clamp(x),3);              // ease out cubic
const back=x=>{x=clamp(x);const c=1.9;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}; // overshoot
let built=-1;
function build(i){
  const c=S.cards[i]; built=i;
  $('.bg').style.backgroundImage=`url(${c.photo})`;
  $('.card img').src=c.photo; $('.card .green').style.backgroundImage=`url(${c.photo})`;
  $('.num').innerHTML=c.num?c.num.replace(/(\d)$/,'<b>$1</b>'):'';
  $('.icon').innerHTML=c.icon?`<svg viewBox="0 0 64 64">${window.ICONS[c.icon]}</svg>`:''; $('.icon').style.display=c.icon?'flex':'none';
  $('.tag').textContent=c.label||''; $('.tag').style.display=c.label?'block':'none';
  $('.title').innerHTML=c.words.map(w=>{let cls='';if(w.startsWith('*')){cls='pk';w=w.slice(1)} if(w==='pH')cls+=' np';return `<span class="${cls}">${w}</span>`}).join('');
  $('.title').style.fontSize=(c.size||140)+'px';
  $('.note').textContent=c.note||'';
  $('.btn').textContent=c.btn||''; $('.btn').style.display=c.btn?'block':'none';
  document.querySelectorAll('.prog i').forEach((e,k)=>{e.parentNode.style.visibility=c.step?'visible':'hidden'});
}
window.render=function(t){
  let i=0,st=0; while(i<S.cards.length-1 && t>=st+S.cards[i].dur){st+=S.cards[i].dur;i++}
  if(i!==built) build(i);
  const c=S.cards[i], lt=t-st, d=c.dur, p=lt/d;
  // fundo: zoom lento
  $('.bg').style.transform=`scale(${1.05+0.08*p}) translateX(${(i%2?1:-1)*30*p}px)`;
  // card entra deslizando + girando
  const e=eo(lt/0.45);
  const rot=(i%2?-1:1)*(3-3*e) + (i%2?1:-1)*1.2;
  $('.card').style.transform=`translateX(${(1-e)*(i%2?-1100:1100)}px) rotate(${rot}deg) scale(${0.9+0.1*e})`;
  $('.card img').style.transform=`scale(${1.04+0.12*p}) translate(${(i%2?1:-1)*20*p}px,${-10*p}px)`;
  // gancho: água fica verde
  const g=c.green?clamp((lt-0.6)/1.4):0;
  $('.card .green').style.opacity=g; $('.card .green').style.filter='hue-rotate(-48deg) saturate(.95) brightness(.78) contrast(1.05)';
  $('.card .green').style.backgroundSize='cover'; $('.card .green').style.backgroundPosition='center';
  $('.card .green').style.transform=$('.card img').style.transform;
  // número gigante
  const n=back((lt-0.15)/0.45);
  $('.num').style.transform=`translateY(${(1-n)*-120}px) scale(${0.6+0.4*n})`; $('.num').style.opacity=clamp((lt-0.15)/0.2)*.95;
  // ícone pop + balanço
  const ic=back((lt-0.35)/0.4);
  $('.icon').style.transform=`scale(${ic}) rotate(${Math.sin(lt*5)*6}deg)`;
  // etiqueta
  const tg=back((lt-0.3)/0.35); $('.tag').style.transform=`scaleX(${tg})`; $('.tag').style.opacity=clamp((lt-0.3)/0.1);
  // título palavra por palavra
  document.querySelectorAll('.title span').forEach((s,k)=>{
    const w=back((lt-0.45-k*0.11)/0.35);
    s.style.transform=`translateY(${(1-w)*80}px) scale(${0.7+0.3*w})`; s.style.opacity=clamp((lt-0.45-k*0.11)/0.12);
  });
  // nota sobe depois do título
  const th=$('.title').getBoundingClientRect(); const nt=eo((lt-0.45-c.words.length*0.11-0.1)/0.4);
  $('.note').style.top=(th.bottom+26)+'px'; $('.note').style.transform=`translateY(${(1-nt)*40}px)`; $('.note').style.opacity=nt;
  // botão pulsa
  if(c.btn){ const b=back((lt-1.0)/0.4); const pulse=1+0.05*Math.max(0,Math.sin((lt-1.4)*6));
    $('.btn').style.top=(th.bottom+150)+'px'; $('.btn').style.transform=`scale(${b*pulse})`; }
  // progresso
  document.querySelectorAll('.prog i b').forEach((b,k)=>{ const s=(c.step||0)-1;
    b.style.width=(k<s?100:k===s?100*clamp(p*1.05):0)+'%'; });
  // flash na troca
  $('.flash').style.opacity=i>0?clamp(1-lt/0.18)*0.85:0;
};
"""


def main(spec, out, audio=None):
    sp = json.load(open(spec))
    fps = sp.get("fps", 30)
    for c in sp["cards"]:
        c["photo"] = b64(os.path.join(ROOT, c["photo"]))
    logo = b64(os.path.join(ROOT, "perfil/logo_splash_original.png"), crop=(80, 150, 1180, 1110), size=(330, 288), fmt="PNG")
    html = (f'<html><head><meta charset="utf-8"><style>{font_face()}{CSS}</style></head><body>'
            '<div class="bg"></div><div class="tint"></div>'
            '<div class="prog"><i><b></b></i><i><b></b></i><i><b></b></i><i><b></b></i></div>'
            '<div class="card"><img><div class="green"></div></div><div class="num"></div><div class="icon"></div>'
            '<div class="tag"></div><div class="title"></div><div class="note"></div><div class="btn"></div>'
            f'<div class="loc">Itaipuaçu | Maricá</div><div class="logo"><img src="{logo}"></div><div class="bar"></div>'
            '<div class="flash"></div></body></html>')
    total = sum(c["dur"] for c in sp["cards"])
    n = int(round(total * fps))
    args = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-"]
    if audio:
        args += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest"]
    else:
        args += ["-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    args += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(fps), "-movflags", "+faststart", out]
    ff = subprocess.Popen(args, stdin=subprocess.PIPE)

    async def run():
        async with async_playwright() as p:
            br = await p.chromium.launch()
            pg = await br.new_page(viewport={"width": 1080, "height": 1920})
            await pg.set_content(html)
            await pg.evaluate(f"window.SPEC={json.dumps(sp)};window.ICONS={json.dumps(ICONS)};")
            await pg.add_script_tag(content=JS)
            await pg.evaluate("document.fonts.ready")
            starts, acc = set(), 0
            for c in sp["cards"]:
                starts.add(int(round(acc * fps))); acc += c["dur"]
            for f in range(n):
                await pg.evaluate(f"render({f / fps})")
                if f in starts:
                    await pg.wait_for_timeout(250)
                    await pg.evaluate(f"render({f / fps})")
                ff.stdin.write(await pg.screenshot(type="jpeg", quality=88))
            await br.close()
    asyncio.run(run())
    ff.stdin.close(); ff.wait()


if __name__ == "__main__":
    main(*sys.argv[1:4])
