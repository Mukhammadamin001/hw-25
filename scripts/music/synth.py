"""Синтез звука: инструменты, барабаны, эффекты, сведение.

Всё построено на numpy/scipy: аддитивный синтез, FM, волновые таблицы
и алгоритм Карплуса — Стронга для щипковых. Никаких внешних сэмплов.
"""
import math
import zlib
from functools import lru_cache

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d

SR = 44100
TAU = 2 * np.pi


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69.0) / 12.0)


def tt(n):
    return np.arange(n) / SR


# --------------------------------------------------------------------------
# Фильтры
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _sos(kind, f1, f2, order):
    if kind == 'bandpass':
        return signal.butter(order, [f1, f2], kind, fs=SR, output='sos')
    return signal.butter(order, f1, kind, fs=SR, output='sos')


def lp(x, fc, order=2):
    return signal.sosfilt(_sos('lowpass', float(min(fc, SR * 0.45)), 0.0, order), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos('highpass', float(fc), 0.0, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos('bandpass', float(lo), float(min(hi, SR * 0.45)), order), x, axis=0)


def release_env(t, dur, rel):
    """1 до конца ноты, затем экспоненциальное затухание."""
    e = np.ones_like(t)
    m = t > dur
    e[m] = np.exp(-(t[m] - dur) / rel)
    return e


# --------------------------------------------------------------------------
# Волновые таблицы
# --------------------------------------------------------------------------
def harm_table(amps, size=2048):
    amps = np.asarray(amps, dtype=float)
    k = np.arange(1, len(amps) + 1)[:, None]
    x = np.arange(size)[None, :] / size
    tab = (amps[:, None] * np.sin(TAU * k * x)).sum(axis=0)
    tab /= max(1e-9, np.abs(tab).max())
    return np.append(tab, tab[0])


def phase_of(freq, n):
    ph = np.cumsum(np.broadcast_to(np.asarray(freq, dtype=float), (n,)) / SR)
    return ph - np.floor(ph)


def wt_read(tab, ph):
    size = len(tab) - 1
    x = ph * size
    i = x.astype(np.int64)
    fr = x - i
    return tab[i] * (1 - fr) + tab[i + 1] * fr


def formant_amps(f, formants, tilt, floor=0.08, fmax=14000.0):
    K = max(1, int(fmax / f))
    k = np.arange(1, K + 1)
    fk = f * k
    a = np.full(K, floor)
    for fc, g, bw in formants:
        a = a + g * np.exp(-((fk - fc) / bw) ** 2)
    return a * k ** (-tilt)


# --------------------------------------------------------------------------
# Карплус — Стронг (щипковые)
# --------------------------------------------------------------------------
def ks_core(f, n_out, rng, t60=2.0, bright=0.6, pick=0.13, semi=None):
    """Струна: шум в линии задержки + усредняющий фильтр.

    Период берём целым, а точную высоту (и бенды) получаем передискретизацией.
    """
    P = max(4, int(SR / f - 0.5))
    f0 = SR / (P + 0.5)
    ratio = f / f0
    if semi is None:
        pos = np.arange(n_out) * ratio
    else:
        pos = np.cumsum(ratio * 2.0 ** (semi / 12.0))
        pos -= pos[0]
    n_src = int(pos[-1]) + 3
    exc = rng.uniform(-1, 1, P)
    if bright < 1.0:
        a = 1.0 - bright
        for _ in range(2):
            exc = signal.lfilter([1 - a], [1, -a], exc)
    shift = max(1, int(P * pick))
    exc = exc - np.roll(exc, shift) * 0.5
    exc -= exc.mean()
    exc /= max(1e-9, np.abs(exc).max())
    g = 10.0 ** (-3.0 / (t60 * f0))
    nb = n_src // P + 2
    y = np.zeros((nb + 1) * P + 1)
    y[1:P + 1] = exc
    for k in range(1, nb):
        s = 1 + k * P
        y[s:s + P] = g * 0.5 * (y[s - P:s] + y[s - P - 1:s - 1])
    y = y[1:]
    return np.interp(pos, np.arange(len(y)), y)


def bend_curve(n, bends, vib=0.0, vib_rate=5.5, vib_delay=0.15):
    """bends: [(t_start, t_end, semitones)] — плавный подъём и удержание."""
    t = tt(n)
    semi = np.zeros(n)
    for t0, t1, amt in bends:
        semi += amt * np.clip((t - t0) / max(1e-3, t1 - t0), 0, 1)
    if vib:
        semi += vib * np.sin(TAU * vib_rate * t) * np.clip((t - vib_delay) / 0.25, 0, 1)
    return semi


# --------------------------------------------------------------------------
# Инструменты: f(pitch, dur, vel, rng, **kw) -> mono np.ndarray
# --------------------------------------------------------------------------
def i_piano(pitch, dur, vel, rng, bright=1.0):
    f = mtof(pitch)
    dur = min(dur, 7.0)
    n = int((dur + 0.5) * SR)
    t = tt(n)
    B = 0.00007 * (f / 110.0) ** 1.1
    T = float(np.clip(5.0 * (220.0 / f) ** 0.6, 0.35, 10.0))
    kmax = max(1, min(20, int(10000 / f)))
    hard = 0.3 + 0.7 * vel * bright
    out = np.zeros(n)
    for k in range(1, kmax + 1):
        fk = k * f * math.sqrt(1 + B * k * k)
        if fk > 16000:
            break
        a = (0.25 + abs(math.sin(math.pi * k / 7.3))) / k ** 1.0 * math.exp(-(k - 1) * (1.0 - hard) * 0.5)
        Tk = T / (1 + 0.3 * (k - 1))
        env = 0.6 * np.exp(-t / (0.22 * Tk)) + 0.4 * np.exp(-t / Tk)
        out += a * env * (np.sin(TAU * fk * t) + np.sin(TAU * fk * 1.0009 * t))
    out *= np.minimum(1.0, t / 0.002)
    m = int(0.03 * SR)
    ham = lp(rng.standard_normal(m), min(5000.0, 900 + f * 3)) * np.exp(-tt(m) / 0.005)
    out[:m] += ham * 0.35 * vel
    out *= release_env(t, dur, 0.09)
    return out * (0.12 + 0.88 * vel) * 0.3


def i_epiano(pitch, dur, vel, rng, bark=1.0):
    f = mtof(pitch)
    dur = min(dur, 6.0)
    n = int((dur + 0.6) * SR)
    t = tt(n)
    idx = (0.5 + 2.0 * vel ** 2 * bark) * np.exp(-t / 0.4) + 0.25
    ph = TAU * f * t
    y = np.sin(ph + idx * np.sin(ph))
    if f * 14 < 18000:
        y += 0.2 * vel * np.sin(TAU * f * 14 * t) * np.exp(-t / 0.012)
    T = float(np.clip(2.4 * (261.6 / f) ** 0.45, 0.5, 6.0))
    env = np.minimum(1.0, t / 0.002) * np.exp(-t / T) * release_env(t, dur, 0.1)
    y = np.tanh(1.4 * y * env * (0.4 + 0.6 * vel)) / math.tanh(1.4)
    return y * 0.8


def i_vibes(pitch, dur, vel, rng, motor=5.3):
    f = mtof(pitch)
    ring = min(dur + 0.25, 4.5)
    n = int((ring + 0.5) * SR)
    t = tt(n)
    y = np.sin(TAU * f * t) * np.exp(-t / 2.6)
    y += 0.3 * vel * np.sin(TAU * f * 4.0 * t) * np.exp(-t / 0.45)
    if f * 10 < 18000:
        y += 0.1 * vel * np.sin(TAU * f * 10.0 * t) * np.exp(-t / 0.08)
    y *= 1 - 0.3 * (0.5 + 0.5 * np.sin(TAU * motor * t + rng.uniform(0, TAU)))
    m = int(0.02 * SR)
    y[:m] += lp(rng.standard_normal(m), 3500) * np.exp(-tt(m) / 0.003) * 0.25
    y *= np.minimum(1.0, t / 0.001) * release_env(t, ring, 0.12)
    return y * (0.2 + 0.8 * vel) * 0.7


def i_pluck(pitch, dur, vel, rng, t60=2.0, bright=0.6, damp=0.07, pick=0.13,
            bends=(), vib=0.0, drive=0.0, cab=0.0, octave=0.0, lowpass=0.0):
    f = mtof(pitch)
    n = int((dur + damp * 6 + 0.02) * SR)
    semi = bend_curve(n, bends, vib) if (bends or vib) else None
    y = ks_core(f, n, rng, t60=t60, bright=bright * (0.6 + 0.4 * vel), pick=pick, semi=semi)
    if octave:
        y += octave * ks_core(f * 2, n, rng, t60=t60 * 0.7, bright=bright, pick=pick, semi=semi)
    t = tt(n)
    y *= release_env(t, dur, damp) * np.minimum(1.0, t / 0.0015)
    if drive:
        y = np.tanh(drive * y) / math.tanh(drive)
    if cab:
        y = lp(hp(y, 110), cab, order=2)
    if lowpass:
        y = lp(y, lowpass)
    return y * (0.25 + 0.75 * vel)


def i_upright(pitch, dur, vel, rng, t60=1.4):
    f = mtof(pitch)
    n = int((dur + 0.4) * SR)
    t = tt(n)
    ks = ks_core(f, n, rng, t60=t60, bright=0.3, pick=0.2)
    ks = lp(ks, 900)
    ks /= max(1e-9, np.abs(ks).max())
    fund = np.sin(TAU * f * t) * np.exp(-t / 0.9) + 0.3 * np.sin(TAU * 2 * f * t) * np.exp(-t / 0.4)
    m = int(0.04 * SR)
    thump = np.zeros(n)
    thump[:m] = lp(rng.standard_normal(m), 250) * np.exp(-tt(m) / 0.012) * 3
    y = 0.6 * ks + 0.7 * fund + thump
    y *= np.minimum(1.0, t / 0.004) * release_env(t, dur, 0.06)
    return y * (0.35 + 0.65 * vel)


def i_ebass(pitch, dur, vel, rng):
    f = mtof(pitch)
    n = int((dur + 0.3) * SR)
    t = tt(n)
    ks = ks_core(f, n, rng, t60=2.5, bright=0.4, pick=0.18)
    ks /= max(1e-9, np.abs(ks).max())
    fund = np.sin(TAU * f * t) * np.exp(-t / 1.5)
    y = lp(0.7 * ks + 0.6 * fund, 1400)
    y = np.tanh(1.5 * y)
    y *= np.minimum(1.0, t / 0.003) * release_env(t, dur, 0.05)
    return y * (0.4 + 0.6 * vel)


def i_organ(pitch, dur, vel, rng, drawbars=(8, 8, 8, 0, 0, 0, 0, 0, 0), perc=0.0, click=0.06):
    f = mtof(pitch)
    n = int((dur + 0.08) * SR)
    t = tt(n)
    ratios = (0.5, 1.5, 1, 2, 3, 4, 5, 6, 8)
    y = np.zeros(n)
    for r, db in zip(ratios, drawbars):
        if db and f * r < 15000:
            y += (db / 8.0) * np.sin(TAU * f * r * t + rng.uniform(0, TAU))
    y /= max(1.0, sum(drawbars) / 8.0 * 0.7)
    if perc:
        y += perc * np.sin(TAU * f * 3 * t) * np.exp(-t / 0.22)
    m = int(0.01 * SR)
    y[:m] += bp(rng.standard_normal(m), 1500, 9000) * np.exp(-tt(m) / 0.002) * click
    y *= np.minimum(1.0, t / 0.005) * release_env(t, dur, 0.025)
    return y * (0.85 + 0.15 * vel)


def _wind_env(t, dur, atk, rel, sag=0.12):
    env = np.minimum(1.0, t / atk)
    env *= 1 - sag * (1 - np.exp(-t / 0.3))
    return env * release_env(t, dur, rel)


def i_sax(pitch, dur, vel, rng, legato=False, breath=0.05, bright=1.0, scoop=0.7):
    f = mtof(pitch)
    n = int((dur + 0.4) * SR)
    t = tt(n)
    semi = np.zeros(n)
    if not legato:
        semi -= scoop * np.exp(-t / 0.045)
    if dur > 0.45:
        semi += 0.17 * np.sin(TAU * 5.1 * t + rng.uniform(0, TAU)) * np.clip((t - 0.28) / 0.4, 0, 1)
    ph = phase_of(f * 2 ** (semi / 12), n)
    soft = wt_read(harm_table(formant_amps(f, [(500, 1.0, 350), (1300, 0.3, 500)], 1.4)), ph)
    hard = wt_read(harm_table(formant_amps(f, [(600, 1.0, 400), (1600, 0.8, 700), (3000, 0.35, 900)], 0.65)), ph)
    atk = 0.012 if legato else 0.03 + 0.04 * (1 - vel)
    env = _wind_env(t, dur, atk, 0.07)
    mix = np.clip(vel * (0.35 + 0.65 * env) * bright, 0, 1)
    y = (soft * (1 - mix) + hard * mix) * env
    nz = bp(rng.standard_normal(n), 1500, 6000) * env * breath * (1 + 3 * np.exp(-t / 0.04))
    return np.tanh(1.2 * (y + nz)) * (0.35 + 0.65 * vel)


def i_trumpet(pitch, dur, vel, rng, legato=False):
    f = mtof(pitch)
    n = int((dur + 0.3) * SR)
    t = tt(n)
    semi = np.zeros(n)
    if not legato:
        semi -= 0.35 * np.exp(-t / 0.03)
    if dur > 0.45:
        semi += 0.1 * np.sin(TAU * 5.6 * t + rng.uniform(0, TAU)) * np.clip((t - 0.3) / 0.4, 0, 1)
    ph = phase_of(f * 2 ** (semi / 12), n)
    tab = harm_table(formant_amps(f, [(1750, 1.0, 450), (3300, 0.45, 900)], 0.35, floor=0.03))
    y = wt_read(tab, ph)
    atk = 0.01 if legato else 0.025
    env = _wind_env(t, dur, atk, 0.05, sag=0.2)
    y = hp(y * env, 450)
    nz = bp(rng.standard_normal(n), 2000, 7000) * env * 0.03 * (1 + 4 * np.exp(-t / 0.03))
    return np.tanh(1.5 * (y + nz)) * (0.35 + 0.65 * vel)


def i_flute(pitch, dur, vel, rng, legato=False, breath=0.06):
    f = mtof(pitch)
    n = int((dur + 0.35) * SR)
    t = tt(n)
    semi = np.zeros(n)
    if dur > 0.4:
        semi += 0.13 * np.sin(TAU * 5.0 * t + rng.uniform(0, TAU)) * np.clip((t - 0.2) / 0.35, 0, 1)
    ph = phase_of(f * 2 ** (semi / 12), n)
    tab = harm_table([1.0, 0.25 + 0.25 * vel, 0.12, 0.05, 0.03][: max(1, int(12000 / f))])
    y = wt_read(tab, ph)
    atk = 0.015 if legato else 0.05
    env = _wind_env(t, dur, atk, 0.09, sag=0.05)
    nz = bp(rng.standard_normal(n), min(f * 1.5, 8000), min(f * 7, 15000))
    nz = nz * env * breath * (1 + (0 if legato else 4) * np.exp(-t / 0.035))
    return (y * env + nz) * (0.4 + 0.6 * vel)


def i_harmonica(pitch, dur, vel, rng, legato=False, bends=(), trem=0.25, vib=0.0):
    f = mtof(pitch)
    n = int((dur + 0.25) * SR)
    t = tt(n)
    semi = bend_curve(n, bends, vib * 0.5) if (bends or vib) else np.zeros(n)
    ph = phase_of(f * 2 ** (semi / 12), n)
    tab = harm_table(formant_amps(f, [(1100, 0.8, 800), (2300, 0.4, 700)], 0.55, floor=0.3, fmax=9000))
    y = wt_read(tab, ph)
    atk = 0.01 if legato else 0.02
    env = _wind_env(t, dur, atk, 0.04, sag=0.1)
    if dur > 0.5:
        env *= 1 - trem * (0.5 + 0.5 * np.sin(TAU * 5.3 * t)) * np.clip((t - 0.25) / 0.3, 0, 1)
    nz = bp(rng.standard_normal(n), 1000, 5000) * env * 0.04
    y = y * env + nz
    y = bp(y, 250, 4800)
    return np.tanh(2.2 * y) * (0.4 + 0.6 * vel)


def i_strings(pitch, dur, vel, rng, attack=0.18, release=0.35, voices=3, detune=0.07,
              vib=0.12, bright=1.0, swell=0.0, legato=False):
    f = mtof(pitch)
    n = int((dur + release * 4) * SR)
    t = tt(n)
    amps = formant_amps(f, [(450, 0.6, 300), (1200, 0.45, 500), (2800, 0.35, 900)], 1.0,
                        floor=0.6, fmax=7000 * bright + 2000)
    amps = amps * np.exp(-np.arange(1, len(amps) + 1) * f / (3500 * bright + 1500))  # мягкий спад верхов
    tab = harm_table(amps)
    y = np.zeros(n)
    for v in range(voices):
        d = detune * (v - (voices - 1) / 2) / max(1.0, (voices - 1) / 2) + rng.normal(0, 0.01)
        semi = d + vib * np.sin(TAU * rng.uniform(4.8, 6.0) * t + rng.uniform(0, TAU)) * np.clip(t / 0.4, 0, 1)
        y += wt_read(tab, phase_of(f * 2 ** (semi / 12), n))
    y /= voices
    atk = 0.07 if legato else attack * (1.3 - 0.6 * vel)
    env = np.clip(t / atk, 0, 1) ** 1.5
    if swell:
        env *= 1 + swell * np.clip(t / max(dur, 0.1), 0, 1)
    env *= release_env(t, dur, release)
    nz = hp(rng.standard_normal(n), 3000) * 0.012
    return (y + nz) * env * (0.3 + 0.7 * vel)


# --------------------------------------------------------------------------
# Барабаны: заготовки кэшируются, громкость масштабируется по velocity
# --------------------------------------------------------------------------
def _d_kick(rng, tight=False):
    n = int(0.5 * SR)
    t = tt(n)
    fr = 47 + 105 * np.exp(-t / 0.03)
    body = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-t / (0.16 if tight else 0.26))
    click = lp(rng.standard_normal(n), 3000) * np.exp(-t / 0.004) * 0.3
    return np.tanh(1.6 * (body + click))


