"""Blewprint · Reel dinámico v3 (1080x1920, 30 fps) con fotos, videos de fondo, música y efectos.
Uso: python3 -I reel.py <reel.json> <salida.mp4> <estudio.html|fonts.css>
reel.json = {"fecha","kicker","escenas":[...]}; cada escena tiene "tipo" y "dur" (s):
  golpe:    {"html": "Frase con <em>clave</em>."}
  contador: {"valor": 22.1, "dec": 1, "pre": "+", "suf": "%", "texto": "..."}
  barras:   {"titulo": "...", "barras": [{"etiqueta","valor","texto"}]}
  texto:    {"texto": "..."}                       (aparece palabra por palabra)
  foto:     {"img": ruta local, "texto", "cifra"?, "credito"?}   (zoom lento, teñida de azul)
  video:    {"vid": ruta local mp4, "texto", "cifra"?, "credito"?} (video de fondo teñido)
  pregunta: {"texto": "..."}
Si a una escena foto/video le falta su archivo, se convierte en texto. Requiere ffmpeg y sonido.py al lado."""
import json, sys, os, re, asyncio, subprocess, tempfile, shutil, base64, mimetypes
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sonido

spec = json.load(open(sys.argv[1])); out = sys.argv[2]
src = open(sys.argv[3]).read(); FONTS = "\n".join(re.findall(r'@font-face\{[^}]*\}', src)) or src
FPS = 30
for e in spec['escenas']:
    if e['tipo'] == 'foto':
        p = e.get('img', '')
        if p and os.path.exists(p):
            e['img'] = 'data:' + (mimetypes.guess_type(p)[0] or 'image/jpeg') + ';base64,' + base64.b64encode(open(p, 'rb').read()).decode()
        else:
            e['tipo'] = 'texto'
    if e['tipo'] == 'video' and not (e.get('vid') and os.path.exists(e['vid'])):
        e['tipo'] = 'texto'
t0 = 0.0
for e in spec['escenas']:
    e['a'] = round(t0, 3); t0 += e['dur']; e['b'] = round(t0, 3)
DUR = t0

HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>%%FONTS%%
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:transparent}
#s{position:relative;width:1080px;height:1920px;overflow:hidden;color:#F4F1E8;font-family:"Space Grotesk"}
#solid{position:absolute;inset:0;background:#0F2E73}
#grid{position:absolute;inset:-180px;background-image:linear-gradient(#3B5A9E55 1px,transparent 1px),linear-gradient(90deg,#3B5A9E55 1px,transparent 1px);background-size:120px 120px}
#flash{position:absolute;inset:0;background:#FF5B1F;opacity:0;z-index:8}
#wipe{position:absolute;top:-200px;bottom:-200px;width:1300px;left:-2000px;background:#FF5B1F;z-index:9;transform:skewX(-12deg)}
header{position:absolute;left:80px;right:80px;top:120px;display:flex;justify-content:space-between;align-items:center;font:500 28px "IBM Plex Mono";letter-spacing:4px;z-index:6}
.brand{font:700 50px "Space Grotesk";letter-spacing:-1px}.brand b{color:#FF5B1F}
.kick{position:absolute;left:80px;top:230px;font:500 28px "IBM Plex Mono";letter-spacing:5px;text-transform:uppercase;color:#FF8A5B;z-index:6}
.sc{position:absolute;left:80px;right:80px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;opacity:0}
.golpe h1{font:700 150px/0.92 "Space Grotesk";letter-spacing:-6px}
.golpe h1 em{font-style:normal;color:#FF5B1F}
.contador .num{font:700 300px/0.9 "Space Grotesk";letter-spacing:-14px;color:#FF5B1F;white-space:nowrap}
.contador p{font:700 64px/1.08 "Space Grotesk";letter-spacing:-2px;margin-top:30px}
.barras h2{font:700 70px/1.05 "Space Grotesk";letter-spacing:-2px;margin-bottom:80px}
.bars{display:flex;gap:50px;align-items:flex-end;height:640px;border-bottom:4px solid #F4F1E8}
.bar{flex:1;display:flex;flex-direction:column;justify-content:flex-end;height:100%;position:relative}
.bar .v{font:700 78px "Space Grotesk";letter-spacing:-3px;margin-bottom:16px}
.bar .f{border-radius:16px 16px 0 0;height:0;background:#FF5B1F}
.bar.neg .f{background:repeating-linear-gradient(135deg,#F4F1E866 0 12px,#F4F1E822 12px 24px)}
.bar .l{position:absolute;bottom:-90px;font:500 28px/1.2 "IBM Plex Mono";letter-spacing:3px;text-transform:uppercase;opacity:.85}
.texto p,.media p{font:700 92px/1.04 "Space Grotesk";letter-spacing:-3px}
.w{display:inline-block;opacity:0;transform:translateY(40px)}
.n{color:#FF5B1F}
.pregunta p{font:700 100px/1.0 "Space Grotesk";letter-spacing:-4px}
.pregunta .h{margin-top:70px;font:500 44px "IBM Plex Mono";letter-spacing:3px;color:#FF8A5B}
.media{left:0;right:0;padding:0 80px}
.media .bg{position:absolute;inset:0;background-size:cover;background-position:center;filter:grayscale(1) contrast(1.15) brightness(.9)}
.media .t1{position:absolute;inset:0;background:#1B3F94;mix-blend-mode:multiply;opacity:.55}
.media.video .t1{mix-blend-mode:normal;opacity:.45}
.media .t2{position:absolute;inset:0;background:linear-gradient(180deg,#0F2E73cc 0%,#0F2E7322 38%,#0F2E73f0 74%)}
.media .cnt{position:relative;margin-top:560px}
.media .big{font:700 230px/0.9 "Space Grotesk";letter-spacing:-10px;color:#FF5B1F;white-space:nowrap}
.media p{font-size:78px;margin-top:20px}
.media .cred{position:absolute;right:80px;bottom:270px;font:500 20px "IBM Plex Mono";opacity:.6}
.bar2{position:absolute;left:80px;right:80px;bottom:200px;height:10px;background:#F4F1E822;border-radius:10px;overflow:hidden;z-index:6}.bar2 i{display:block;height:100%;width:0;background:#FF5B1F}
footer{position:absolute;left:80px;right:80px;bottom:120px;display:flex;justify-content:space-between;font:500 28px "IBM Plex Mono";letter-spacing:4px;opacity:.8;z-index:6}
</style></head><body><div id="s"><div id="solid"></div><div id="grid"></div>
<div id="scs"></div><div id="flash"></div><div id="wipe"></div>
<header><div class="brand"><b>blew</b>print</div><div>%%FECHA%%</div></header><div class="kick">%%KICK%%</div>
<div class="bar2"><i id="pb"></i></div><footer><span>@BLEWPRINT.MX</span><span>LO QUE SOPLÓ HOY</span></footer></div>
<script>
const E=%%E%%, DUR=%%DUR%%;
const esc=s=>(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const hiw=s=>esc(s).split(/\s+/).map(w=>'<span class="w'+(/\d/.test(w)?' n':'')+'">'+w+'</span>').join(' ');
const host=document.getElementById('scs');
E.forEach(e=>{const d=document.createElement('div');d.className='sc '+e.tipo;
 if(e.tipo=='golpe')d.innerHTML='<h1>'+e.html+'</h1>';
 if(e.tipo=='contador')d.innerHTML='<div class="num"></div><p>'+esc(e.texto)+'</p>';
 if(e.tipo=='barras')d.innerHTML='<h2>'+esc(e.titulo)+'</h2><div class="bars">'+e.barras.map(b=>'<div class="bar '+(b.valor<0?'neg':'')+'" data-v="'+b.valor+'"><div class="v">'+esc(b.texto)+'</div><div class="f"></div><div class="l">'+esc(b.etiqueta)+'</div></div>').join('')+'</div>';
 if(e.tipo=='texto')d.innerHTML='<p>'+hiw(e.texto)+'</p>';
 if(e.tipo=='foto'||e.tipo=='video'){d.className='sc media '+e.tipo;
   d.innerHTML=(e.tipo=='foto'?'<div class="bg" style="background-image:url('+e.img+')"></div>':'')+'<div class="t1"></div><div class="t2"></div><div class="cnt">'+(e.cifra?'<div class="big" style="font-size:'+Math.min(230,Math.floor(1650/e.cifra.length))+'px">'+esc(e.cifra)+'</div>':'')+'<p>'+hiw(e.texto)+'</p></div>'+(e.credito?'<div class="cred">'+esc(e.credito)+'</div>':'');}
 if(e.tipo=='pregunta')d.innerHTML='<p>'+hiw(e.texto)+'</p><div class="h">@blewprint.mx</div>';
 host.appendChild(d)});
const cl=x=>Math.min(Math.max(x,0),1), ease=x=>1-Math.pow(1-cl(x),3), back=x=>{x=cl(x);const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const fmt=(v,d)=>v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
window.render=t=>{
 document.getElementById('grid').style.transform=`translate(${-(t*14)%120}px,${-(t*22)%120}px)`;
 document.getElementById('pb').style.width=(100*t/DUR)+'%';
 let fl=0, wipe=-1, cur=null;
 [...host.children].forEach((el,i)=>{const e=E[i], k=t-e.a, vis=t>=e.a&&t<e.b;
  el.style.opacity=vis?1:0; if(!vis)return; cur=e;
  if(i>0&&k<0.28)wipe=k/0.28;
  if(k<0.1)fl=Math.max(fl,0.3*(1-k/0.1));
  let shake=0; if((e.tipo=='golpe'||e.tipo=='contador')&&k<0.35)shake=(1-k/0.35)*14;
  const sx=shake*Math.sin(t*90), sy=shake*Math.cos(t*70), s=1+0.05*(k/e.dur);
  if(e.tipo=='golpe')el.style.transform=`translate(${sx}px,${sy}px) scale(${(0.55+0.45*back(k/0.3))*s})`;
  else if(e.tipo=='foto'||e.tipo=='video'){el.style.transform='none';const bg=el.querySelector('.bg');if(bg)bg.style.transform=`scale(${1.1+0.15*(k/e.dur)}) translate(${-20*(k/e.dur)}px,${-35*(k/e.dur)}px)`;
    const big=el.querySelector('.big');if(big){big.style.transform=`translateX(${(1-ease(k/0.4))*-120}px)`;big.style.opacity=ease(k/0.3);}}
  else el.style.transform=`translate(${sx}px,${(1-ease(k/0.3))*90+sy}px) scale(${s})`;
  el.querySelectorAll('.w').forEach((w,j)=>{const p=ease((k-0.15-j*0.07)/0.25);w.style.opacity=p;w.style.transform=`translateY(${(1-p)*40}px)`;});
  if(e.tipo=='contador'){const n=el.querySelector('.num');n.textContent=(e.pre||'')+fmt(e.valor*ease(k/1.2),e.dec||0)+(e.suf||'');n.style.fontSize=Math.min(300,Math.floor(2000/n.textContent.length))+'px';}
  if(e.tipo=='barras'){const bs=[...el.querySelectorAll('.bar')],mx=Math.max(...bs.map(b=>Math.abs(+b.dataset.v)));
   bs.forEach((b,j)=>{const p=ease((k-0.3-j*0.35)/0.6);b.querySelector('.f').style.height=(Math.max(Math.abs(+b.dataset.v)/mx*440,22)*p)+'px';b.querySelector('.v').style.opacity=p;});}
 });
 const isv=cur&&cur.tipo=='video';
 document.getElementById('solid').style.opacity=isv?0:1;
 document.getElementById('grid').style.opacity=isv?0.25:1;
 document.getElementById('flash').style.opacity=fl;
 document.getElementById('wipe').style.left=(wipe<0?-2000:(-1700+wipe*3400))+'px';
};
</script></body></html>"""

def eventos():
    ev = []
    for i, e in enumerate(spec['escenas']):
        a = e['a']
        if i > 0: ev.append((max(0, a - 0.12), 'whoosh'))
        if e['tipo'] in ('golpe', 'contador'): ev.append((a, 'impacto'))
        if e['tipo'] == 'contador':
            ev += [(a + 0.1 + j * 0.08, 'tick') for j in range(13)]
        if e['tipo'] == 'barras':
            ev += [(a + 0.3 + j * 0.35, 'pop') for j in range(len(e['barras']))]
        if e['tipo'] == 'pregunta':
            ev.append((max(0, a - 1.2), 'riser')); ev.append((a, 'cierre'))
    return ev

async def main():
    tmp = tempfile.mkdtemp(); fr = os.path.join(tmp, 'f'); os.makedirs(fr)
    page = os.path.join(tmp, 'r.html')
    html = (HTML.replace('%%FONTS%%', FONTS).replace('%%FECHA%%', spec.get('fecha', ''))
            .replace('%%KICK%%', spec.get('kicker', '')).replace('%%E%%', json.dumps(spec['escenas'], ensure_ascii=False))
            .replace('%%DUR%%', str(DUR)))
    open(page, 'w').write(html)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.route('**/*', lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
        await pg.goto('file://' + page); await pg.evaluate('document.fonts.ready')
        for k in range(int(DUR * FPS)):
            await pg.evaluate(f'render({k / FPS})')
            await pg.screenshot(path=os.path.join(fr, f'{k:05d}.png'), omit_background=True)
        await b.close()
    wav = os.path.join(tmp, 'a.wav'); sonido.pista(DUR, eventos(), wav, semilla=len(spec['escenas']))
    # fondo: color + videos en sus tramos + capa de gráficos + audio
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'color=c=0x0F2E73:s=1080x1920:r={FPS}:d={DUR}']
    vids = [e for e in spec['escenas'] if e['tipo'] == 'video']
    for e in vids:
        cmd += ['-stream_loop', '-1', '-t', str(e['dur'] + 0.5), '-i', e['vid']]
    cmd += ['-framerate', str(FPS), '-i', os.path.join(fr, '%05d.png'), '-i', wav]
    fc = []; last = '[0:v]'
    for j, e in enumerate(vids):
        fc.append(f'[{j+1}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={FPS},hue=s=0,eq=contrast=1.1:brightness=-0.05,setpts=PTS-STARTPTS+{e["a"]}/TB[v{j}]')
        fc.append(f'{last}[v{j}]overlay=enable=\'between(t,{e["a"]},{e["b"]})\':eof_action=pass[b{j}]'); last = f'[b{j}]'
    gi = len(vids) + 1
    fc.append(f'{last}[{gi}:v]overlay=format=auto,format=yuv420p[out]')
    cmd += ['-filter_complex', ';'.join(fc), '-map', '[out]', '-map', f'{gi+1}:a', '-t', str(DUR),
            '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '160k', out]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp); print(out, f'{DUR:.1f}s', len(spec['escenas']), 'escenas,', len(vids), 'videos')

asyncio.run(main())
