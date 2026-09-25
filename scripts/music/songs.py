"""Партитуры всех треков. Каждая функция возвращает готовый к рендеру Song."""
import numpy as np

from .synth import Song, SR, lp, hp, bp, fx_leslie, fx_autopan, fx_chorus, fx_eq, fx_slapback
from .compose import (
    Changes, Chord, Tune, bars, pc_of, N, near_pc, nearest, voice, drop2, pitches_in,
    walking_bass, jazz_comp, ballad_comp, swing_drums, play_notes, improvise, make_contour, realize,
    end_on, blues_changes, LICKS, TURNAROUND, blues_line, lick_len, shuffle_drums, boogie_bass,
    guitar_boogie, blues_comp_stabs, pads, T3, MAJOR, AEOLIAN, HARM_MINOR, BLUES, MINOR_PENT,
    MAJOR_PENT, DORIAN, key_scale_fn,
)

# --------------------------------------------------------------------------
# Ритмические клетки мелодий (2 такта по 4 доли)
# --------------------------------------------------------------------------
JAZZ_CELLS = [
    [(0, 1), (1, 0.5), (1.5, 0.5), (2, 1.5), (3.5, 0.5), (4, 3)],
    [(0.5, 0.5), (1, 0.5), (1.5, 1), (2.5, 1), (3.5, 0.5), (4, 2.5)],
    [(0, 1.5), (1.5, 0.5), (2, 0.5), (2.5, 0.5), (3, 0.5), (3.5, 0.5), (4, 2)],
    [(1, 1), (2, 0.5), (2.5, 0.5), (3, 0.5), (3.5, 2.5), (6.5, 0.5), (7, 1)],
    [(0, 0.5), (0.5, 0.5), (1, 1), (2, 1), (3, 0.5), (3.5, 3)],
    [(0.5, 1), (1.5, 0.5), (2, 1), (3, 1), (4, 0.5), (4.5, 0.5), (5, 2)],
]
JAZZ_CAD = [
    [(0, 1), (1, 1), (2, 0.5), (2.5, 0.5), (3, 1), (4, 3.5)],
    [(0, 0.5), (0.5, 0.5), (1, 0.5), (1.5, 0.5), (2, 1), (3, 1), (4, 4)],
    [(0.5, 0.5), (1, 1), (2, 1.5), (3.5, 0.5), (4, 4)],
]
BALLAD_CELLS = [
    [(0, 2), (2, 1), (3, 0.5), (3.5, 0.5), (4, 3)],
    [(0, 1), (1, 1), (2, 2), (4, 1.5), (5.5, 0.5), (6, 2)],
    [(0.5, 0.5), (1, 0.5), (1.5, 2.5), (4, 1), (5, 1), (6, 2)],
    [(0, 3), (3, 0.5), (3.5, 0.5), (4, 1), (5, 3)],
]
BALLAD_CAD = [[(0, 1), (1, 1), (2, 2), (4, 4)], [(0, 1.5), (1.5, 0.5), (2, 2), (4, 4)]]
BOSSA_CELLS = [
    [(0, 1.5), (1.5, 1), (2.5, 1), (3.5, 0.5), (4, 3)],
    [(0.5, 0.5), (1, 1), (2, 0.5), (2.5, 1.5), (4, 1.5), (5.5, 2)],
    [(0, 1), (1, 0.5), (1.5, 1.5), (3, 1), (4, 3.5)],
    [(1, 0.5), (1.5, 0.5), (2, 0.5), (2.5, 1), (3.5, 0.5), (4, 0.5), (4.5, 3)],
]
BOSSA_CAD = [[(0, 1), (1, 0.5), (1.5, 1), (2.5, 1.5), (4, 4)], [(0.5, 1), (1.5, 1), (2.5, 1.5), (4, 4)]]


def shift(notes, beats):
    return [[b + beats, d, p] for b, d, p in notes]


def cymbal_swell(drums, beat, length=2.0, vel=0.6):
    k = int(length * 6)
    for i in range(k):
        drums.hit(beat + i / 6, 'ride', vel * (0.15 + 0.6 * i / k))


def final_hit(drums, beat, vel=0.8):
    drums.hit(beat, 'crash', vel)
    drums.hit(beat, 'kick', vel)


def rain(seconds, rng, level=1.0):
    """Шум дождя: розоватый шум + отдельные капли, в стерео."""
    n = int(seconds * SR)
    out = np.zeros((n, 2))
    t = np.arange(n) / SR
    for ch in range(2):
        w = rng.standard_normal(n)
        bed = lp(w, 1400) * 0.5 + hp(lp(w, 7000), 1500) * 0.25
        drops = np.zeros(n)
        k = int(seconds * 25)
        pos = rng.integers(0, n - 2000, k)
        for p in pos:
            m = int(rng.uniform(0.004, 0.02) * SR)
            f = rng.uniform(1800, 5500)
            drops[p:p + m] += np.sin(2 * np.pi * f * np.arange(m) / SR) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.2, 1)
        out[:, ch] = bed + drops * 0.6
    fade = np.minimum(1, np.minimum(t / 3.0, (seconds - t) / 4.0))
    return out * fade[:, None] * level


# ==========================================================================
# JAZZ
# ==========================================================================
def midnight_avenue():
    s = Song(132, seed=101, swing=0.64, t60=1.6, loud=-17)
    rng = s.rng
    A = bars('Fmaj7 | D7 | Gm7 | C7 | Am7 D7 | Gm7 C7 | Fmaj7 D7 | Gm7 C7')
    B = bars('Cm7 | F7 | Bbmaj7 | Bbmaj7 | Dm7 | G7 | Gm7 | C7')
    intro = bars('Gm7 C7 | Am7 D7 | Gm7 C7 | Gm7 C7')
    tag = bars('Gm7 C7 | Am7 D7 | Gm7 C7 | F69')
    form = A + A + B + A
    ch = Changes(intro + form + A + A + B + A + A + tag)
    total = len(ch.bars)
    bass = s.part('upright', level=-19, send=0.12)
    piano = s.part('piano', pan=-0.3, level=-25, send=0.25)
    drums = s.part('drums', level=-22, send=0.1, jitter=0.003)
    vibes = s.part('vibes', pan=0.25, level=-16, send=0.3, jitter=0.004)

    walking_bass(bass, ch, 0, total - 1, rng)
    jazz_comp(piano, ch, 0, 52, rng)
    jazz_comp(piano, ch, 52, 68, rng, lo=45, hi=62, vel=0.45, density=0.6)
    jazz_comp(piano, ch, 68, total - 1, rng)
    swing_drums(drums, 0, total - 1, rng)

    tune = Tune(ch, np.random.default_rng(7), JAZZ_CELLS, JAZZ_CAD, 65, 84, pc_of('F'))
    a = tune.section(4, 8, start=N('A4'))
    b = tune.section(20, 8, ending='half')
    head = a + shift(a, 8 * 4) + b + shift(a, 24 * 4)
    play_notes(vibes, head, vel=0.85, rng=rng, legato=0.9)
    improvise(vibes, ch, 36, 52, rng, 62, 86, density=0.5)
    improvise(piano, ch, 52, 68, rng, 62, 84, density=0.55, vel=0.75)
    play_notes(vibes, shift(a, 64 * 4), vel=0.85, rng=rng)  # последняя A
    end = (total - 1) * 4
    cymbal_swell(drums, end - 2)
    final_hit(drums, end)
    bass.note(end, 6, N('F1'), 0.9)
    piano.chord(end, 8, [N('A3'), N('D4'), N('G4'), N('C5')], 0.6, strum=0.05)
    vibes.note(end, 8, N('A5'), 0.8)
    return s


def blue_velvet_rain():
    s = Song(64, seed=202, swing=0.66, t60=2.4, loud=-18)
    rng = s.rng
    A = bars('Ebmaj7 | Cm7 | Fm7 | Bb7 | Gm7 C7 | Fm7 Bb7 | Ebmaj7 Ab7 | Gm7 C7b9')
    B = bars('Fm7 | Bb7 | Gm7 | C7 | Abmaj7 | Abm6 | Gm7 C7 | Fm7 Bb7')
    intro = bars('Fm7 | Bb7')
    tag = bars('Fm7 Bb7 | Ebmaj9')
    ch = Changes(intro + A + B + A + B + tag)
    total = len(ch.bars)
    rh = s.part('piano', pan=0.1, level=-16, send=0.35)
    lh = s.part('piano', pan=-0.15, level=-23, send=0.35)
    bass = s.part('upright', level=-20, send=0.15)
    drums = s.part('drums', level=-27, send=0.15, jitter=0.004)
    sweep = s.part('sweep', level=-33, send=0.1, pan=0.2)
    amb = s.part('drums', level=-35, send=0.0)

    ballad_comp(lh, ch, 0, total - 1, rng)
    for bar in range(0, total - 1):
        for b in (0, 2):
            beat = bar * 4 + b
            c = ch.at(beat)
            p = near_pc(c.bass if ch.is_change(beat) else (c.root + 7) % 12, 38, 31, 48)
            bass.note(beat, 1.9, p, 0.75 * rng.uniform(0.9, 1.05))
    swing_drums(drums, 2, total - 1, rng, style='brush', vel=0.6, sweep_part=sweep)

    tune = Tune(ch, np.random.default_rng(11), BALLAD_CELLS, BALLAD_CAD, 67, 86, pc_of('Eb'))
    a = tune.section(2, 8, start=N('G5'))
    b = tune.section(10, 8, ending='half')
    play_notes(rh, a + b, vel=0.75, rng=rng)
    improvise(rh, ch, 18, 26, rng, 65, 88, density=0.35, vel=0.65)
    play_notes(rh, shift(b, 64), vel=0.72, rng=rng)
    end = (total - 1) * 4
    bass.note(end, 8, N('Eb1'), 0.8)
    lh.chord(end, 10, [N('G3'), N('Bb3'), N('D4'), N('F4')], 0.5, strum=0.07)
    rh.chord(end + 0.5, 10, [N('Bb4'), N('Eb5'), N('G5')], 0.45, strum=0.1)
    drums.hit(end, 'ride', 0.35)
    secs = s.time(end) + 8
    amb.raw(0.0, rain(secs, rng))
    return s