def _d_snare(rng):
    n = int(0.4 * SR)
    t = tt(n)
    tone = 0.7 * np.sin(TAU * 190 * t) * np.exp(-t / 0.05) + 0.35 * np.sin(TAU * 330 * t) * np.exp(-t / 0.03)
    nz = bp(rng.standard_normal(n), 1200, 9000) * np.exp(-t / 0.12)
    return (tone + nz * 1.1) * np.minimum(1.0, t / 0.001)


def _d_brush(rng):
    n = int(0.35 * SR)
    t = tt(n)
    nz = bp(rng.standard_normal(n), 1500, 8000)
    env = np.minimum(1.0, t / 0.004) * (np.exp(-t / 0.05) + 0.15 * np.exp(-t / 0.2))
    return nz * env


def _d_hat(rng, kind='closed'):
    L = {'closed': 0.15, 'open': 0.7, 'pedal': 0.12}[kind]
    dec = {'closed': 0.035, 'open': 0.3, 'pedal': 0.025}[kind]
    n = int(L * SR)
    t = tt(n)
    sq = sum(np.sign(np.sin(TAU * fq * 1.7 * t + rng.uniform(0, TAU)))
             for fq in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)) / 6
    y = hp(hp(0.6 * sq + 0.5 * rng.standard_normal(n), 4500 if kind == 'pedal' else 6500), 6000)
    return y * np.exp(-t / dec) * np.minimum(1.0, t / 0.001)


