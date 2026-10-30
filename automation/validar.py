"""Blewprint · Valida edicion.json antes de renderizar.
Uso: python3 -I validar.py <edicion.json> [--fuente recopilacion.txt]
Revisa estructura, largos, horas, emojis y escenas del reel (portada "hook" v4). Con --fuente avisa de cifras
que no aparecen en la recopilación. Imprime ERROR (bloquea) y AVISO (revisar) y sale con código 1 si hay errores.
También se importa desde pipeline.py: validar(ed, fuente='') -> (errores, avisos)."""
import json, re, sys

KICKERS = {f'{a} · {b}' for a in ('Negocios', 'Tecnología', 'Administración') for b in ('México', 'Internacional')}
MESES = 'ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC'.split()
TIPOS = {'hook', 'foto', 'video', 'contador', 'barras', 'texto', 'pregunta'}
EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿️‍]')
HORA = re.compile(r'^([1-9]|1\d|2[0-3]):[0-5]\d$')

def validar(ed, fuente=''):
    err, av = [], []
    def largo(donde, txt, maximo):
        n = len(re.sub(r'<[^>]+>', '', txt or ''))
        if n > maximo * 1.3: err.append(f'{donde}: {n} caracteres (máx ~{maximo})')
        elif n > maximo: av.append(f'{donde}: {n} caracteres (máx ~{maximo})')
    def textos(o, ruta=''):
        if isinstance(o, dict):
            for k, v in o.items(): yield from textos(v, f'{ruta}.{k}' if ruta else k)
        elif isinstance(o, list):
            for i, v in enumerate(o): yield from textos(v, f'{ruta}[{i}]')
        elif isinstance(o, str): yield ruta, o

    if not re.match(r'^\d{4}-\d{2}-\d{2}$', ed.get('fecha', '')): err.append('fecha debe ser AAAA-MM-DD')
    m = re.match(r'^\d{2} ([A-Z]{3}) \d{4}$', ed.get('fechaLabel', ''))
    if not m or m.group(1) not in MESES: err.append('fechaLabel debe ser "DD MMM AAAA" (ej. "29 OCT 2026")')
    for ruta, t in textos(ed):
        if EMOJI.search(t): err.append(f'{ruta}: tiene emojis')

    notas = ed.get('notas') or []
    if not 1 <= len(notas) <= 12: err.append(f'notas: {len(notas)} (deben ser 1 a 12)')
    for i, n in enumerate(notas):
        d = f'notas[{i}]'
        for k in ('titular', 'titularCorto', 'bajada', 'fuente'):
            if not n.get(k): err.append(f'{d}.{k} vacío')
        if n.get('kicker') not in KICKERS: av.append(f'{d}.kicker "{n.get("kicker")}" no es uno de los permitidos')
        largo(f'{d}.titular', n.get('titular'), 80); largo(f'{d}.titularCorto', n.get('titularCorto'), 45)
        largo(f'{d}.bajada', n.get('bajada'), 260)
        if n.get('dato'): largo(f'{d}.dato.cifra', n['dato'].get('cifra'), 10); largo(f'{d}.dato.contexto', n['dato'].get('contexto'), 70)

    hs = ed.get('historias') or []
    if len(hs) != len(notas): err.append(f'historias: {len(hs)}, debe haber una por nota ({len(notas)})')
    colores = [h.get('tema') for h in hs]
    for i, h in enumerate(hs):
        d = f'historias[{i}]'
        if h.get('nota') != i: av.append(f'{d}.nota es {h.get("nota")}, se esperaba {i}')
        if not HORA.match(str(h.get('hora', ''))): err.append(f'{d}.hora "{h.get("hora")}" debe ser H:MM')
        if str(h.get('titulo', '')).lower().startswith('noticia'): av.append(f'{d}.titulo no debe empezar con "Noticia:" (el Estudio ya lo agrega)')
        largo(f'{d}.titulo', h.get('titulo'), 30)
        sl = h.get('slides') or []
        if len(sl) != 5: err.append(f'{d}.slides: {len(sl)} láminas (deben ser 5)')
        for j, s in enumerate(sl):
            if 'etiqueta' not in s or not s.get('titular'): err.append(f'{d}.slides[{j}] necesita etiqueta y titular')
            largo(f'{d}.slides[{j}].titular', s.get('titular'), 60 if j == 0 else 55)
            largo(f'{d}.slides[{j}].texto', s.get('texto'), 200)
            for k, p in enumerate(s.get('puntos') or []): largo(f'{d}.slides[{j}].puntos[{k}]', p, 120)
        if '#Blewprint' not in (h.get('caption') or ''): av.append(f'{d}.caption sin #Blewprint')
    if len(hs) > 1 and len(set(colores)) == 1: av.append('historias: todas tienen el mismo "tema" (el color debe alternar)')

    for k in ('instagram', 'linkedin'):
        if not (ed.get('copy') or {}).get(k): err.append(f'copy.{k} vacío')
    if not (ed.get('cierre') or {}).get('pregunta'): av.append('cierre.pregunta vacía')

    vs = ed.get('videos') or []
    if len(vs) != 3: err.append(f'videos: {len(vs)} (deben ser 3)')
    for i, v in enumerate(vs):
        d = f'videos[{i}]'
        if not isinstance(v.get('nota'), int) or not 0 <= v['nota'] < len(notas): err.append(f'{d}.nota fuera de rango')
        for k in ('titulo', 'caption', 'hora'):
            if not v.get(k): err.append(f'{d}.{k} vacío')
        if v.get('hora') and not HORA.match(v['hora']): err.append(f'{d}.hora "{v["hora"]}" debe ser H:MM')
        r = v.get('reel') or {}
        es = r.get('escenas') or []
        if not r.get('kicker'): err.append(f'{d}.reel.kicker vacío')
        largo(f'{d}.reel.kicker', r.get('kicker'), 30)
        if not 6 <= len(es) <= 10: err.append(f'{d}.reel: {len(es)} escenas (deben ser 7 a 9)')
        elif not 7 <= len(es) <= 9: av.append(f'{d}.reel: {len(es)} escenas (deben ser 7 a 9)')
        if es and es[0].get('tipo') != 'hook': err.append(f'{d}.reel.escenas[0] debe ser "hook" (es "{es[0].get("tipo")}")')
        if es and es[-1].get('tipo') != 'pregunta': av.append(f'{d}.reel: la última escena debería ser "pregunta"')
        for j, e in enumerate(es):
            de, t = f'{d}.reel.escenas[{j}]', e.get('tipo')
            if t not in TIPOS: err.append(f'{de}.tipo "{t}" no existe ({", ".join(sorted(TIPOS))})'); continue
            if t == 'hook':
                if not e.get('cifra'): av.append(f'{de}: la portada no tiene "cifra"')
                if '<em>' not in (e.get('html') or ''): av.append(f'{de}: la portada no marca la palabra clave con <em>')
                largo(f'{de}.cifra', e.get('cifra'), 8); largo(f'{de}.sub', e.get('sub'), 45)
            if t in ('foto', 'video') and not e.get('busqueda'): err.append(f'{de}: falta "busqueda" para Pixabay')
            if t == 'contador' and not isinstance(e.get('valor'), (int, float)): err.append(f'{de}.valor debe ser número')
            if t == 'barras':
                bs = e.get('barras') or []
                if not 2 <= len(bs) <= 4 or any(not isinstance(b.get('valor'), (int, float)) for b in bs):
                    err.append(f'{de}: 2 a 4 barras con "valor" numérico')
            if t in ('texto', 'pregunta', 'foto', 'video', 'contador') and not e.get('texto'): err.append(f'{de}.texto vacío')
        fotos = sum(1 for e in es if e.get('tipo') in ('foto', 'video'))
        if not 3 <= fotos <= 4: av.append(f'{d}.reel: {fotos} escenas de foto/video (deben ser 3 o 4)')

    if fuente:
        plano = re.sub(r'(?<=\d)[,\s](?=\d{3})', '', fuente)
        cifras = [(f'notas[{i}].dato.cifra', (n.get('dato') or {}).get('cifra', '')) for i, n in enumerate(notas)]
        for i, v in enumerate(vs):
            for j, e in enumerate((v.get('reel') or {}).get('escenas') or []):
                if e.get('cifra'): cifras.append((f'videos[{i}].reel.escenas[{j}].cifra', e['cifra']))
                if e.get('tipo') == 'contador': cifras.append((f'videos[{i}].reel.escenas[{j}].valor', str(e.get('valor'))))
        for donde, c in cifras:
            for num in re.findall(r'\d+(?:[.,]\d+)*', c or ''):
                n = re.sub(r'(?<=\d),(?=\d{3})', '', num).rstrip('0').rstrip('.') if '.' in num else re.sub(r'(?<=\d),(?=\d{3})', '', num)
                if n and n not in plano: av.append(f'{donde}: "{c}" no aparece tal cual en la recopilación; confirma que sea un hecho')
    return err, av

if __name__ == '__main__':
    args = sys.argv[1:]
    fuente = ''
    if '--fuente' in args:
        k = args.index('--fuente'); fuente = open(args[k + 1], encoding='utf-8').read(); del args[k:k + 2]
    errores, avisos = validar(json.load(open(args[0], encoding='utf-8')), fuente)
    for a in avisos: print('AVISO', a)
    for e in errores: print('ERROR', e)
    print(f'{len(errores)} errores, {len(avisos)} avisos')
    sys.exit(1 if errores else 0)