def smoke_and_saxophone():
    s = Song(100, seed=303, swing=0.66, t60=2.0, loud=-17)
    rng = s.rng
    F = bars('Cm7 | Cm7 | Fm7 | Fm7 | Dm7b5 | G7b9 | Cm7 | Cm7 | Abmaj7 | Abmaj7 | Dm7b5 | G7b9 | '
             'Cm7 Ab7 | Dm7b5 G7b9 | Cm7 | Dm7b5 G7b9')
    intro = bars('Cm7 | Cm7 | Dm7b5 | G7b9')
    tag = bars('Cm7 | Dm7b5 G7b9 | Cm9')
    ch = Changes(intro + F + F + F[:8] + F[8:] + tag)
    total = len(ch.bars)
    bass = s.part('upright', level=-19, send=0.12)
    piano = s.part('piano', pan=-0.3, level=-25, send=0.3)
    drums = s.part('drums', level=-25, send=0.12, jitter=0.003)
    sweep = s.part('sweep', level=-32, send=0.1, pan=0.2)
    sax = s.part('sax', pan=0.15, level=-15, send=0.35, jitter=0.008)

    walking_bass(bass, ch, 0, total - 1, rng, vel=0.8)
    jazz_comp(piano, ch, 0, 36, rng, vel=0.5)
    jazz_comp(piano, ch, 36, 44, rng, lo=45, hi=62, vel=0.42, density=0.6)
    jazz_comp(piano, ch, 44, total - 1, rng, vel=0.5)
    swing_drums(drums, 0, total - 1, rng, style='brush', vel=0.75, sweep_part=sweep)

    tune = Tune(ch, np.random.default_rng(5), JAZZ_CELLS, JAZZ_CAD, 60, 79, pc_of('C'),
                key_scale=AEOLIAN)
    h1 = tune.section(4, 8, plan='AaAB', ending='half')
    h2 = tune.section(12, 8, plan='BbBC')
    play_notes(sax, h1 + h2, vel=0.82, rng=rng, accent_offbeats=0.08)
    improvise(sax, ch, 20, 36, rng, 58, 81, density=0.55, vel=0.85, approach=0.3)
    improvise(piano, ch, 36, 44, rng, 60, 84, density=0.5, vel=0.7)
    play_notes(sax, shift(h2, 32 * 4), vel=0.82, rng=rng, accent_offbeats=0.08)
    end = (total - 1) * 4
    cymbal_swell(drums, end - 2, vel=0.4)
    drums.hit(end, 'ride', 0.5)
    drums.hit(end, 'kick', 0.5)
    bass.note(end, 6, N('C2'), 0.85)
    piano.chord(end, 8, [N('Eb3'), N('G3'), N('Bb3'), N('D4')], 0.55, strum=0.05)
    sax.note(end, 5, N('D5'), 0.75)
    return s


HIJAZ = {pc_of(x) for x in ('D', 'Eb', 'F#', 'G', 'A', 'Bb', 'C')}


def late_night_samarkand():
    s = Song(104, seed=404, swing=0.5, t60=2.2, loud=-17)
    rng = s.rng
    V = bars('D7b9 | D7b9 | Ebmaj7/D | D7b9')
    A = bars('D7b9 | D7b9 | Ebmaj7/D | D7b9 | Gm | Gm | Ebmaj7 | D7b9')
    B = bars('Gm | Cm | D7b9 | Gm | Ebmaj7 | Cm | D7b9 | D7b9')
    ch = Changes(V + V + A + B + A + V + V + B + A + V)
    total = len(ch.bars)
    bass = s.part('upright', level=-18, send=0.12)
    ep = s.part('epiano', pan=-0.3, level=-25, send=0.3, post=[fx_autopan])
    drums = s.part('drums', level=-20, send=0.15, jitter=0.004)
    drone = s.part('strings', level=-31, send=0.4, attack=1.5, release=1.5, vib=0.05)
    flute = s.part('flute', pan=0.2, level=-15, send=0.4, breath=0.12, jitter=0.006)
    scale_fn = lambda c: HIJAZ

    for bar in range(total):
        c = ch.at(bar * 4)
        r = near_pc(c.bass, N('D2'), N('A1'), N('G2'))
        sc = pitches_in(HIJAZ, r - 12, r + 12)
        below = max(p for p in sc if p < r)
        fifth = r - 5
        if bar < 2:
            continue
        v = 0.85 if bar < total - 2 else 0.6
        for b, d, p in ((0, 1, r), (1.5, 0.5, r), (2, 0.5, fifth), (2.5, 0.5, below), (3, 1, r)):
            bass.note(bar * 4 + b, d * 0.9, p, v * rng.uniform(0.9, 1.05))
    for bar in range(total):
        B = bar * 4
        fade = 1.0 if bar < total - 3 else 0.6
        for b, name, v in ((0, 'dum', 0.9), (0.5, 'tak', 0.6), (1.5, 'tak', 0.7), (2, 'dum', 0.8), (3, 'tak', 0.7)):
            drums.hit(B + b, name, v * fade * rng.uniform(0.9, 1.05))
        for b in (0.75, 1.25, 2.5, 3.5, 3.75):
            if rng.random() < 0.45:
                drums.hit(B + b, 'ka', 0.5 * fade * rng.uniform(0.7, 1.0))
        if bar % 8 == 7:
            for k in range(8):
                drums.hit(B + 2 + k * 0.25, 'tak' if k % 2 else 'ka', (0.4 + 0.07 * k) * fade)
    prev = None
    for bar in range(4, total):
        c = ch.at(bar * 4)
        v = voice(c.rootless(), 55, 72, prev)
        prev = v
        for b, d in ((0, 1.2), (1.5, 0.4), (3, 0.8)):
            ep.chord(bar * 4 + b, d, v, 0.5 * rng.uniform(0.85, 1.05), strum=0.01)
    for bar in range(0, total, 4):
        drone.note(bar * 4, 16, N('D3'), 0.5)
        drone.note(bar * 4, 16, N('A3'), 0.4)

    tune = Tune(ch, np.random.default_rng(21), JAZZ_CELLS[:3] + BOSSA_CELLS[:2], JAZZ_CAD, 62, 86,
                pc_of('D'), scale_fn=scale_fn)
    a = tune.section(8, 8, start=N('A4'))
    b = tune.section(16, 8, plan='BbDC')

    def orn(notes):
        out = []
        for i, (bt, d, p) in enumerate(notes):
            if d >= 1 and rng.random() < 0.6:
                up = min([q for q in pitches_in(HIJAZ, p + 1, p + 4)] or [p + 1])
                out.append([bt - 0.18, 0.16, up])
            out.append([bt, d, p])
        return out

    play_notes(flute, orn(a + b + shift(a, 16 * 4)), vel=0.8, rng=rng)
    improvise(flute, ch, 32, 48, rng, 62, 86, density=0.55, vel=0.8, scale_fn=scale_fn, triplets=0.15)
    play_notes(flute, orn(shift(a, 40 * 4)), vel=0.8, rng=rng)
    end = total * 4
    bass.note(end, 4, N('D2'), 0.8)
    drums.hit(end, 'dum', 0.9)
    ep.chord(end, 6, [N('F#3'), N('C4'), N('Eb4'), N('A4')], 0.45, strum=0.08)
    flute.note(end, 4, N('D5'), 0.7)
    return s


