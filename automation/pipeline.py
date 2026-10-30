"""Blewprint · Produce todo lo del día a partir de edicion.json, sin pasos a mano.
Uso: python3 -I pipeline.py <edicion.json> <estudio.html> <outdir> [--fuente recopilacion.txt] [--ahora HH:MM] [--sin-reels]
1. Valida la edición (validar.py); si hay errores, se detiene.
2. Renderiza los JPEG con render.py en <outdir> (posts con "problemas" no se programan).
3. Por cada video: fotos.py (Pixabay, lee PIXABAY_KEY) y reel.py en paralelo -> <outdir>/reel-i.mp4; revisa cada MP4
   con ffprobe (1080x1920, audio, 24-40 s) y saca cuadros a 1 s y 9 s en <outdir>-trabajo/cuadros/.
4. Escribe <outdir>-trabajo/publicar.json con cada llamada a createScheduledPost lista (blogId, date, info) y recorre
   las horas que ya pasaron o a las que faltan menos de 10 min (hora de Mérida, o --ahora).
En <outdir> quedan solo los archivos a publicar (JPEG y MP4) y manifest.json; lo demás va en <outdir>-trabajo/.
Al final imprime un resumen; sale con código 1 si no se puede programar nada."""
import json, os, re, sys, subprocess, datetime
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from validar import validar

BLOG, TZ = '7219940', 'America/Merida'
RAW = 'https://raw.githubusercontent.com/RodrigoLopez17/blewprint-web/media/{fecha}/{archivo}'
BASE_INFO = {'autoPublish': True, 'draft': False, 'descendants': [], 'firstCommentText': '', 'hasNotReadNotes': False,
             'mediaAltText': [], 'shortener': False, 'smartLinkData': {'ids': []}}

args = sys.argv[1:]
def opcion(nombre, con_valor=True):
    if nombre not in args: return None
    k = args.index(nombre); v = args[k + 1] if con_valor else True
    del args[k:k + (2 if con_valor else 1)]; return v
fuente_path, ahora_txt, sin_reels = opcion('--fuente'), opcion('--ahora'), opcion('--sin-reels', False)
ed_path, estudio, out = args[:3]
trabajo = out.rstrip('/') + '-trabajo'
os.makedirs(out, exist_ok=True); os.makedirs(os.path.join(trabajo, 'cuadros'), exist_ok=True)
ed = json.load(open(ed_path, encoding='utf-8'))
fecha = ed['fecha']

def py(script, *a, **kw):
    return subprocess.run([sys.executable, '-I', os.path.join(AQUI, script), *a], capture_output=True, text=True, **kw)

# 1. Validar
errores, avisos = validar(ed, open(fuente_path, encoding='utf-8').read() if fuente_path else '')
for a in avisos: print('AVISO', a)
if errores:
    for e in errores: print('ERROR', e)
    sys.exit('Edición inválida: corrige edicion.json y vuelve a correr.')

# 2. Imágenes
for intento in range(2):  # Playwright a veces no arranca a la primera ("Connection closed while reading from the driver")
    r = py('render.py', estudio, ed_path, out, timeout=600)
    print(r.stdout.strip() or r.stderr.strip()[-2000:])
    if r.returncode == 0: break
else: sys.exit('render.py falló dos veces')
man = json.load(open(os.path.join(out, 'manifest.json'), encoding='utf-8'))
malos = {p['file'].rsplit('-', 1)[0] for p in man['problemas']}

# 3. Reels
reels, fallas = [], []
if not sin_reels:
    procs = []
    for i, v in enumerate(ed.get('videos', []), 1):
        spec = os.path.join(trabajo, f'reel-{i}.json')
        json.dump({'fecha': ed['fechaLabel'], 'kicker': v['reel']['kicker'], 'escenas': v['reel']['escenas']},
                  open(spec, 'w', encoding='utf-8'), ensure_ascii=False)
        f = py('fotos.py', spec, os.path.join(trabajo, f'fotos-{i}'))
        print(f'reel {i} fotos:', (f.stdout + f.stderr).strip().replace('\n', ' | ')[-600:])
        mp4 = os.path.join(out, f'reel-{i}.mp4')
        procs.append((i, v, mp4, subprocess.Popen([sys.executable, '-I', os.path.join(AQUI, 'reel.py'), spec, mp4, estudio],
                                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
    for i, v, mp4, p in procs:
        salida = p.communicate()[0].strip()
        print(f'reel {i}:', salida.splitlines()[-1] if salida else '(sin salida)')
        try:
            info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height:format=duration',
                                              '-of', 'json', mp4], capture_output=True, text=True).stdout)
            vid = next(s for s in info['streams'] if s['codec_type'] == 'video')
            dur = float(info['format']['duration'])
            audio = any(s['codec_type'] == 'audio' for s in info['streams'])
            ok = p.returncode == 0 and (vid['width'], vid['height']) == (1080, 1920) and audio and 24 <= dur <= 40
        except Exception as ex:
            ok, dur, audio, vid = False, 0, False, {}
        for s in (1, 9):
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(s), '-i', mp4, '-frames:v', '1', '-vf', 'scale=540:-1',
                            os.path.join(trabajo, 'cuadros', f'reel-{i}-{s}s.jpg')])
        if ok: reels.append((i, v))
        else: fallas.append(f'reel-{i}: {vid.get("width")}x{vid.get("height")}, audio={audio}, {dur:.1f} s, código {p.returncode}\n{salida[-1500:]}')

