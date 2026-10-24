"""Blewprint · Banda sonora para reels, generada por código (sin derechos de terceros).
Función principal: pista(duracion, eventos, salida_wav, bpm=118, semilla=0)
eventos = [(t, tipo)] con tipo en: whoosh, impacto, tick, pop, riser, cierre."""
import numpy as np, wave

SR = 44100

def _env(n, a=0.005, r=0.1):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

def _kick(d=0.35):
    t = np.arange(int(d * SR)) / SR
    f = 120 * np.exp(-t * 18) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)

def _hat(d=0.06, rng=None):
    n = int(d * SR); x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # agudo
    return x * np.exp(-np.arange(n) / SR * 80) * 0.10

def _clap(rng, d=0.18):
    n = int(d * SR); x = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 22)
    return np.convolve(x, np.ones(6) / 6, 'same') * 0.5

def _tone(freq, d, kind='saw', vol=0.2):
    t = np.arange(int(d * SR)) / SR
    if kind == 'saw':
        x = 2 * ((t * freq) % 1) - 1
        x = np.convolve(x, np.ones(18) / 18, 'same')
    else:
        x = np.sin(2 * np.pi * freq * t)
    return x * _env(len(t), 0.01, min(0.2, d * 0.5)) * vol

def _noise_sweep(d, f0, f1, rng, vol=0.5):
    n = int(d * SR); x = rng.standard_normal(n)
    out = np.zeros(n); y = 0.0
    fs = np.linspace(f0, f1, n)
    a = np.clip(2 * np.pi * fs / SR, 0, 1)
    for i in range(n):  # paso bajo variable
        y += a[i] * (x[i] - y); out[i] = y
    w = np.sin(np.linspace(0, np.pi, n)) ** 2
    return out / (np.abs(out).max() + 1e-9) * w * vol

def sfx(tipo, rng):
    if tipo == 'whoosh': return _noise_sweep(0.38, 300, 6000, rng, 0.45)
    if tipo == 'riser': return _noise_sweep(1.2, 200, 9000, rng, 0.35)
    if tipo == 'impacto':
        k = _kick(0.6) * 1.0; n = _noise_sweep(0.25, 4000, 300, rng, 0.35)
        out = np.zeros(len(k)); out[:len(n)] += n; return out + k
    if tipo == 'tick':
        n = int(0.02 * SR); return np.sin(2 * np.pi * 2400 * np.arange(n) / SR) * np.exp(-np.arange(n) / SR * 300) * 0.25
    if tipo == 'pop':
        t = np.arange(int(0.09 * SR)) / SR; return np.sin(2 * np.pi * (900 - 5000 * t) * t) * np.exp(-t * 40) * 0.4
    if tipo == 'cierre':
        return sum(_tone(f, 1.4, 'sine', 0.18) for f in (523.25, 659.25, 783.99))
    return np.zeros(1)

def musica(dur, bpm, rng):
    n = int(dur * SR); mix = np.zeros(n + SR)
    beat = 60 / bpm
    prog = [(55.0, (220.0, 261.63, 329.63)), (43.65, (174.61, 220.0, 261.63)),
            (65.41, (261.63, 329.63, 392.0)), (49.0, (196.0, 246.94, 293.66))]  # Am F C G
    k = _kick(); i = 0; t = 0.0
    while t < dur:
        s = int(t * SR)
        bar = int(i // 4) % 4; root, chord = prog[bar]
        if i % 4 in (0, 2) or (i % 8 == 7):
            mix[s:s + len(k)] += k[:len(mix) - s] * 0.9
        if i % 4 in (1, 3):
            c = _clap(rng); mix[s:s + len(c)] += c[:len(mix) - s] * 0.35
        for h in (0, 0.5):
            hs = int((t + h * beat) * SR); hh = _hat(rng=rng); mix[hs:hs + len(hh)] += hh[:max(0, len(mix) - hs)]
        b = _tone(root * 2, beat * 0.9, 'saw', 0.22); mix[s:s + len(b)] += b[:len(mix) - s]
        if i % 4 == 0:
            pad = sum(_tone(f, beat * 4, 'saw', 0.05) for f in chord); mix[s:s + len(pad)] += pad[:len(mix) - s]
        i += 1; t += beat
    mix = np.convolve(mix, np.ones(5) / 5, 'same')  # suaviza agudos
    return mix[:n]

def pista(dur, eventos, salida, bpm=118, semilla=0):
    rng = np.random.default_rng(semilla)
    n = int(dur * SR)
    m = musica(dur, bpm, rng) * 0.55
    fx = np.zeros(n + 2 * SR)
    for t, tipo in eventos:
        x = sfx(tipo, rng); s = max(0, int(t * SR))
        fx[s:s + len(x)] += x[:len(fx) - s]
    mix = m + fx[:n]
    fo = int(0.6 * SR); mix[-fo:] *= np.linspace(1, 0, fo)  # fade out
    mix = np.tanh(mix * 1.2)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
    st = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(salida, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