def autumn_coffee():
    s = Song(120, seed=505, swing=0.5, t60=1.8, loud=-17)
    rng = s.rng
    A = bars('Gmaj7 | G6 | Am7 | D7 | Bm7 | E7b9 | Am7 | D7')
    B = bars('Cmaj7 | Cm6 | Bm7 | E7b9 | Am7 | D7 | Gmaj7 | Am7 D7')
    intro = bars('Am7 | D7 | Am7 | D7')
    outro = bars('Gmaj7 | G6 | Gmaj7 | G69')
    ch = Changes(intro + A + B + A + B + A + B + outro)
    total = len(ch.bars)
    bass = s.part('upright', level=-19, send=0.12)
    gtr = s.part('pluck', pan=-0.35, level=-23, send=0.25, t60=2.2, bright=0.45, pick=0.2)
    drums = s.part('drums', level=-25, send=0.1, jitter=0.003)
    ep = s.part('epiano', pan=0.2, level=-16, send=0.3, post=[fx_chorus])
    solo_gtr = s.part('pluck', pan=0.3, level=-17, send=0.3, t60=2.5, bright=0.55, pick=0.18)

    prev = None
    for bar in range(total - 1):
        c = ch.at(bar * 4)
        r = near_pc(c.bass, N('G2'), N('E2'), N('D3'))
        fifth = r + 7 if r + 7 <= N('D3') else r - 5
        for b, d, p in ((0, 1.4, r), (1.5, 0.45, fifth), (2, 1.4, fifth), (3.5, 0.45, r)):
            bass.note(bar * 4 + b, d, p, 0.8 * rng.uniform(0.9, 1.05))
        hits = (0, 1.5, 3) if bar % 2 == 0 else (1, 2.5)
        for b in hits:
            cc = ch.at(bar * 4 + b)
            v = drop2(voice(cc.rootless(), 55, 70, prev))
            prev = voice(cc.rootless(), 55, 70, prev)
            gtr.chord(bar * 4 + b, 0.9, v, 0.6 * rng.uniform(0.85, 1.05), strum=0.012)
        B_ = bar * 4
        for b in ((0, 1.5, 3) if bar % 2 == 0 else (1, 2.5)):
            drums.hit(B_ + b, 'rim', 0.6 * rng.uniform(0.9, 1.05))
        for k in range(8):
            drums.hit(B_ + k * 0.5, 'shaker', (0.55 if k % 2 else 0.35) * rng.uniform(0.9, 1.1))
        for b, v in ((0, 0.6), (1.5, 0.35), (2, 0.55), (3.5, 0.35)):
            drums.hit(B_ + b, 'kick', v)

    tune = Tune(ch, np.random.default_rng(3), BOSSA_CELLS, BOSSA_CAD, 64, 83, pc_of('G'))
    a = tune.section(4, 8, start=N('B4'))
    b = tune.section(12, 8, plan='AaBC')
    play_notes(ep, a + b, vel=0.75, rng=rng)
    improvise(ep, ch, 20, 36, rng, 62, 86, density=0.45, vel=0.7)
    improvise(solo_gtr, ch, 36, 44, rng, 57, 81, density=0.5, vel=0.8)
    play_notes(ep, shift(b, 32 * 4), vel=0.75, rng=rng)
    end = (total - 1) * 4
    bass.note(end, 6, N('G2'), 0.8)
    gtr.chord(end, 6, [N('G2'), N('D3'), N('F#3'), N('B3'), N('E4')], 0.6, strum=0.05)
    ep.note(end, 6, N('A5'), 0.6)
    drums.hit(end, 'rim', 0.5)
    return s


def brass_reflections():
    s = Song(172, seed=606, swing=0.6, t60=1.5, loud=-16)
    rng = s.rng
    A1 = bars('Bbmaj7 G7 | Cm7 F7 | Dm7 G7 | Cm7 F7 | Fm7 Bb7 | Ebmaj7 Ab7 | Dm7 G7 | Cm7 F7')
    A2 = A1[:6] + bars('Cm7 F7 | Bb6')
    Bb = bars('D7 | D7 | G7 | G7 | C7 | C7 | F7 | F7')
    form = A1 + A2 + Bb + A2
    intro = bars('Cm7 F7 | Cm7 F7 | Cm7 F7 | Cm7 F7 | Cm7 F7 | Cm7 F7 | Cm7 F7 | Cm7 F7')
    tag = bars('Cm7 F7 | Dm7 G7 | Cm7 F7 | Bb69')
    ch = Changes(intro + form + form + A1 + A2 + Bb + A2 + tag)
    total = len(ch.bars)
    bass = s.part('upright', level=-19, send=0.1)
    piano = s.part('piano', pan=-0.3, level=-25, send=0.22)
    drums = s.part('drums', level=-21, send=0.08, jitter=0.003)
    tpt = s.part('trumpet', pan=0.2, level=-15, send=0.3, jitter=0.005)

    for bar in range(4):
        for b in range(4):
            drums.hit(bar * 4 + b, 'ride', 0.7 if b % 2 else 0.5)
        drums.hit(bar * 4 + 1, 'pedal', 0.5)
        drums.hit(bar * 4 + 3, 'pedal', 0.5)
        drums.hit(bar * 4 + 2.5, 'snare', 0.4)
    swing_drums(drums, 4, total - 1, rng, vel=0.85)
    walking_bass(bass, ch, 4, total - 1, rng, vel=0.85)
    jazz_comp(piano, ch, 4, 72, rng)
    jazz_comp(piano, ch, 72, 88, rng, lo=45, hi=62, vel=0.45, density=0.6)
    jazz_comp(piano, ch, 88, total - 1, rng)

    tune = Tune(ch, np.random.default_rng(13), JAZZ_CELLS, JAZZ_CAD, 64, 84, pc_of('Bb'))
    a1 = tune.section(8, 8, start=N('D5'))
    a2 = tune.section(16, 8, plan='AaAC')
    br = tune.section(24, 8, plan='BbDd', ending='half')
    head = a1 + a2 + br + shift(a2, 16 * 4)
    play_notes(tpt, head, vel=0.85, rng=rng, legato=0.85, accent_offbeats=0.1)
    improvise(tpt, ch, 40, 72, rng, 62, 86, density=0.62, vel=0.85, approach=0.3)
    improvise(piano, ch, 72, 88, rng, 62, 86, density=0.6, vel=0.75)
    play_notes(tpt, shift(br + shift(a2, 16 * 4), 64 * 4), vel=0.85, rng=rng, legato=0.85,
               accent_offbeats=0.1)
    end = (total - 1) * 4
    cymbal_swell(drums, end - 2, vel=0.7)
    final_hit(drums, end, 0.9)
    bass.note(end, 5, N('Bb1'), 0.9)
    piano.chord(end, 6, [N('D3'), N('G3'), N('C4'), N('F4')], 0.7, strum=0.03)
    tpt.note(end, 5, N('F5'), 0.85)
    return s


# ==========================================================================
# CLASSIC
# ==========================================================================
CL44 = [
    [(0, 2), (2, 1), (3, 1)],
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(0, 1.5), (1.5, 0.5), (2, 2)],
    [(0, 1), (1, 0.5), (1.5, 0.5), (2, 1), (3, 1)],
    [(0, 0.5), (0.5, 0.5), (1, 1), (2, 2)],
    [(0, 3), (3, 1)],
]
CL44_CAD = [[(0, 1), (1, 1), (2, 2)], [(0, 2), (2, 2)], [(0, 1.5), (1.5, 0.5), (2, 2)]]
NOCT = [
    [(0, 3), (3, 1)],
    [(0, 1.5), (1.5, 0.5), (2, 1), (3, 1)],
    [(0, 2), (2, 2 / 3), (2 + 2 / 3, 1 / 3), (3, 1)],
    [(0, 1), (1, 2), (3, 1 / 3), (3 + 1 / 3, 1 / 3), (3 + 2 / 3, 1 / 3)],
    [(0, 2.5), (2.5, 0.5), (3, 0.5), (3.5, 0.5)],
]
NOCT_CAD = [[(0, 2), (2, 2)], [(0, 1), (1, 1), (2, 2)]]
WALTZ = [
    [(0, 1), (1, 1), (2, 1), (3, 2), (5, 1)],
    [(0, 1.5), (1.5, 0.5), (2, 1), (3, 3)],
    [(0, 2), (2, 1), (3, 1), (4, 1), (5, 1)],
    [(1, 1), (2, 1), (3, 1.5), (4.5, 0.5), (5, 1)],
    [(0, 0.5), (0.5, 0.5), (1, 1), (2, 1), (3, 3)],
]
WALTZ_CAD = [[(0, 1), (1, 1), (2, 1), (3, 3)], [(0, 2), (2, 1), (3, 3)]]
PAST = [
    [(0, 2 / 3), (2 / 3, 1 / 3), (1, 1), (2, 2 / 3), (2 + 2 / 3, 1 / 3), (3, 1)],
    [(0, 1), (1, 1 / 3), (4 / 3, 1 / 3), (5 / 3, 1 / 3), (2, 2)],
    [(0, 1 / 3), (1 / 3, 1 / 3), (2 / 3, 1 / 3), (1, 2 / 3), (5 / 3, 1 / 3), (2, 2)],
    [(0, 4 / 3), (4 / 3, 1 / 3), (5 / 3, 1 / 3), (2, 1), (3, 1)],
]
PAST_CAD = [[(0, 2 / 3), (2 / 3, 1 / 3), (1, 1), (2, 2)], [(0, 1), (1, 1), (2, 2)]]

strong44 = lambda b, d: (b % 2 == 0 and d >= 1) or d >= 2
strong34 = lambda b, d: (b % 3 == 0) or d >= 2
strong68 = lambda b, d: (b % 1 == 0 and d >= 2 / 3) or d >= 1


def upper4(c, prev, lo=55, hi=77):
    v = voice(c.pcs[:4], lo, hi, prev)
    if len(v) < 4:
        v = v + [v[0] + 12]
    return v[:4]