@lru_cache(maxsize=None)
def _metal(kind):
    r = np.random.default_rng({'ride': 11, 'crash': 23, 'bell': 37}[kind])
    k = 140
    fq = np.sort(np.exp(r.uniform(np.log(320), np.log(12500), k)))
    amp = r.uniform(0.2, 1.0, k) / (fq / 320) ** 0.35
    dec = r.uniform(0.25, 1.3, k) * (1.0 - 0.5 * fq / 12500)
    if kind == 'bell':
        fq[:5] = [560, 830, 1110, 1450, 1720]
        amp[:5] = 3.0
        dec[:5] = 1.5
    return fq, amp, dec, r.uniform(0, TAU, k)


def _d_cymbal(rng, kind='ride'):
    L = {'ride': 2.4, 'bell': 2.2, 'crash': 3.2}[kind]
    n = int(L * SR)
    t = tt(n)
    fq, amp, dec, ph = _metal(kind)
    y = np.zeros(n)
    jitter = rng.uniform(0.995, 1.005, len(fq))
    for f_, a_, d_, p_, j_ in zip(fq, amp, dec, ph, jitter):
        m = min(n, int(d_ * 7 * SR))
        y[:m] += a_ * np.sin(TAU * f_ * j_ * t[:m] + p_) * np.exp(-t[:m] / d_)
    y /= np.abs(y).max()
    wash_amt = {'ride': 0.9, 'bell': 0.4, 'crash': 2.2}[kind]
    wash = bp(rng.standard_normal(n), 3500, 14000) * np.exp(-t / (0.7 if kind != 'crash' else 1.3))
    ping = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.005)
    y = y * (0.8 if kind != 'crash' else 0.35) + wash * wash_amt + ping * 0.8
    y = hp(y, 400)
    if kind == 'crash':
        y *= np.minimum(1.0, t / 0.003)
    return y * np.exp(-t / (1.3 if kind != 'crash' else 1.6))


