"""Renderiza las piezas del Estudio Blewprint a JPEG sin intervención.
Uso: python3 -I render.py <estudio.html> <edicion.json> <outdir>
(estudio.html = página del Estudio guardada por Artifact read; edicion.json = la edición del día)
Escribe outdir/<key>-NN.jpg y outdir/manifest.json con los posts (key, hora, tipo, caption, li, titulo, imagenes)."""
import json, sys, asyncio, os
from playwright.async_api import async_playwright
html_path, ed_path, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
ed = json.load(open(ed_path))
MOCK = """
window.__ED__ = %s;
window.claude = { use: async (cap) => {
  if (cap !== 'db') return null;
  const snap = (docs)=>({docs: docs.map(([id,d])=>({id, data:()=>d}))});
  const coll = (name)=>{ const q = { orderBy(){return q}, limit(){return q},
     onSnapshot(cb){ setTimeout(()=>cb(snap(name==='ediciones'?[[window.__ED__.fecha, window.__ED__]]:[])),0); return ()=>{}; } }; return q; };
  return { collection: coll, doc: ()=>({get: async()=>({exists:false}), set: async()=>{}}) };
}};
""" % json.dumps(ed, ensure_ascii=False)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width':1400,'height':1000})
        await pg.route('**/*', lambda r: r.abort() if r.request.url.startswith('http') else r.continue_())
        await pg.add_init_script(MOCK)
        await pg.goto('file://' + os.path.abspath(html_path))
        await pg.wait_for_function("document.querySelector('#main')?._ps?.length > 0", timeout=30000)
        await pg.evaluate("document.fonts.ready")
        posts = await pg.evaluate("""() => { const e = editions[current], ps = $('#main')._ps;
            return postsDe(e, ps).map(p=>({key:p.key, hora:p.hora, titulo:p.titulo, caption:p.caption, li:p.li||'', tipo:p.tipo, idx:p.idx, w:p.idx.map(i=>ps[i].w), h:p.idx.map(i=>ps[i].h)})); }""")
        bad = []
        for post in posts:
            files = []
            for k, i in enumerate(post['idx']):
                ok = await pg.evaluate("""async (i)=>{ await document.fonts.ready;
                    const fr = document.querySelector(`.frame[data-i="${i}"]`), piece = fr.firstElementChild, p = $('#main')._ps[i];
                    const host = document.getElementById('__host') || Object.assign(document.body.appendChild(document.createElement('div')),{id:'__host'});
                    host.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#000';
                    host.innerHTML=''; const c = piece.cloneNode(true); c.style.transform='none'; c.style.position='relative'; host.appendChild(c);
                    host.style.width=p.w+'px'; host.style.height=p.h+'px';
                    fit(host); noClash(c);
                    const fonts = ['700 52px "Space Grotesk"','500 26px "IBM Plex Mono"','400 40px "Source Serif 4"'].every(f=>document.fonts.check(f));
                    return {clash:c.dataset.clash, fonts}; }""", i)
                name = f"{post['key']}-{k+1:02d}.jpg"
                await pg.set_viewport_size({'width':max(post['w'][k],1400),'height':max(post['h'][k],1000)})
                await pg.locator('#__host').screenshot(path=os.path.join(out,name), type='jpeg', quality=85)
                if ok['clash']=='1' or not ok['fonts']: bad.append({'file':name, **ok})
                files.append(name)
            post['imagenes'] = files
            del post['idx'], post['w'], post['h']
        json.dump({'fecha':ed['fecha'], 'posts':posts, 'problemas':bad}, open(os.path.join(out,'manifest.json'),'w'), ensure_ascii=False, indent=1)
        print(len(posts), 'posts,', sum(len(x['imagenes']) for x in posts), 'imagenes, problemas:', bad)
        await b.close()
asyncio.run(main())