def morning_prelude():
    s = Song(66, seed=701, t60=2.6, loud=-19)
    prog = bars('C | Am/C | Dm7/C | G7/B | C | Fmaj7/C | D7/C | G/B | Am | D7 | G | Em | Am7 | D7 | '
                'Gmaj7 | G7 | C/E | Fmaj7 | Dm7 | E7 | Am | Dm/F | G7sus4 | G7 | C/G | F/G | G7 | C/G | '
                'Dm7/G | G7 | C')
    n = len(prog)
    s.tempo([(0, 66), ((n - 5) * 4, 66), ((n - 1) * 4, 48)])
    ch = Changes(prog)
    rng = s.rng
    pno = s.part('piano', level=-15, send=0.45, jitter=0.004)
    prev_up, prev_bass = None, N('C3')
    for bar in range(n - 1):
        c = ch.at(bar * 4)
        bass = near_pc(c.bass, prev_bass, N('E2'), N('D3'))
        up = upper4(c, prev_up, 55, 76)
        tenor, fig = up[0], up[1:]
        vel = 0.42 + 0.3 * np.sin(np.pi * min(1, bar / (n - 4))) ** 1.5
        for h in (0, 2):
            B = bar * 4 + h
            pno.note(B, 2, bass, vel)
            pno.note(B + 0.25, 1.75, tenor, vel * 0.8)
            for k, idx in enumerate((0, 1, 2, 0, 1, 2)):
                pno.note(B + 0.5 + k * 0.25, 1.5 - k * 0.25, fig[idx], vel * (0.72 if k % 3 else 0.8))
        prev_up, prev_bass = up, bass
    end = (n - 1) * 4
    pno.chord(end, 10, [N('C2'), N('C3'), N('G3'), N('C4'), N('E4'), N('G4'), N('C5')], 0.5, strum=0.09)
    return s


def serenade_in_g():
    s = Song(76, seed=702, t60=2.0, loud=-18)
    rng = s.rng
    A = bars('G | Em | Am | D7 | G | C | D7 | G')
    B = bars('Em | B7 | Em | A7 | D | A7 | D | D7')
    coda = bars('G | C | D7 | G | G')
    ch = Changes(bars('G | G') + A + A + B + A + coda)
    total = len(ch.bars)
    vln = s.part('strings', pan=-0.2, level=-14, send=0.35, voices=2, vib=0.18, attack=0.07, detune=0.04)
    inner = s.part('strings', pan=0.25, level=-24, send=0.3, voices=3, attack=0.03, release=0.12, vib=0.05)
    cello = s.part('pluck', pan=0.05, level=-20, send=0.3, t60=0.9, bright=0.3, pick=0.25, lowpass=2500)
    scale_fn = key_scale_fn(pc_of('G'))
    prev = None
    for bar in range(total - 1):
        c = ch.at(bar * 4)
        v = voice(c.pcs[:3], 55, 69, prev)
        prev = v
        for k in range(8):
            inner.chord(bar * 4 + k * 0.5, 0.42, v, 0.4 * (1.1 if k % 2 == 0 else 0.9))
        r = near_pc(c.root, N('G2'), N('D2'), N('C3'))
        cello.note(bar * 4, 1, r, 0.85)
        cello.note(bar * 4 + 2, 1, r + 7 if r + 7 <= N('D3') else r - 5, 0.7)
    tune = Tune(ch, np.random.default_rng(31), CL44, CL44_CAD, N('D4'), N('B5'), pc_of('G'), cell_bars=1,
                scale_fn=scale_fn, strong_fn=strong44)
    a = tune.section(2, 8, plan='ABaHABDC', start=N('B4'))
    b = tune.section(18, 8, plan='EeFHEeGH')
    play_notes(vln, a + shift(a, 32) + b + shift(a, 24 * 4), vel=0.8, rng=rng, legato=0.97)
    coda_m = tune.section(34, 4, plan='AaDC')
    play_notes(vln, coda_m, vel=0.75, rng=rng)
    end = (total - 1) * 4
    vln.note(end, 4, N('G4'), 0.6)
    inner.chord(end, 4, [N('B3'), N('D4'), N('G4')], 0.4)
    cello.note(end, 2, N('G2'), 0.8)
    return s


def nocturne_silent_lake():
    s = Song(58, seed=703, t60=2.8, loud=-19)
    A = bars('Eb | Cm | Fm7 | Bb7 | Eb | Abmaj7 | Bb7 | Eb')
    B = bars('Cm | G7 | Cm | Ab | Fm | G7 | Cm | Bb7')
    coda = bars('Eb | Ab | Eb/Bb | Bb7 | Eb | Eb')
    prog = bars('Eb') + A + B + A + coda
    n = len(prog)
    s.tempo([(0, 58), (8 * 4, 58), (9 * 4, 54), (9.5 * 4, 58), ((n - 6) * 4, 58), ((n - 1) * 4, 44)])
    ch = Changes(prog)
    rng = s.rng
    rh = s.part('piano', pan=0.1, level=-15, send=0.45, jitter=0.006)
    lh = s.part('piano', pan=-0.15, level=-22, send=0.45, jitter=0.004)
    prev_b = N('Eb2')
    for bar in range(n - 1):
        c = ch.at(bar * 4)
        bass = near_pc(c.bass, prev_b, N('Bb1'), N('Ab2'))
        third = (c.root + c.iv[1]) % 12
        tones = [bass, bass + 7, near_pc(c.root, bass + 12, bass + 9, bass + 20),
                 near_pc(third, bass + 16, bass + 12, bass + 24), bass + 19]
        tones[4] = near_pc((c.root + 7) % 12, tones[3] + 3, tones[3] + 1, tones[3] + 9)
        vel = 0.4 + 0.12 * np.sin(np.pi * bar / n)
        for h in (0, 2):
            for k, idx in enumerate((0, 1, 2, 3, 4, 3)):
                beat = bar * 4 + h + k / 3
                rest = bar * 4 + h + 2 - beat
                lh.note(beat, rest, tones[idx], vel * (1.0 if k == 0 else 0.7))
        prev_b = bass
    tune = Tune(ch, np.random.default_rng(41), NOCT, NOCT_CAD, N('G4'), N('Eb6'), pc_of('Eb'), cell_bars=1,
                scale_fn=key_scale_fn(pc_of('Eb')), strong_fn=strong44)
    a = tune.section(1, 8, plan='ABaHABDC', start=N('Bb4'))
    b = tune.section(9, 8, plan='EeFHEeGH')

    def turns(notes):
        out = []
        for bt, d, p in notes:
            if d >= 2 and rng.random() < 0.5:
                sc = pitches_in(key_scale_fn(pc_of('Eb'))(ch.at(bt)), p - 3, p + 3)
                up = min([q for q in sc if q > p] or [p + 2])
                dn = max([q for q in sc if q < p] or [p - 1])
                out += [[bt, 1 / 6, p], [bt + 1 / 6, 1 / 6, up], [bt + 2 / 6, 1 / 6, p], [bt + 3 / 6, 1 / 6, dn]]
                out.append([bt + 4 / 6, d - 4 / 6, p])
            else:
                out.append([bt, d, p])
        return out

    play_notes(rh, a + b + turns(shift(a, 16 * 4)), vel=0.72, rng=rng, legato=1.0)
    coda_m = tune.section(25, 4, plan='AaDC', start=N('G5'))
    play_notes(rh, coda_m, vel=0.6, rng=rng)
    end = (n - 1) * 4
    lh.chord(end, 8, [N('Eb2'), N('Bb2'), N('G3')], 0.45, strum=0.1)
    rh.chord(end + 0.3, 8, [N('Bb4'), N('Eb5'), N('G5'), N('Bb5')], 0.4, strum=0.12)
    return s


def waltz_of_the_lanterns():
    s = Song(120, seed=704, bpb=3, t60=2.0, loud=-18)
    A = bars('F | F | C7 | C7 | C7 | C7 | F | F | F | F | Bb | Bb | F/C | C7 | F | F')
    B = bars('Dm | Dm | A7 | A7 | A7 | A7 | Dm | Dm | Gm | Gm | Dm | Dm | E7 | A7 | Dm | C7')
    coda = bars('F | Bb | F/C | C7 | F | F')
    prog = bars('F | C7') + A + A + B + A + coda
    n = len(prog)
    s.tempo([(0, 120), ((n - 4) * 3, 120), ((n - 1) * 3, 84)])
    ch = Changes(prog, bpb=3)
    rng = s.rng
    rh = s.part('piano', pan=0.12, level=-15, send=0.35)
    lh = s.part('piano', pan=-0.12, level=-22, send=0.35)
    strg = s.part('strings', pan=-0.3, level=-22, send=0.4, voices=3, attack=0.12, vib=0.14)
    prev = None
    for bar in range(n - 1):
        c = ch.at(bar * 3)
        r = near_pc(c.bass if bar % 2 == 0 else (c.root + 7) % 12, N('F2'), N('C2'), N('C3'))
        v = voice(c.pcs[:3], N('F3'), N('F4'), prev)
        prev = v
        lh.note(bar * 3, 1.0, r, 0.6)
        lh.chord(bar * 3 + 1, 0.55, v, 0.38)
        lh.chord(bar * 3 + 2, 0.55, v, 0.34)
    tune = Tune(ch, np.random.default_rng(51), WALTZ, WALTZ_CAD, N('A4'), N('D6'), pc_of('F'), cell_bars=2,
                scale_fn=key_scale_fn(pc_of('F')), strong_fn=strong34)
    a = tune.section(2, 16, plan='AaBCAaDC', start=N('C5'))
    tune_b = Tune(ch, np.random.default_rng(52), WALTZ, WALTZ_CAD, N('A4'), N('D6'), pc_of('D'), cell_bars=2,
                  scale_fn=key_scale_fn(pc_of('D'), minor=True), strong_fn=strong34, key_scale=AEOLIAN)
    b = tune_b.section(34, 16, plan='EeFCEeGH')
    play_notes(rh, a + shift(a, 16 * 3) + b + shift(a, 48 * 3), vel=0.72, rng=rng, legato=0.9)
    play_notes(strg, [[bt, d, p - 12] for bt, d, p in shift(a, 16 * 3)], vel=0.55, rng=rng, legato=1.0)
    play_notes(strg, [[bt, d, p - 12] for bt, d, p in b], vel=0.5, rng=rng, legato=1.0)
    coda_m = tune.section(66, 6, plan='AaC', start=N('A5'))
    play_notes(rh, coda_m, vel=0.65, rng=rng)
    end = (n - 1) * 3
    lh.chord(end, 5, [N('F2'), N('C3'), N('A3')], 0.5, strum=0.05)
    strg.chord(end, 4, [N('F3'), N('A3'), N('C4')], 0.4)
    return s