def _d_rim(rng):
    n = int(0.12 * SR)
    t = tt(n)
    return (np.sin(TAU * 1750 * t) * np.exp(-t / 0.008) * 0.7
            + bp(rng.standard_normal(n), 1000, 5000) * np.exp(-t / 0.012))


def _d_shaker(rng):
    n = int(0.12 * SR)
    t = tt(n)
    env = np.minimum(1.0, t / 0.012) * np.exp(-t / 0.035)
    return bp(rng.standard_normal(n), 4000, 13000) * env


def _d_tom(rng, f0):
    n = int(0.6 * SR)
    t = tt(n)
    fr = f0 * (1 + 0.35 * np.exp(-t / 0.04))
    y = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-t / 0.3)
    y += lp(rng.standard_normal(n), 2000) * np.exp(-t / 0.03) * 0.3
    return y


def _d_clap(rng):
    n = int(0.3 * SR)
    t = tt(n)
    env = np.zeros(n)
    for d in (0.0, 0.009, 0.018):
        m = t >= d
        env[m] += np.exp(-(t[m] - d) / 0.006)
    env += 0.5 * np.exp(-np.maximum(t - 0.02, 0) / 0.08) * (t > 0.02)
    return bp(rng.standard_normal(n), 900, 3500) * env


def _d_stomp(rng):
    n = int(0.35 * SR)
    t = tt(n)
    fr = 60 + 40 * np.exp(-t / 0.02)
    y = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-t / 0.12)
    y += lp(rng.standard_normal(n), 600) * np.exp(-t / 0.03) * 0.8
    return y


