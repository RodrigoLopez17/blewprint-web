"""Blewprint · Sube los JPEG y MP4 del día a la rama huérfana "media" (un solo commit, push --force).
Uso: python3 -I subir_media.py <repo> <outdir> [--sin-push]
Usa un worktree temporal, así que no toca la rama ni los archivos del checkout de <repo>. La carpeta del día
(<fecha>/, tomada de outdir/manifest.json) queda en https://raw.githubusercontent.com/RodrigoLopez17/blewprint-web/media/<fecha>/.
Después del push comprueba que una imagen y los reels respondan 200 (hasta 3 intentos con 30 s de espera).
--sin-push arma el commit pero no lo sube (para probar). Sale con código 1 si algo falla."""
import json, os, sys, glob, shutil, subprocess, tempfile, time, urllib.request

args = sys.argv[1:]
sin_push = '--sin-push' in args
if sin_push: args.remove('--sin-push')
repo, out = os.path.abspath(args[0]), os.path.abspath(args[1])
man = json.load(open(os.path.join(out, 'manifest.json'), encoding='utf-8'))
fecha = man['fecha']
# Solo lo que dice el manifest más los reels: nada de copias sueltas (ej. "h0-01 2.jpg" de iCloud).
archivos = [os.path.join(out, a) for p in man['posts'] for a in p['imagenes']] + sorted(glob.glob(os.path.join(out, 'reel-[0-9].mp4')))
faltan = [a for a in archivos if not os.path.exists(a)]
if faltan or not archivos: sys.exit('Faltan archivos: ' + ', '.join(map(os.path.basename, faltan or [out])))

def git(*a, cwd=repo):
    r = subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)
    if r.returncode: sys.exit(f'git {" ".join(a)} falló: {r.stderr.strip()}')
    return r.stdout.strip()

tmp = tempfile.mkdtemp(prefix='media-')
rama = f'_media_{fecha}'
try:
    git('worktree', 'add', '--detach', tmp, 'HEAD')
    git('checkout', '-q', '--orphan', rama, cwd=tmp)
    git('rm', '-rfq', '.', cwd=tmp)
    for x in os.listdir(tmp):
        if x != '.git': shutil.rmtree(os.path.join(tmp, x), ignore_errors=True)
    os.makedirs(os.path.join(tmp, fecha))
    for a in archivos: shutil.copy2(a, os.path.join(tmp, fecha))
    git('add', fecha, cwd=tmp)
    git('commit', '-qm', f'Media {fecha}', cwd=tmp)
    print(git('log', '--oneline', '--stat', '-1', cwd=tmp).splitlines()[0], f'({len(archivos)} archivos)')
    if not sin_push:
        # El proxy de la nube a veces responde con error aunque el push sí entró: se compara contra el remoto.
        r = subprocess.run(['git', 'push', '--force', 'origin', 'HEAD:refs/heads/media'], cwd=tmp, capture_output=True, text=True)
        if git('ls-remote', 'origin', 'refs/heads/media', cwd=tmp).split('\t')[0] != git('rev-parse', 'HEAD', cwd=tmp):
            sys.exit('push a media falló: ' + r.stderr.strip())
finally:
    subprocess.run(['git', 'worktree', 'remove', '--force', tmp], cwd=repo, capture_output=True)
    subprocess.run(['git', 'branch', '-D', rama], cwd=repo, capture_output=True)
    shutil.rmtree(tmp, ignore_errors=True)

if sin_push: print('Sin push: commit armado y descartado.'); sys.exit(0)
base = f'https://raw.githubusercontent.com/RodrigoLopez17/blewprint-web/media/{fecha}/'
revisar = [os.path.basename(archivos[0])] + [os.path.basename(a) for a in archivos if a.endswith('.mp4')]
for intento in range(3):
    malos = []
    for nombre in revisar:
        try:
            req = urllib.request.Request(base + nombre, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            if urllib.request.urlopen(req, timeout=30).status != 200: malos.append(nombre)
        except Exception: malos.append(nombre)
    if not malos: print('OK: medios públicos en', base); sys.exit(0)
    time.sleep(30)
sys.exit('No responden: ' + ', '.join(malos))
