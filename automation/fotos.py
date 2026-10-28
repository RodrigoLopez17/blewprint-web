"""Blewprint · Busca y descarga fotos y videos de Pixabay para un reel.
Uso: python3 -I fotos.py <reel.json> <carpeta_media>
Lee PIXABAY_KEY del entorno.
- Escenas "foto" y "video" con "busqueda"/"busqueda2": reciben "img" o "vid" (ruta local) y "credito".
- Cualquier otra escena con "busqueda" (hook, texto, contador, pregunta) recibe una foto de fondo en "img".
  El hook sin "busqueda" usa la búsqueda de la primera escena foto/video.
- Además guarda en spec["fondos"] hasta 4 fotos extra (segundos resultados de las búsquedas) para que
  reel.py ponga foto de fondo en las pantallas que no tienen la suya.
Si no hay clave, red o resultados, la escena queda sin archivo (reel.py la resuelve). No repite archivos.
Reescribe reel.json."""
import json, os, sys, urllib.request, urllib.parse

spec_path, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
spec = json.load(open(spec_path))
key = os.environ.get('PIXABAY_KEY', '').strip()
usadas = set()
extras = []  # (busqueda) para fondos

def api(path, **kw):
    params = dict(key=key, safesearch='true', per_page=20, **kw)
    with urllib.request.urlopen(f'https://pixabay.com/api/{path}?' + urllib.parse.urlencode(params), timeout=20) as r:
        return json.load(r).get('hits', [])

def bajar(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
        f.write(r.read())

def fotos(q):
    hits = api('', q=q[:100], image_type='photo', orientation='vertical', min_height=1600)
    if len(hits) < 3: hits += api('', q=q[:100], image_type='photo', min_width=1600)
    return [x for x in hits if x['id'] not in usadas]

def videos(q, dur):
    return [x for x in api('videos/', q=q[:100]) if x.get('duration', 0) >= min(dur, 6) and x['id'] not in usadas]

def poner_foto(e, i, consultas, campo='img'):
    for q in consultas:
        if not q: continue
        hits = fotos(q)
        if hits:
            h = hits[0]; usadas.add(h['id'])
            dest = os.path.join(outdir, f'foto-{i}-{h["id"]}.jpg'); bajar(h['largeImageURL'], dest)
            e[campo] = dest; e['credito'] = f'Foto: {h.get("user", "")} / Pixabay'
            print('ok foto', e.get('tipo'), q, '->', dest); return True
    print('sin resultados:', consultas); return False

escenas = spec['escenas']
primera_busqueda = next((e.get('busqueda') for e in escenas if e.get('tipo') in ('foto', 'video') and e.get('busqueda')), '')
for i, e in enumerate(escenas):
    e.pop('vid', None)
    if e.get('tipo') == 'foto' or e.get('busqueda') or e.get('tipo') in ('hook', 'golpe'):
        e.pop('img', None)
if not key:
    print('sin PIXABAY_KEY: las escenas quedan sin foto')
else:
    for i, e in enumerate(escenas):
        tipo = e.get('tipo')
        try:
            if tipo == 'video':
                h = None
                for q in [e.get('busqueda', ''), e.get('busqueda2', '')]:
                    if not q: continue
                    hits = videos(q, e.get('dur', 3))
                    if hits: h = hits[0]; break
                if not h:
                    print('sin videos:', e.get('busqueda')); continue
                usadas.add(h['id'])
                v = h['videos']; srcu = (v.get('medium') or {}).get('url') or (v.get('small') or {}).get('url') or (v.get('large') or {}).get('url')
                dest = os.path.join(outdir, f'video-{i}-{h["id"]}.mp4'); bajar(srcu, dest); e['vid'] = dest
                e['credito'] = f'Video: {h.get("user", "")} / Pixabay'; print('ok video', e.get('busqueda'), '->', dest)
                extras.append(e.get('busqueda'))
            elif tipo == 'foto':
                poner_foto(e, i, [e.get('busqueda', ''), e.get('busqueda2', '')]); extras.append(e.get('busqueda'))
            elif tipo in ('hook', 'golpe'):
                poner_foto(e, i, [e.get('busqueda', ''), e.get('busqueda2', ''), primera_busqueda])
            elif e.get('busqueda'):
                poner_foto(e, i, [e.get('busqueda', ''), e.get('busqueda2', '')])
        except Exception as ex:
            print('error en escena', i, ex)
    fondos = []
    for q in [x for x in extras if x][:4]:
        try:
            hits = fotos(q)
            if hits:
                h = hits[0]; usadas.add(h['id'])
                dest = os.path.join(outdir, f'fondo-{len(fondos)}-{h["id"]}.jpg'); bajar(h['largeImageURL'], dest)
                fondos.append(dest)
        except Exception as ex:
            print('error en fondo', q, ex)
    spec['fondos'] = fondos
    print('fondos:', len(fondos))
json.dump(spec, open(spec_path, 'w'), ensure_ascii=False, indent=1)