def _jingles(rng, n, amt):
    t = tt(n)
    am = np.abs(lp(rng.standard_normal(n), 60))
    am /= max(1e-9, am.max())
    return hp(rng.standard_normal(n), 6500) * am * np.exp(-t / 0.18) * amt


def _d_dum(rng):
    n = int(0.6 * SR)
    t = tt(n)
    fr = 82 + 40 * np.exp(-t / 0.025)
    y = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-t / 0.28)
    y += lp(rng.standard_normal(n), 500) * np.exp(-t / 0.04) * 0.5
    return y + _jingles(rng, n, 0.25)


def _d_tak(rng):
    n = int(0.4 * SR)
    t = tt(n)
    y = bp(rng.standard_normal(n), 1500, 6000) * np.exp(-t / 0.035)
    y += 0.5 * np.sin(TAU * 390 * t) * np.exp(-t / 0.03)
    return y + _jingles(rng, n, 0.35)


def _d_ka(rng):
    n = int(0.25 * SR)
    t = tt(n)
    y = bp(rng.standard_normal(n), 3000, 9000) * np.exp(-t / 0.015)
    return y * 0.7 + _jingles(rng, n, 0.25)


# имя: (генератор, панорама, громкость)
DRUMS = {
    'kick': (lambda r: _d_kick(r), 0.0, 1.0),
    'kick_t': (lambda r: _d_kick(r, tight=True), 0.0, 1.0),
    'snare': (_d_snare, -0.1, 0.75),
    'brush': (_d_brush, -0.1, 0.55),
    'hat': (lambda r: _d_hat(r, 'closed'), -0.3, 0.3),
    'ohat': (lambda r: _d_hat(r, 'open'), -0.3, 0.25),
    'pedal': (lambda r: _d_hat(r, 'pedal'), -0.3, 0.3),
    'ride': (lambda r: _d_cymbal(r, 'ride'), 0.35, 0.3),
    'bell': (lambda r: _d_cymbal(r, 'bell'), 0.35, 0.3),
    'crash': (lambda r: _d_cymbal(r, 'crash'), -0.4, 0.45),
    'rim': (_d_rim, -0.1, 0.4),
    'shaker': (_d_shaker, 0.4, 0.25),
    'tom_hi': (lambda r: _d_tom(r, 190), -0.25, 0.7),
    'tom_lo': (lambda r: _d_tom(r, 110), 0.25, 0.8),
    'clap': (_d_clap, 0.15, 0.5),
    'stomp': (_d_stomp, 0.0, 1.0),
    'dum': (_d_dum, 0.0, 1.0),
    'tak': (_d_tak, 0.15, 0.6),
    'ka': (_d_ka, -0.2, 0.45),
}