CANON_FIGS = {
    1: [[0]],
    2: [[0, 1], [0, -1], [0, 2], [0, -2]],
    4: [[0, 1, 2, 1], [0, -1, -2, -1], [0, 1, 0, -1], [0, -1, 0, 1], [0, 2, 1, 0], [0, -2, -1, 0]],
    8: [[0, 1, 2, 3, 2, 1, 0, -1], [0, -1, -2, -3, -2, -1, 0, 1], [0, 1, 0, -1, 0, 1, 2, 1],
        [0, -1, 0, 1, 0, -1, -2, -1], [0, 2, 1, 3, 2, 4, 3, 1]],
}


def figured_line(ch, bar0, nbars, k, rng, lo, hi, start, scale, figs=None, fig_seq=None):
    """Линия из фигур по полтакта: опора на аккордовый звук + поступенное заполнение."""
    notes, used = [], []
    a = start
    i = 0
    for bar in range(bar0, bar0 + nbars):
        for h in (0, 2):
            beat = bar * 4 + h
            c = ch.at(beat)
            a = nearest(pitches_in(c.tones(3), lo, hi), a)
            if fig_seq is not None:
                fig = fig_seq[i % len(fig_seq)]
            else:
                pool = (figs or CANON_FIGS)[k]
                fig = pool[rng.integers(len(pool))]
            i0 = int(np.argmin([abs(x - a) for x in scale]))
            if i0 + max(fig) > len(scale) - 1 or (rng.random() < 0.5 and i0 + min(fig) >= 0 and fig_seq is None):
                if i0 - max(fig) >= 0:
                    fig = [-x for x in fig]
            used.append(fig)
            d = 2 / len(fig)
            for j, st in enumerate(fig):
                notes.append([beat + j * d, d, scale[int(np.clip(i0 + st, 0, len(scale) - 1))]])
            last = fig[-1] - (fig[-2] if len(fig) > 1 else 0)
            a = notes[-1][2] + (2 if last >= 0 else -2)
            i += 1
    return notes, used


def canon_in_autumn():
    s = Song(62, seed=705, t60=2.6, loud=-18)
    rng = s.rng
    ground = bars('D A/C# | Bm F#m/A | G D/F# | Em7 A7')
    cycles = 8
    ch = Changes(ground * cycles + bars('D'))
    total = len(ch.bars)
    vl = [s.part('strings', pan=p, level=-18, send=0.4, voices=2, vib=0.15, attack=0.1, detune=0.05)
          for p in (-0.5, 0.45, 0.0)]
    cello = s.part('strings', pan=0.1, level=-18, send=0.35, voices=2, attack=0.12, vib=0.08)
    hc = s.part('pluck', pan=-0.2, level=-27, send=0.3, t60=1.6, bright=1.0, octave=0.35, pick=0.1, damp=0.1)
    prev_b, prev = N('D3'), None
    for i, (beat, L, c) in enumerate(ch.ev[:-1]):
        b = near_pc(c.bass, prev_b, N('D2'), N('D3'))
        cello.note(beat, 1.95, b, 0.7)
        prev_b = b
        if beat >= 16:
            v = voice(c.pcs[:3], N('A3'), N('F#4') + 3, prev)
            prev = v
            hc.chord(beat, 1.9, v, 0.5, strum=0.025)
    scale = pitches_in({pc_of(x) for x in ('D', 'E', 'F#', 'G', 'A', 'B', 'C#')}, N('D4'), N('D6'))
    dens = [1, 2, 4, 8, 2]
    segs, a = [], N('F#5')
    for k in dens:
        notes, _ = figured_line(ch, 0, 4, k, rng, N('F#4'), N('C#6'), a, scale)
        segs.append(notes)
        a = notes[-1][2]
    for vi, part in enumerate(vl):
        for si, seg in enumerate(segs):
            cyc = 1 + vi + si
            if cyc >= cycles:
                continue
            play_notes(part, shift(seg, cyc * 16), vel=0.62 + 0.05 * (si == 3), rng=rng, legato=1.0)
    end = cycles * 16
    cello.note(end, 6, N('D3'), 0.7)
    cello.note(end, 6, N('D2'), 0.6)
    for part, p in zip(vl, (N('F#5'), N('A4'), N('D5'))):
        part.note(end, 6, p, 0.55)
    hc.chord(end, 4, [N('D3'), N('A3'), N('D4'), N('F#4')], 0.5, strum=0.04)
    return s


def spring_dance():
    s = Song(100, seed=706, t60=1.8, loud=-17)
    rng = s.rng
    R = bars('F | Bb | Gm7 C7 | F')
    E1 = bars('Dm | Gm | C7 | F | Bb | Em7b5 | A7 | Dm')
    RC = bars('C | F | Dm7 G7 | C')
    E2 = bars('Am | Dm | G7 | C7')
    RD = bars('Dm | Gm | A7 | Dm')
    T = bars('Bb | Gm | C7 | C7')
    END = bars('Bb | C7 | F | F')
    prog = R + R + E1 + RC + E2 + RD + T + R + END
    n = len(prog)
    s.tempo([(0, 100), ((n - 3) * 4, 100), ((n - 1) * 4, 76)])
    ch = Changes(prog)
    vln = s.part('strings', pan=-0.25, level=-14, send=0.3, voices=3, vib=0.1, attack=0.03, release=0.12,
                 detune=0.06)
    inner = s.part('strings', pan=0.3, level=-26, send=0.35, voices=3, attack=0.15, vib=0.06)
    bass = s.part('strings', pan=0.1, level=-19, send=0.25, voices=2, attack=0.02, release=0.1, vib=0.0)
    hc = s.part('pluck', pan=-0.1, level=-24, send=0.25, t60=1.4, bright=1.0, octave=0.35, pick=0.1, damp=0.08)
    prev = None
    for bar in range(n - 2):
        for h in (0, 2):
            beat = bar * 4 + h
            c = ch.at(beat)
            r = near_pc(c.bass, N('F2'), N('C2'), N('B2'))
            for k, p in enumerate((r, r + 12, r, r + 12)):
                bass.note(beat + k * 0.5, 0.4, p, 0.7 if k % 2 == 0 else 0.55)
            v = voice(c.pcs[:4], N('A3'), N('A4'), prev)
            prev = v
            hc.chord(beat, 0.9, v, 0.5, strum=0.012)
            hc.chord(beat + 1, 0.9, v, 0.42, strum=0.012)
            if ch.is_change(beat):
                L = 4 if bar * 4 == beat and not ch.is_change(beat + 2) else 2
                inner.chord(beat, L * 0.98, v, 0.45)
    scale = pitches_in({pc_of(x) for x in ('F', 'G', 'A', 'Bb', 'C', 'D', 'E')}, N('E4'), N('F6'))
    lo, hi = N('F4'), N('E6')
    theme, figs = figured_line(ch, 0, 4, 4, rng, lo, hi, N('A5'), scale)
    theme2, figs2 = figured_line(ch, 4, 4, 8, rng, lo, hi, N('C6'), scale)
    epi, _ = figured_line(ch, 8, 8, 8, rng, lo, hi, N('A5'), scale, fig_seq=[[0, 1, 2, 3, 2, 1, 0, -1], [0, -1, -2, -1, 0, 1, 2, 1]])
    rc, _ = figured_line(ch, 16, 4, 4, rng, lo, hi, N('G5'), scale, fig_seq=figs)
    e2, _ = figured_line(ch, 20, 4, 8, rng, lo, hi, N('E5'), scale, fig_seq=figs2)
    rd, _ = figured_line(ch, 24, 4, 4, rng, lo, hi, N('F5'), scale, fig_seq=figs)
    t2, _ = figured_line(ch, 28, 4, 8, rng, lo, hi, N('D5'), scale)
    r3, _ = figured_line(ch, 32, 4, 4, rng, lo, hi, N('A5'), scale, fig_seq=figs)
    en, _ = figured_line(ch, 36, 2, 4, rng, lo, hi, N('D5'), scale)
    melody = theme + theme2 + epi + rc + e2 + rd + t2 + r3 + en
    play_notes(vln, melody, vel=0.75, rng=rng, legato=0.8)
    end = (n - 2) * 4
    for p in (N('A5'), N('F5'), N('C5')):
        vln.note(end, 7, p, 0.6)
    bass.note(end, 7, N('F2'), 0.7)
    bass.note(end, 7, N('F3'), 0.5)
    hc.chord(end, 4, [N('F3'), N('A3'), N('C4'), N('F4')], 0.55, strum=0.03)
    return s