# 4. Horarios y llamadas
ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6)))  # Mérida: UTC-6 todo el año
if ahora_txt:
    h, m = map(int, ahora_txt.split(':'))  # simula esa hora en el día de la edición
    ahora = datetime.datetime.strptime(fecha, '%Y-%m-%d').replace(hour=h, minute=m, tzinfo=ahora.tzinfo)
limite = (ahora + datetime.timedelta(minutes=10)).replace(tzinfo=None)
dia = datetime.datetime.strptime(fecha, '%Y-%m-%d')
def momento(hora): h, m = map(int, hora.split(':')); return dia.replace(hour=h, minute=m)
def siguiente(t, minutos):  # primer horario >= t cuyo minuto esté en "minutos"
    t = t.replace(second=0, microsecond=0)
    while t.minute not in minutos or t < limite: t += datetime.timedelta(minutes=1)
    return t
def hhmm(t): return f'{t.hour}:{t.minute:02d}'

recorridos, omitidos, items = [], [], []
posts = [p for p in man['posts'] if p['tipo'] == 'POST']
cur = None
for p in sorted(posts, key=lambda p: momento(p['hora'])):
    t = momento(p['hora'])
    if cur is not None and t < cur: t = cur
    if t < limite: t = siguiente(limite, (0, 30))
    if hhmm(t) != p['hora']: recorridos.append(f'{p["key"]}: {p["hora"]} -> {hhmm(t)}')
    items.append((p, t)); cur = t + datetime.timedelta(minutes=30)
for p in man['posts']:
    if p['tipo'] == 'STORY':
        t = momento(p['hora'])
        if t < limite: t = siguiente(limite, (0, 30)); recorridos.append(f'{p["key"]}: {p["hora"]} -> {hhmm(t)}')
        items.append((p, t))
usadas = set()
for i, v in reels:
    t = momento(v['hora'])
    if t < limite or t in usadas:
        t = siguiente(max(t, limite), (15, 45))
        while t in usadas: t = siguiente(t + datetime.timedelta(minutes=1), (15, 45))
        recorridos.append(f'reel{i}: {v["hora"]} -> {hhmm(t)}')
    usadas.add(t)
    items.append(({'key': f'reel{i}', 'tipo': 'REEL', 'titulo': v['titulo'], 'caption': v['caption'], 'li': '',
                   'imagenes': [f'reel-{i}.mp4']}, t))

def sin_hashtags(txt):
    lineas = txt.rstrip().split('\n')
    while lineas and (not lineas[-1].strip() or all(w.startswith('#') for w in lineas[-1].split())): lineas.pop()
    return '\n'.join(lineas).rstrip() + '\n\nNotas completas en blewprint.mx'

llamadas = []
for p, t in sorted(items, key=lambda x: x[1]):
    if p['key'] in malos: omitidos.append(f'{p["key"]}: texto encimado o fuente faltante en render'); continue
    media = [RAW.format(fecha=fecha, archivo=a) for a in p['imagenes']]
    date = f'{fecha}T{t.hour:02d}:{t.minute:02d}:00-06:00'
    base = dict(BASE_INFO, media=media, publicationDate={'dateTime': date[:19], 'timezone': TZ})
    titulo = re.sub(r'^(Noticia:\s*)+', '', p['titulo']).strip()
    if p['tipo'] == 'STORY':
        igfb = dict(base, providers=[{'network': 'instagram'}, {'network': 'facebook'}],
                    instagramData={'type': 'STORY'}, facebookData={'type': 'STORY'})
    elif p['tipo'] == 'REEL':
        igfb = dict(base, providers=[{'network': 'instagram'}, {'network': 'facebook'}], text=p['caption'],
                    instagramData={'type': 'REEL', 'showReelOnFeed': True}, facebookData={'type': 'REEL', 'title': titulo})
    else:
        igfb = dict(base, providers=[{'network': 'instagram'}, {'network': 'facebook'}], text=p['caption'],
                    instagramData={'type': 'POST'}, facebookData={'type': 'POST'})
    llamadas.append({'key': p['key'], 'redes': 'instagram+facebook', 'tipo': p['tipo'], 'hora': hhmm(t), 'blogId': BLOG, 'date': date, 'info': igfb})
    if p['tipo'] != 'STORY':
        varias = len(media) > 1
        li = {'type': 'post', 'publishImagesAsPDF': varias, 'previewIncluded': True}
        if varias: li['documentTitle'] = titulo[:90]
        llamadas.append({'key': p['key'], 'redes': 'linkedin', 'tipo': p['tipo'], 'hora': hhmm(t), 'blogId': BLOG, 'date': date,
                         'info': dict(base, providers=[{'network': 'linkedin'}], text=sin_hashtags(p['li'] or p['caption']), linkedinData=li)})

json.dump({'fecha': fecha, 'blogId': BLOG, 'timezone': TZ, 'llamadas': llamadas, 'recorridos': recorridos, 'omitidos': omitidos,
           'reels_fallidos': fallas, 'avisos': avisos},
          open(os.path.join(trabajo, 'publicar.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n{len(llamadas)} llamadas listas en {trabajo}/publicar.json ({len({c["key"] for c in llamadas if c["tipo"] != "REEL"})} posts, {len(reels)} reels)')
for x in recorridos: print('RECORRIDO', x)
for x in omitidos: print('OMITIDO', x)
for x in fallas: print('REEL FALLIDO', x)
print('Cuadros para revisar:', os.path.join(trabajo, 'cuadros'))
sys.exit(0 if llamadas else 1)