_drum_cache = {}


def drum_hit(name, vel, rng):
    key = (name, int(rng.integers(4)))
    if key not in _drum_cache:
        gen = DRUMS[name][0]
        _drum_cache[key] = gen(np.random.default_rng(zlib.crc32(name.encode()) + key[1]))
    y = _drum_cache[key]
    return y * DRUMS[name][2] * vel ** 1.3


def i_drums(pitch, dur, vel, rng):
    return drum_hit(pitch, vel, rng)


def sweep(dur, vel, rng):
    """Щётка «по кругу» — непрерывный шорох."""
    n = int(dur * SR)
    t = tt(n)
    env = np.sin(np.pi * t / dur) ** 2
    return bp(rng.standard_normal(n), 1200, 6500) * env * 0.18 * vel


def i_sweep(pitch, dur, vel, rng):
    return sweep(dur, vel, rng)


INSTRUMENTS = {
    'piano': i_piano,
    'epiano': i_epiano,
    'vibes': i_vibes,
    'pluck': i_pluck,
    'upright': i_upright,
    'ebass': i_ebass,
    'organ': i_organ,
    'sax': i_sax,
    'trumpet': i_trumpet,
    'flute': i_flute,
    'harmonica': i_harmonica,
    'strings': i_strings,
    'drums': i_drums,
    'sweep': i_sweep,
}
CACHEABLE = {'piano', 'epiano', 'vibes', 'organ'}
MONO_LEGATO = {'sax', 'trumpet', 'flute', 'harmonica'}


