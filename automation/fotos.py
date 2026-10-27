"""Blewprint · Busca y descarga fotos y videos de Pixabay para las escenas "foto" y "video" de un reel.
Uso: python3 -I fotos.py <reel.json> <carpeta_media>
Lee PIXABAY_KEY del entorno. Cada escena {"tipo":"foto"|"video","busqueda":"...","busqueda2":"..."} recibe
"img" o "vid" (ruta local) y "credito". Si no hay clave, red o resultados, la escena queda sin archivo
(reel.py la convierte en texto). No repite la misma foto o video en el mismo reel. Reescribe reel.json."""
import json, os, sys, urllib.request, urllib.parse

spec_path, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
spec = json.load(open(spec_path))
key = os.environ.get('PIXABAY_KEY', '').strip()
usadas = set()

def api(path, **kw):
    params = dict(key=key, safesearch='true', per_page=20, **kw)
    req = urllib.request.Request(f'https://pixabay.com/api/{path}?' + urllib.parse.urlencode(params), headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get('hits', [])

def bajar(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
        f.write(r.read())

for i, e in enumerate(spec['escenas']):
    tipo = e.get('tipo')
    if tipo not in ('foto', 'video'):
        continue
    e.pop('img', None); e.pop('vid', None)
    if not key:
        print('sin PIXABAY_KEY: escena', i, 'queda como texto'); continue
    try:
        h = None
        for q in [e.get('busqueda', ''), e.get('busqueda2', '')]:
            if not q: continue
            if tipo == 'foto':
                hits = api('', q=q[:100], image_type='photo', orientation='vertical', min_height=1600)
                if not hits: hits = api('', q=q[:100], image_type='photo', min_width=1600)
            else:
                hits = [x for x in api('videos/', q=q[:100]) if x.get('duration', 0) >= min(e.get('dur', 3), 6)]
            hits = [x for x in hits if x['id'] not in usadas]
            if hits: h = hits[0]; break
        if not h:
            print('sin resultados:', e.get('busqueda')); continue
        usadas.add(h['id'])
        if tipo == 'foto':
            dest = os.path.join(outdir, f'foto-{i}-{h["id"]}.jpg'); bajar(h['largeImageURL'], dest); e['img'] = dest
        else:
            v = h['videos']; src = (v.get('medium') or {}).get('url') or (v.get('small') or {}).get('url') or (v.get('large') or {}).get('url')
            dest = os.path.join(outdir, f'video-{i}-{h["id"]}.mp4'); bajar(src, dest); e['vid'] = dest
        e['credito'] = f'{"Foto" if tipo == "foto" else "Video"}: {h.get("user", "")} / Pixabay'
        print('ok', tipo, e.get('busqueda'), '->', dest)
    except Exception as ex:
        print('error en escena', i, ex)
json.dump(spec, open(spec_path, 'w'), ensure_ascii=False, indent=1)