def voice_satb(c, prev, rng, sop_lo=N('D4'), sop_hi=N('A5'), target=None):
    """Три верхних голоса (тенор, альт, сопрано) с плавным голосоведением."""
    pcs = c.pcs[:4]
    if len(pcs) == 4:
        pcs = [pcs[0], pcs[1], pcs[3]]
    best = None
    for tv in pitches_in(set(pcs), N('C3'), N('G4')):
        for av in pitches_in(set(pcs), N('G3'), N('D5')):
            for sv in pitches_in(set(pcs), sop_lo, sop_hi):
                if not (tv < av < sv) or sv - av > 12 or av - tv > 12:
                    continue
                if len({tv % 12, av % 12, sv % 12}) < len(set(pcs)):
                    continue
                v = (tv, av, sv)
                cost = rng.uniform(0, 1.5)
                if prev:
                    cost += sum(abs(x - y) for x, y in zip(v, prev)) + abs(sv - prev[2]) * 0.5
                else:
                    cost += abs(sv - (sop_lo + sop_hi) / 2)
                if target is not None:
                    cost += abs(sv - target) * 0.8
                if best is None or cost < best[0]:
                    best = (cost, v)
    return list(best[1])


def adagio_grey_morning():
    s = Song(54, seed=707, t60=3.0, loud=-18)
    rng = s.rng
    prog = bars('Gm | Gm/F | Eb | Cm/Eb | D | D7 | Gm | Gm | Cm | F7 | Bb | Eb | Am7b5 | D7 | Gm | D7 | '
                'Eb | Cm7 | F | Bb | Eb | Am7b5 | D7sus4 D7 | Gm | Cm/G | Gm')
    n = len(prog)
    s.tempo([(0, 54), ((n - 4) * 4, 54), ((n - 1) * 4, 40)])
    ch = Changes(prog)
    names = ('tenor', 'alto', 'sop')
    parts = {
        'bass': s.part('strings', pan=0.15, level=-18, send=0.4, voices=3, attack=0.35, vib=0.08, release=0.6),
        'tenor': s.part('strings', pan=0.3, level=-21, send=0.45, voices=3, attack=0.4, vib=0.1, release=0.6),
        'alto': s.part('strings', pan=-0.3, level=-21, send=0.45, voices=3, attack=0.4, vib=0.12, release=0.6),
        'sop': s.part('strings', pan=-0.1, level=-15, send=0.5, voices=3, attack=0.3, vib=0.16, release=0.7,
                      detune=0.05),
    }
    prev, prev_b = None, N('G2')
    ev = ch.ev[:-1]
    for i, (beat, L, c) in enumerate(ev):
        bar = int(beat // 4)
        dyn = 0.45 + 0.35 * np.sin(np.pi * (bar % 8) / 8) + 0.1 * (8 <= bar < 22)
        b = near_pc(c.bass, prev_b, N('C2'), N('D3'))
        parts['bass'].note(beat, L, b, dyn * 0.9, swell=0.3)
        parts['bass'].note(beat, L, b - 12 if b - 12 >= N('C1') + 4 else b, dyn * 0.6)
        prev_b = b
        # мелодия сопрано идёт «аркой» внутри каждой 8-тактовой фразы
        target = N('G4') + 9 * np.sin(np.pi * ((beat / 4) % 8) / 8) + (3 if 8 <= bar < 22 else 0)
        v = voice_satb(c, prev, rng, target=target)
        for vi, name in enumerate(names):
            p = v[vi]
            held = prev is not None and 0 < prev[vi] - p <= 2 and prev[vi] % 12 not in c.pcs and L >= 2
            if held and name != 'tenor':
                parts[name].note(beat, 1, prev[vi], dyn * 0.95)
                parts[name].note(beat + 1, L - 1, p, dyn * 0.85, swell=0.2)
            elif name == 'sop' and L >= 4 and rng.random() < 0.55:
                nxt = voice_satb(ev[i + 1][2], v, np.random.default_rng(bar)) if i + 1 < len(ev) else v
                sc = pitches_in(key_scale_fn(pc_of('G'), minor=True)(c), p - 5, p + 5)
                mid = nearest([q for q in sc if q != p], (p + nxt[2]) / 2 if nxt[2] != p else p + 2)
                parts[name].note(beat, 2, p, dyn, swell=0.3)
                parts[name].note(beat + 2, 1.5, mid, dyn * 0.9)
                parts[name].note(beat + 3.5, 0.5, p if abs(mid - p) > 2 else mid, dyn * 0.8)
            else:
                parts[name].note(beat, L, p, dyn * 0.9, swell=0.25)
        prev = v
    end = (n - 1) * 4
    for name, p in zip(('bass', 'tenor', 'alto', 'sop'), (N('G2'), N('D3'), N('Bb3'), N('G4'))):
        parts[name].note(end, 6, p, 0.5)
    parts['bass'].note(end, 6, N('G1'), 0.4)
    return s


def pastorale_harp_flute():
    s = Song(44, seed=708, bpb=2, t60=2.6, loud=-18)
    rng = s.rng
    A = bars('F | Bb | F | C7 | F | Bb | C7 | F')
    B = bars('Dm | Gm | C7 | F | Bb | Gm7 | C7sus4 | C7')
    coda = bars('Bb | F/C | C7 | F | F')
    prog = bars('F | F') + A + A + B + A + coda
    n = len(prog)
    s.tempo([(0, 44), ((n - 4) * 2, 44), ((n - 1) * 2, 34)])
    ch = Changes(prog, bpb=2)
    harp = s.part('pluck', pan=-0.2, level=-18, send=0.45, t60=3.5, bright=0.5, pick=0.3, damp=0.3)
    flute = s.part('flute', pan=0.2, level=-14, send=0.45, breath=0.05)
    pad = s.part('strings', pan=0.3, level=-30, send=0.5, voices=3, attack=0.8, release=1.0, vib=0.06)
    prev_b = N('F2')
    for bar in range(n - 1):
        c = ch.at(bar * 2)
        bass = near_pc(c.bass, prev_b, N('C2'), N('Bb2'))
        root = near_pc(c.root, bass + 12, bass + 8, bass + 19)
        third = near_pc((c.root + c.iv[1]) % 12, root + 4, root + 1, root + 10)
        fifth = near_pc((c.root + c.iv[2]) % 12, third + 3, third + 1, third + 9)
        tones = [bass, near_pc((c.root + 7) % 12, bass + 7, bass + 3, bass + 11), root, third, fifth]
        tones.append(root + 12)
        for k, idx in enumerate((0, 1, 2, 3, 4, 5)):
            beat = bar * 2 + k / 3
            harp.note(beat, bar * 2 + 2 - beat, tones[idx], 0.55 if k else 0.7)
        prev_b = bass
        if 18 <= bar < 42:
            pad.chord(bar * 2, 1.98, voice(c.pcs[:3], N('F3'), N('F4'), None), 0.4)
    tune = Tune(ch, np.random.default_rng(81), PAST, PAST_CAD, N('F4'), N('F6'), pc_of('F'), cell_bars=2,
                scale_fn=key_scale_fn(pc_of('F')), strong_fn=strong68)
    a = tune.section(2, 8, plan='AaBC', start=N('A5'))
    b = tune.section(18, 8, plan='DdEH')
    play_notes(flute, a + shift(a, 16) + b + shift(a, 24 * 2), vel=0.75, rng=rng, legato=0.97)
    cm = tune.section(34, 4, plan='AC')
    play_notes(flute, cm[:-1], vel=0.65, rng=rng)
    end = (n - 1) * 2
    flute.note(end, 3, N('F5'), 0.6)
    sc = pitches_in({pc_of(x) for x in ('F', 'G', 'A', 'Bb', 'C', 'D', 'E')}, N('F3'), N('F6'))
    for i, p in enumerate(sc):
        harp.note(end - 1 + i / len(sc), 4, p, 0.35 + 0.3 * i / len(sc))
    harp.chord(end + 0.1, 4, [N('F2'), N('C3'), N('F3'), N('A3')], 0.6, strum=0.05)
    return s


# ==========================================================================
# BLUES
# ==========================================================================
def crackle(seconds, rng, density=5.0):
    """Потрескивание винила + лёгкое шипение."""
    n = int(seconds * SR)
    out = np.zeros((n, 2))
    for ch in range(2):
        x = hp(rng.standard_normal(n), 4000) * 0.015
        for p in rng.integers(0, n - 200, int(seconds * density)):
            m = int(rng.uniform(0.0003, 0.0015) * SR)
            x[p:p + m] += rng.uniform(-1, 1) * np.exp(-np.arange(m) / (m / 3))
        out[:, ch] = hp(x, 800)
    return out


def pick_licks(rng, budget, pool=None):
    pool = pool or LICKS
    seq, tot = [], 0.0
    while tot < budget:
        lk = pool[rng.integers(len(pool))]
        if seq and tot + lick_len(lk) > budget + 1:
            break
        seq.append(lk)
        tot += lick_len(lk)
    return seq


def blues_chorus(part, bar0, rng, ref, intensity=0, minor=False, style='bend', last=False, vel=0.85, **kw):
    """Квадрат в 12 тактов по схеме AAB: фраза, её повтор над IV, ответ и оборот."""
    B = bar0 * 4
    budget = 5 + 3 * intensity
    l1 = pick_licks(rng, budget)
    st = float(rng.choice([0, 2 * T3, 1]))
    blues_line(part, l1, B + st, ref, rng, vel=vel, minor=minor, bend_style=style, **kw)
    l2 = l1 if rng.random() < 0.65 else pick_licks(rng, budget)
    blues_line(part, l2, B + 16 + st, ref, rng, vel=vel, minor=minor, bend_style=style, **kw)
    l3 = pick_licks(rng, min(budget, 7))
    blues_line(part, l3, B + 32 + float(rng.choice([0, 2 * T3])), ref, rng, vel=vel, minor=minor,
               bend_style=style, **kw)
    if not last:
        blues_line(part, [TURNAROUND], B + 40, ref, rng, vel=vel * 0.95, minor=minor, bend_style=style, **kw)
    else:
        run = [(0, T3, 12, 0, 0), (T3, T3, 10, 0, 0), (2 * T3, T3, 7, 0, 0), (1, T3, 10, 0, 0),
               (1 + T3, T3, 7, 0, 0), (1 + 2 * T3, T3, 5, 0, 0), (2, T3, 7, 0, 0), (2 + T3, T3, 6, 0, 0),
               (2 + 2 * T3, T3, 5, 0, 0), (3, 1, 3, 1, 0)]
        blues_line(part, [run], B + 40, ref, rng, vel=vel, minor=minor, bend_style=style, **kw)


def blues_ending(beat, key, parts, drums=None, ninth=True):
    """Финальный аккорд: подъезд на полтона сверху и I9."""
    for part, lo, hi, v in parts:
        top = voice([(key + x) % 12 for x in ((4, 7, 10, 14) if ninth else (3, 7, 10, 14))], lo, hi)
        slide = [p + 1 for p in top]
        part.chord(beat - 1 / 3, 1 / 3, slide, v * 0.8, strum=0.01)
        part.chord(beat, 6, top, v, strum=0.02)
    if drums is not None:
        for k in range(9):
            drums.hit(beat - 3 + k / 3, 'snare' if k < 6 else 'tom_lo', 0.35 + 0.05 * k)
        drums.hit(beat, 'crash', 0.85)
        drums.hit(beat, 'kick', 0.9)


def crossroads_at_dawn():
    s = Song(56, seed=801, t60=2.2, loud=-16)
    rng = s.rng
    key = pc_of('E')
    form = blues_changes(key, quick=True, ext='9')
    ch = Changes(form[8:] + form + form + ['E9'])
    total = len(ch.bars)
    drums = s.part('drums', level=-21, send=0.15, jitter=0.004)
    bass = s.part('ebass', level=-19, send=0.08)
    organ = s.part('organ', level=-27, send=0.35, post=[lambda b, r: fx_leslie(b, r, rate=0.9, depth=0.2)],
                   drawbars=(8, 8, 8, 0, 0, 0, 0, 0, 0))
    gtr = s.part('pluck', pan=0.25, level=-14, send=0.35, t60=3.5, bright=0.9, drive=4.0, cab=4500, pick=0.1,
                 post=[fx_slapback(0.12, 0.2)])
    amb = s.part('drums', level=-42, send=0.0)
    shuffle_drums(drums, 0, total - 1, rng, style='slow', vel=0.75)
    boogie_bass(bass, ch, 0, total - 1, rng, lo=N('E1'), hi=N('E3'), pattern='walk4')
    pads(organ, ch, 0, total - 1, rng, lo=N('G3'), hi=N('E5'), vel=0.5)
    ref = N('E4')
    blues_line(gtr, [TURNAROUND], 8, ref, rng, vel=0.85)
    blues_chorus(gtr, 4, rng, ref, intensity=0)
    blues_chorus(gtr, 16, rng, ref, intensity=2, last=True)
    end = (total - 1) * 4
    blues_ending(end, key, [(organ, N('G3'), N('E5'), 0.55)], drums)
    gtr.note(end, 5, ref + 12, 0.8, vib=0.35)
    bass.note(end, 5, N('E2'), 0.9)
    amb.raw(0.0, crackle(s.time(end) + 6, rng))
    return s


def whiskey_rain_shuffle():
    s = Song(108, seed=802, t60=1.5, loud=-15)
    rng = s.rng
    key = pc_of('A')
    form = blues_changes(key, quick=True)
    ch = Changes(bars('A7 | A7') + form * 4 + ['A9'])
    total = len(ch.bars)
    drums = s.part('drums', level=-19, send=0.1, jitter=0.003)
    bass = s.part('ebass', level=-18, send=0.05)
    rgt = s.part('pluck', pan=-0.45, level=-22, send=0.15, t60=0.35, bright=0.7, drive=1.8, cab=4000, damp=0.03)
    pno = s.part('piano', pan=0.35, level=-26, send=0.2)
    gtr = s.part('pluck', pan=0.2, level=-14, send=0.25, t60=3.0, bright=0.95, drive=6.0, cab=5000, pick=0.1,
                 post=[fx_slapback(0.1, 0.18)])
    for b in range(8):
        drums.hit(b, 'hat', 0.6)
        drums.hit(b + 2 * T3, 'hat', 0.4)
        if b in (1, 3, 5, 7):
            drums.hit(b, 'snare', 0.6 + 0.05 * b)
    shuffle_drums(drums, 2, total - 1, rng, style='shuffle', vel=0.85)
    boogie_bass(bass, ch, 2, total - 1, rng, lo=N('E1'), hi=N('E3'), pattern='walk8')
    guitar_boogie(rgt, ch, 0, total - 1, rng, lo=N('E2'))
    blues_comp_stabs(pno, ch, 2, total - 1, rng, lo=N('G4'), hi=N('E5'))
    blues_chorus(gtr, 2, rng, N('A3'), intensity=0)
    blues_chorus(gtr, 14, rng, N('A4'), intensity=1)
    blues_chorus(gtr, 26, rng, N('A4'), intensity=2)
    blues_chorus(gtr, 38, rng, N('A3'), intensity=1, last=True)
    end = (total - 1) * 4
    blues_ending(end, key, [(pno, N('G4'), N('E5'), 0.6), (rgt, N('E3'), N('C#4') + 3, 0.7)], drums)
    gtr.note(end, 4, N('A4'), 0.85, vib=0.35)
    bass.note(end, 4, N('A1'), 0.9)
    return s


def tremolo(part, beat, beats, lo_notes, hi_notes, vel, rng):
    k = int(beats * 3)
    for i in range(k):
        notes = lo_notes if i % 2 == 0 else hi_notes
        part.chord(beat + i * T3, T3 * 0.9, notes, vel * rng.uniform(0.85, 1.0))


def blue_monday_boogie():
    s = Song(140, seed=803, t60=1.6, loud=-15)
    rng = s.rng
    key = pc_of('C')
    form = blues_changes(key, quick=False)
    ch = Changes(bars('C7 | C7 | C7 | C7') + form * 5 + ['C9'])
    total = len(ch.bars)
    lh = s.part('piano', pan=-0.2, level=-17, send=0.2, bright=1.1)
    rh = s.part('piano', pan=0.2, level=-16, send=0.25, bright=1.2)
    drums = s.part('drums', level=-24, send=0.1, jitter=0.003)
    ub = s.part('upright', level=-24, send=0.05)
    for bar in range(total - 1):
        c = ch.at(bar * 4)
        r = near_pc(c.root, N('C2'), N('G1'), N('F#2'))
        for i, st in enumerate((0, 4, 7, 9, 10, 9, 7, 4)):
            beat = bar * 4 + i // 2 + (i % 2) * 2 * T3
            lh.note(beat, 0.55 if i % 2 == 0 else 0.3, r + st, 0.8 if i % 2 == 0 else 0.62)
            if i % 2 == 0:
                lh.note(beat, 0.55, r + st + 12, 0.45)
    shuffle_drums(drums, 4, total - 1, rng, style='shuffle', vel=0.55)
    boogie_bass(ub, ch, 4, total - 1, rng, lo=N('C2'), hi=N('C3'), pattern='root5', vel=0.6)
    ref = N('C5')
    for k in range(5):
        bar0 = 4 + k * 12
        if k in (1, 3):
            for line in range(3):
                b = (bar0 + line * 4) * 4
                c = ch.at(b)
                third = (c.root + 4) % 12
                lo_n = voice([c.root, third], N('C5'), N('C6'))
                hi_n = [near_pc((c.root + 7) % 12, lo_n[-1] + 3, lo_n[-1] + 1, lo_n[-1] + 9)]
                tremolo(rh, b, 3, lo_n, hi_n, 0.6, rng)
                blues_line(rh, [LICKS[int(rng.integers(len(LICKS)))]], b + 3 * 4 - 4 + 1, ref, rng, vel=0.8,
                           bend_style='none')
        else:
            blues_chorus(rh, bar0, rng, ref, intensity=k // 2, last=(k == 4), vel=0.85, style='none')
            for line in range(3):
                b = (bar0 + line * 4 + 2) * 4
                c = ch.at(b)
                v = voice([(c.root + x) % 12 for x in (4, 9, 10)], N('E4'), N('Bb5'))
                for t in (0, 2 * T3 + 1, 3):
                    rh.chord(b + t, 0.3, v, 0.55, strum=0.008)
    end = (total - 1) * 4
    blues_ending(end, key, [(rh, N('E4'), N('D5') + 3, 0.7)], drums)
    lh.chord(end, 5, [N('C2'), N('C3')], 0.85)
    ub.note(end, 4, N('C2'), 0.8)
    return s


def muddy_road_home():
    s = Song(84, seed=804, t60=1.4, loud=-15)
    rng = s.rng
    key = pc_of('G')
    form = blues_changes(key, quick=False)
    ch = Changes(bars('G7 | G7') + form * 3 + ['G7'])
    total = len(ch.bars)
    perc = s.part('drums', level=-20, send=0.15, jitter=0.006)
    thumb = s.part('pluck', pan=-0.25, level=-20, send=0.2, t60=0.6, bright=0.45, pick=0.2, damp=0.04)
    slide = s.part('pluck', pan=0.25, level=-14, send=0.3, t60=3.0, bright=0.75, drive=1.4, pick=0.12,
                   lowpass=6000)
    for bar in range(total - 1):
        for b in range(4):
            perc.hit(bar * 4 + b, 'stomp', 0.85 if b % 2 == 0 else 0.7)
            if bar >= 14 and b in (1, 3):
                perc.hit(bar * 4 + b, 'clap', 0.6 * rng.uniform(0.85, 1.05))
    boogie_bass(thumb, ch, 0, total - 1, rng, lo=N('D2'), hi=N('D3') + 6, pattern='thumb', vel=0.8)
    for bar in range(total - 1):
        c = ch.at(bar * 4)
        r = near_pc(c.root, N('G3'), N('D3'), N('C#4'))
        for b in (1 + 2 * T3, 3 + 2 * T3):
            thumb.chord(bar * 4 + b, 0.25, [r + 4, r + 7, r + 10], 0.35, strum=0.012)
    ref = N('G4')
    blues_line(slide, [LICKS[7]], 2, ref, rng, bend_style='slide')
    for k in range(3):
        blues_chorus(slide, 2 + 12 * k, rng, ref if k != 1 else ref - 12, intensity=k, style='slide',
                     last=(k == 2))
    end = (total - 1) * 4
    slide.note(end, 5, ref - 2, 0.85, bends=[(0.0, 0.25, 2)], vib=0.25)
    thumb.chord(end, 4, [N('G2'), N('D3'), N('G3'), N('B3'), N('F4')], 0.7, strum=0.04)
    perc.hit(end, 'stomp', 0.9)
    return s


def midnight_train_blues():
    s = Song(132, seed=805, t60=1.4, loud=-15)
    rng = s.rng
    key = pc_of('A')
    form = blues_changes(key, quick=True)
    ch = Changes(bars('A7 | A7') + form * 5 + ['A7'])
    total = len(ch.bars)
    drums = s.part('drums', level=-19, send=0.08, jitter=0.003)
    bass = s.part('ebass', level=-18, send=0.05)
    rgt = s.part('pluck', pan=-0.4, level=-22, send=0.12, t60=0.35, bright=0.65, drive=1.5, cab=4000, damp=0.03)
    harp = s.part('harmonica', pan=0.15, level=-13, send=0.25, post=[fx_slapback(0.09, 0.15)])
    for bar in range(total - 1):
        ramp = min(1.0, 0.35 + bar * 0.35) if bar < 2 else 1.0
        B = bar * 4
        for beat in range(4):
            for k, v in ((0, 0.5), (2 * T3, 0.32)):
                acc = 0.3 if beat % 2 and k == 0 else 0.0
                drums.hit(B + beat + k, 'snare', (v + acc) * ramp * rng.uniform(0.9, 1.05))
            if beat in (0, 2):
                drums.hit(B + beat, 'kick', 0.8 * ramp)
        if bar % 12 == 1 and bar > 2:
            drums.hit(B + 4, 'crash', 0.6)
    boogie_bass(bass, ch, 2, total - 1, rng, lo=N('E1'), hi=N('E3'), pattern='root5')
    guitar_boogie(rgt, ch, 2, total - 1, rng, lo=N('E2'))
    harp.chord(0, 3.5, [N('A4'), N('C#5')], 0.7, bends=[(0.05, 0.6, 1)])
    harp.chord(4, 3.5, [N('A4'), N('C#5')], 0.75, bends=[(0.05, 0.6, 1)])
    ref = N('A4')
    for k in range(5):
        blues_chorus(harp, 2 + 12 * k, rng, ref, intensity=min(2, k), last=(k == 4))
    end = (total - 1) * 4
    blues_ending(end, key, [(rgt, N('E3'), N('C#4') + 3, 0.7)], drums)
    harp.chord(end, 4, [N('A4'), N('C#5'), N('E5')], 0.8, bends=[(0.0, 0.3, 1)])
    bass.note(end, 4, N('A1'), 0.9)
    return s


def minor_mood_blues():
    s = Song(80, seed=806, t60=1.9, loud=-16)
    rng = s.rng
    key = pc_of('C')
    form = blues_changes(key, minor=True)
    ch = Changes(form[8:] + form * 3 + ['Cm9'])
    total = len(ch.bars)
    drums = s.part('drums', level=-22, send=0.12, jitter=0.004)
    bass = s.part('upright', level=-18, send=0.1)
    ep = s.part('epiano', pan=-0.3, level=-25, send=0.3, post=[fx_autopan])
    organ = s.part('organ', pan=0.1, level=-15, send=0.3, drawbars=(8, 8, 8, 0, 0, 0, 0, 0, 0), perc=0.5,
                   post=[lambda b, r: fx_leslie(b, r, rate=6.3, depth=0.25)])
    shuffle_drums(drums, 0, total - 1, rng, style='ride', vel=0.7)
    boogie_bass(bass, ch, 0, total - 1, rng, lo=N('C2') - 2, hi=N('C3') + 3, pattern='walk4', minor=True)
    prev = None
    for bar in range(total - 1):
        for beat in range(4):
            c = ch.at(bar * 4 + beat)
            v = voice(c.rootless(), N('G3'), N('Eb5'), prev)
            prev = v
            for k in (0, 2 * T3):
                if rng.random() < (0.8 if k == 0 else 0.35):
                    ep.chord(bar * 4 + beat + k, 0.5, v, 0.45 * rng.uniform(0.8, 1.05), strum=0.01)
    ref = N('C5')
    scale_fn = lambda c: {(key + x) % 12 for x in (0, 2, 3, 5, 6, 7, 10)}
    blues_chorus(organ, 4, rng, ref, intensity=0, minor=True, style='none')
    improvise(organ, ch, 16, 28, rng, N('G4'), N('Eb6'), density=0.5, vel=0.85, scale_fn=scale_fn, triplets=0.25)
    blues_chorus(organ, 28, rng, ref, intensity=1, minor=True, style='none', last=True)
    end = (total - 1) * 4
    blues_ending(end, key, [(ep, N('G3'), N('Eb5'), 0.5)], drums, ninth=False)
    organ.chord(end, 5, [N('Eb4'), N('G4'), N('Bb4'), N('D5')], 0.85)
    bass.note(end, 5, N('C2'), 0.85)
    return s


def last_call_at_joes():
    s = Song(60, seed=807, t60=2.4, loud=-16)
    rng = s.rng
    key = pc_of('Bb')
    form = blues_changes(key, quick=True, ext='9')
    ch = Changes(form[10:] + form * 2 + ['Bb9'])
    total = len(ch.bars)
    s.tempo([(0, 60), ((total - 2) * 4, 60), ((total - 1) * 4, 48)])
    drums = s.part('drums', level=-24, send=0.15, jitter=0.004)
    bass = s.part('upright', level=-19, send=0.1)
    ep = s.part('epiano', pan=-0.25, level=-22, send=0.3, post=[fx_autopan])
    sax = s.part('sax', pan=0.15, level=-14, send=0.35, jitter=0.01)
    amb = s.part('drums', level=-44, send=0.0)
    shuffle_drums(drums, 0, total - 1, rng, style='slow', vel=0.6)
    boogie_bass(bass, ch, 0, total - 1, rng, lo=N('Bb1') - 2, hi=N('Bb2') + 5, pattern='walk4')
    prev = None
    for bar in range(total - 1):
        for beat in range(4):
            c = ch.at(bar * 4 + beat)
            v = voice(c.rootless(), N('F3'), N('Eb5'), prev)
            prev = v
            for k in range(3):
                ep.chord(bar * 4 + beat + k * T3, T3 * 0.9, v, (0.5 if k == 0 else 0.35) * rng.uniform(0.85, 1.05))
    ref = N('Bb4')
    blues_line(ep, [TURNAROUND], 0, N('Bb4'), rng, vel=0.6, bend_style='none')
    blues_chorus(sax, 2, rng, ref, intensity=0, style='scoop', vel=0.8)
    blues_chorus(sax, 14, rng, ref, intensity=2, style='scoop', last=True, vel=0.9)
    end = (total - 1) * 4
    blues_ending(end, key, [(ep, N('F3'), N('Eb5'), 0.55)], None)
    drums.hit(end, 'ride', 0.6)
    drums.hit(end, 'kick', 0.6)
    sax.note(end, 5, N('D5'), 0.75)
    bass.note(end, 5, N('Bb1'), 0.85)
    amb.raw(0.0, crackle(s.time(end) + 6, rng, density=3))
    return s