# --------------------------------------------------------------------------
# Эффекты
# --------------------------------------------------------------------------
def fx_leslie(buf, rng, rate=6.0, depth=0.25):
    n = len(buf)
    t = tt(n)
    m = buf.mean(axis=1)
    d = 0.00045 * SR * (1 + np.sin(TAU * rate * t))
    y = np.interp(np.arange(n) - d - 1, np.arange(n), m)
    L = y * (1 + depth * np.sin(TAU * rate * t))
    R = y * (1 + depth * np.sin(TAU * rate * t + 2.0))
    return np.stack([L, R], axis=1) * 0.85 + buf * 0.15


def fx_autopan(buf, rng, rate=3.0, depth=0.35):
    t = tt(len(buf))
    p = depth * np.sin(TAU * rate * t)
    out = buf.copy()
    out[:, 0] *= 1 - p
    out[:, 1] *= 1 + p
    return out


def fx_chorus(buf, rng, rate=0.8, depth_ms=3.0, mix=0.35):
    n = len(buf)
    t = tt(n)
    out = buf.copy()
    for ch, off in ((0, 0.0), (1, 1.6)):
        d = (depth_ms / 1000 * SR) * (1.5 + np.sin(TAU * rate * t + off))
        out[:, ch] = buf[:, ch] * (1 - mix) + np.interp(np.arange(n) - d, np.arange(n), buf[:, ch]) * mix
    return out


def fx_eq(lo=None, hi=None):
    def f(buf, rng):
        if lo:
            buf = hp(buf, lo)
        if hi:
            buf = lp(buf, hi)
        return buf
    return f


def fx_slapback(delay=0.11, fb=0.25):
    def f(buf, rng):
        d = int(delay * SR)
        out = buf.copy()
        for k in range(1, 4):
            out[d * k:] += buf[:-d * k] * fb ** k
        return out
    return f


def make_ir(t60, rng, predelay=0.018, damping=0.45):
    n = int((predelay + t60 * 1.05) * SR)
    t = tt(n)
    irs = []
    for _ in range(2):
        nz = rng.standard_normal(n)
        low = lp(nz, 1800)
        high = nz - low
        ir = low * 10 ** (-3 * t / t60) + high * 0.7 * 10 ** (-3 * t / (t60 * damping))
        ir *= np.minimum(1.0, t / 0.012)
        ir[: int(predelay * SR)] = 0
        ir = lp(ir, 9000)
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    return irs


def active_rms(x):
    m = x.mean(axis=1) if x.ndim == 2 else x
    w = int(0.05 * SR)
    nw = len(m) // w
    if nw == 0:
        return 0.0
    r = np.sqrt((m[: nw * w].reshape(nw, w) ** 2).mean(axis=1))
    act = r[r > r.max() * 0.1]
    return float(np.sqrt((act ** 2).mean())) if len(act) else 0.0


def master(x, loud_db=-17.0):
    x = hp(x, 28)
    m = (x ** 2).mean(axis=1)
    env = np.sqrt(np.maximum(lp(m, 6, order=1), 1e-12))
    ar = active_rms(x)
    thr = ar * 1.3
    ratio = 2.2
    g = np.where(env > thr, (env / thr) ** (1 / ratio - 1), 1.0)
    x = x * g[:, None]
    x *= 10 ** (loud_db / 20) / max(1e-9, active_rms(x))
    # лимитер с «заглядыванием вперёд»: пики не выше 0.9
    w = int(0.004 * SR) * 2 + 1
    peak = maximum_filter1d(np.abs(x).max(axis=1), size=w)
    need = np.minimum(1.0, 0.9 / np.maximum(peak, 1e-9))
    gain = minimum_filter1d(need, size=int(0.03 * SR))
    gain = signal.lfilter([0.002], [1, -0.998], gain - 1) + 1
    x = x * np.minimum(gain, need)[:, None]
    a = np.abs(x)
    over = a > 0.85
    x[over] = np.sign(x[over]) * (0.85 + 0.13 * np.tanh((a[over] - 0.85) / 0.13))
    return x


# --------------------------------------------------------------------------
# Песня и партии
# --------------------------------------------------------------------------
class Part:
    def __init__(self, song, inst, pan=0.0, level=-20.0, send=0.2, jitter=0.005, post=(), **kw):
        self.song = song
        self.inst = inst
        self.pan = pan
        self.level = level
        self.send = send
        self.jitter = jitter
        self.post = list(post)
        self.kw = kw
        self.ev = []
        self.raws = []

    def note(self, beat, dur, pitch, vel=0.8, delay=0.0, **kw):
        s = self.song
        j = s.rng.normal(0, self.jitter) if self.jitter else 0.0
        t0 = s.time(beat) + delay + j
        t1 = s.time(beat + dur) + delay
        self.ev.append((max(0.0, t0), max(0.03, t1 - t0 - j), pitch, float(np.clip(vel, 0.05, 1.0)), kw))

    def chord(self, beat, dur, pitches, vel=0.7, strum=0.0, **kw):
        for i, p in enumerate(pitches):
            self.note(beat, dur, p, vel * (1 - 0.04 * i), delay=i * strum, **kw)

    def hit(self, beat, name, vel=0.8, **kw):
        self.note(beat, 0.1, name, vel, **kw)

    def raw(self, t0, buf):
        self.raws.append((t0, buf))

    def end_time(self):
        e = [a + b for a, b, *_ in self.ev] + [t0 + len(b) / SR for t0, b in self.raws]
        return max(e) if e else 0.0

    def render(self, n_total):
        out = np.zeros((n_total, 2))
        fn = INSTRUMENTS[self.inst]
        cache = {}
        last_end = -1.0
        for t0, dur, pitch, vel, kw in sorted(self.ev, key=lambda e: e[0]):
            args = dict(self.kw)
            args.update(kw)
            pan = args.pop('pan', None)
            gain = args.pop('gain', 1.0)
            if pan is None:
                pan = self.pan + (DRUMS[pitch][1] if self.inst == 'drums' else 0.0)
            if self.inst in MONO_LEGATO and 'legato' not in args:
                args['legato'] = t0 < last_end + 0.02
            last_end = max(last_end, t0 + dur)
            if self.inst in CACHEABLE:
                vq = round(vel * 20) / 20
                key = (pitch, round(dur, 2), vq, tuple(sorted(args.items())))
                if key not in cache:
                    cache[key] = fn(pitch, round(dur, 2), max(vq, 0.05), self.song.rng, **args)
                y = cache[key] * (vel / max(vq, 0.05))
            else:
                y = fn(pitch, dur, vel, self.song.rng, **args)
            i0 = int(round(t0 * SR))
            if i0 >= n_total:
                continue
            y = y[: n_total - i0] * gain
            a = (np.clip(pan, -1, 1) + 1) * np.pi / 4
            out[i0:i0 + len(y), 0] += y * math.cos(a)
            out[i0:i0 + len(y), 1] += y * math.sin(a)
        for t0, b in self.raws:
            i0 = int(t0 * SR)
            b = b[: n_total - i0]
            if b.ndim == 1:
                b = np.stack([b, b], axis=1) * 0.7071
            out[i0:i0 + len(b)] += b
        for fx in self.post:
            out = fx(out, self.song.rng)
        return out


class Song:
    def __init__(self, bpm, seed, bpb=4, swing=0.5, t60=1.8, wet=1.0, loud=-17.0):
        self.bpm = bpm
        self.bpb = bpb
        self.swing = swing
        self.rng = np.random.default_rng(seed)
        self.parts = []
        self.t60 = t60
        self.wet = wet
        self.loud = loud
        self._tmap = None

    def tempo(self, points):
        """points: [(beat, bpm), ...] — кусочно-линейное изменение темпа."""
        pts = sorted(points)
        grid = np.arange(0, pts[-1][0] + 600, 1 / 48)
        bpm = np.interp(grid, [p[0] for p in pts], [p[1] for p in pts])
        dt = 60.0 / bpm / 48
        self._tmap = (grid, np.concatenate([[0.0], np.cumsum(dt)[:-1]]))

    def time(self, beat):
        b = math.floor(beat)
        fr = beat - b
        s = self.swing
        x = b + (fr / 0.5 * s if fr < 0.5 else s + (fr - 0.5) / 0.5 * (1 - s))
        if self._tmap is None:
            return x * 60.0 / self.bpm
        return float(np.interp(x, *self._tmap))

    def part(self, inst, **kw):
        p = Part(self, inst, **kw)
        self.parts.append(p)
        return p

    def render(self):
        end = max(p.end_time() for p in self.parts)
        n = int((end + self.t60 + 1.0) * SR)
        mix = np.zeros((n, 2))
        send = np.zeros(n)
        for p in self.parts:
            if not p.ev and not p.raws:
                continue
            buf = p.render(n)
            r = active_rms(buf)
            if r > 0:
                buf *= 10 ** (p.level / 20) / r
            mix += buf
            send += buf.mean(axis=1) * p.send
        ir = make_ir(self.t60, self.rng)
        for ch in range(2):
            mix[:, ch] += signal.oaconvolve(send, ir[ch])[:n] * self.wet
        x = master(mix, self.loud)
        # обрезаем тишину в конце и делаем короткие фейды
        a = np.abs(x).max(axis=1)
        idx = np.nonzero(a > 10 ** (-58 / 20))[0]
        last = min(n, (idx[-1] if len(idx) else n - 1) + int(0.3 * SR))
        x = x[:last]
        f = int(0.3 * SR)
        x[-f:] *= np.linspace(1, 0, f)[:, None] ** 2
        x[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))[:, None]
        return x
