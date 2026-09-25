"""Музыкальная теория и генераторы партий: аккорды, голосоведение,
walking bass, комп, мелодии по мотивам, импровизации, блюзовые фразы.
"""
from bisect import bisect_right

import numpy as np

PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

MAJOR = [0, 2, 4, 5, 7, 9, 11]
DORIAN = [0, 2, 3, 5, 7, 9, 10]
MIXO = [0, 2, 4, 5, 7, 9, 10]
AEOLIAN = [0, 2, 3, 5, 7, 8, 10]
HARM_MINOR = [0, 2, 3, 5, 7, 8, 11]
MEL_MINOR = [0, 2, 3, 5, 7, 9, 11]
LOCRIAN = [0, 1, 3, 5, 6, 8, 10]
PHRYG_DOM = [0, 1, 4, 5, 7, 8, 10]
DIM = [0, 2, 3, 5, 6, 8, 9, 11]
WHOLE = [0, 2, 4, 6, 8, 10]
BLUES = [0, 3, 5, 6, 7, 10]
MINOR_PENT = [0, 3, 5, 7, 10]
MAJOR_PENT = [0, 2, 4, 7, 9]

QUAL = {
    '': [0, 4, 7], 'm': [0, 3, 7], 'dim': [0, 3, 6], 'aug': [0, 4, 8],
    'sus4': [0, 5, 7], '7sus4': [0, 5, 7, 10],
    '7': [0, 4, 7, 10], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10], 'm7b5': [0, 3, 6, 10],
    'dim7': [0, 3, 6, 9], '6': [0, 4, 7, 9], 'm6': [0, 3, 7, 9], 'mmaj7': [0, 3, 7, 11],
    '9': [0, 4, 7, 10, 14], 'maj9': [0, 4, 7, 11, 14], 'm9': [0, 3, 7, 10, 14],
    '7b9': [0, 4, 7, 10, 13], '7#9': [0, 4, 7, 10, 15], '13': [0, 4, 7, 10, 14, 21],
    '69': [0, 4, 7, 9, 14], 'add9': [0, 4, 7, 14], 'm11': [0, 3, 7, 10, 14, 17],
}
CHORD_SCALE = {
    '': MAJOR, 'maj7': MAJOR, '6': MAJOR, '69': MAJOR, 'maj9': MAJOR, 'add9': MAJOR,
    'm': DORIAN, 'm7': DORIAN, 'm9': DORIAN, 'm11': DORIAN, 'm6': DORIAN,
    '7': MIXO, '9': MIXO, '13': MIXO, '7sus4': MIXO, 'sus4': MIXO,
    '7b9': PHRYG_DOM, '7#9': [0, 1, 3, 4, 7, 8, 10], 'm7b5': LOCRIAN,
    'dim': DIM, 'dim7': DIM, 'mmaj7': MEL_MINOR, 'aug': WHOLE,
}
# «Безкорневые» джазовые аккорды (интервалы от корня)
ROOTLESS = {
    'maj7': [4, 7, 11, 14], '6': [4, 7, 9, 14], '69': [4, 7, 9, 14], 'maj9': [4, 7, 11, 14],
    '': [0, 4, 7, 14], 'add9': [0, 4, 7, 14],
    'm7': [3, 7, 10, 14], 'm9': [3, 7, 10, 14], 'm11': [3, 5, 10, 14], 'm6': [3, 7, 9, 14],
    'm': [0, 3, 7, 14], 'mmaj7': [3, 7, 11, 14],
    '7': [4, 9, 10, 14], '9': [4, 9, 10, 14], '13': [4, 9, 10, 14],
    '7b9': [4, 8, 10, 13], '7#9': [4, 8, 10, 15], '7sus4': [5, 7, 10, 14], 'sus4': [0, 5, 7, 14],
    'm7b5': [0, 3, 6, 10], 'dim7': [0, 3, 6, 9], 'dim': [0, 3, 6, 9], 'aug': [0, 4, 8, 10],
}


def pc_of(name):
    v = PC[name[0]]
    for ch in name[1:]:
        v += 1 if ch == '#' else -1 if ch == 'b' else 0
    return v % 12


def N(s):
    """'C4' -> 60, 'Bb2' -> 46."""
    i = 1
    while i < len(s) and s[i] in '#b':
        i += 1
    return 12 * (int(s[i:]) + 1) + pc_of(s[:i])


class Chord:
    def __init__(self, sym):
        self.sym = sym
        s, _, bass = sym.partition('/')
        i = 2 if len(s) > 1 and s[1] in '#b' else 1
        self.root = pc_of(s[:i])
        self.qual = s[i:]
        self.iv = QUAL[self.qual]
        self.bass = pc_of(bass) if bass else self.root
        self.pcs = [(self.root + x) % 12 for x in self.iv]

    def tones(self, n=4):
        return {(self.root + x) % 12 for x in self.iv[:n]}

    def scale(self):
        return {(self.root + x) % 12 for x in CHORD_SCALE[self.qual]}

    def rootless(self):
        return [(self.root + x) % 12 for x in ROOTLESS[self.qual]]

    def __repr__(self):
        return self.sym


def bars(s):
    return [b.strip() for b in s.split('|') if b.strip()]


def chord_name(pc, qual=''):
    return NAMES[pc % 12] + qual


class Changes:
    """Сетка аккордов: список тактов вида 'Dm7 G7' (аккорды делят такт поровну)."""

    def __init__(self, bar_list, bpb=4):
        self.bpb = bpb
        self.bars = list(bar_list)
        self.ev = []
        for i, bar in enumerate(self.bars):
            syms = bar.split()
            L = bpb / len(syms)
            for j, s in enumerate(syms):
                self.ev.append((i * bpb + j * L, L, Chord(s)))
        self.starts = [e[0] for e in self.ev]
        self.total = len(self.bars) * bpb

    def idx(self, beat):
        return min(len(self.ev) - 1, max(0, bisect_right(self.starts, beat + 1e-6) - 1))

    def at(self, beat):
        return self.ev[self.idx(beat)][2]

    def start(self, beat):
        return self.ev[self.idx(beat)][0]

    def is_change(self, beat):
        return beat < self.total and abs(self.start(beat) - beat) < 1e-6

    def __add__(self, other):
        return Changes(self.bars + other.bars, self.bpb)


# --------------------------------------------------------------------------
# Высоты
# --------------------------------------------------------------------------
def pitches_in(pcs, lo, hi):
    return [p for p in range(lo, hi + 1) if p % 12 in pcs]


def nearest(cands, ref, direction=0):
    if not cands:
        return ref
    if direction:
        side = [c for c in cands if (c - ref) * direction >= 0]
        if side:
            cands = side
    return min(cands, key=lambda c: (abs(c - ref), c))


def near_pc(pc, ref, lo, hi):
    return nearest([p for p in range(lo, hi + 1) if p % 12 == pc % 12], ref)


def step_in(scale, p, steps):
    if not scale:
        return p
    i = int(np.argmin([abs(s - p) for s in scale]))
    if scale[i] != p and steps:
        if (scale[i] - p) * steps > 0:
            steps -= int(np.sign(steps))
    return scale[int(np.clip(i + steps, 0, len(scale) - 1))]


def voice(pcs, lo, hi, prev=None):
    """Плотное расположение аккорда в диапазоне с минимальным движением голосов."""
    best = None
    for base in range(lo, lo + 12):
        v = sorted(base + ((pc - base) % 12) for pc in pcs)
        if v[-1] > hi:
            continue
        if prev:
            cost = sum(min(abs(x - y) for y in prev) for x in v) + abs(np.mean(v) - np.mean(prev)) * 0.5
        else:
            cost = abs(np.mean(v) - (lo + hi) / 2)
        if best is None or cost < best[0]:
            best = (cost, v)
    if best is None:
        return sorted(lo + ((pc - lo) % 12) for pc in pcs)
    return best[1]


def drop2(v):
    if len(v) < 4:
        return v
    v = sorted(v)
    return sorted([v[-2] - 12] + v[:-2] + v[-1:])


# --------------------------------------------------------------------------
# Ритм-секция: джаз
# --------------------------------------------------------------------------
def walking_bass(part, ch, b0, b1, rng, lo=31, hi=50, vel=0.8, offset=0):
    """Шагающий бас четвертями: тоника на смене аккорда, хроматический подход к следующему."""
    prev = None
    direction = 1
    for beat in range(b0 * ch.bpb, b1 * ch.bpb):
        c = ch.at(beat)
        nb = beat + 1
        if prev is None or ch.is_change(beat):
            ref = prev if prev is not None else (lo + hi) // 2 - 3
            p = near_pc(c.bass, ref, lo, hi)
            if prev is not None and p == prev and rng.random() < 0.5:
                p = p + 12 if p + 12 <= hi else p - 12 if p - 12 >= lo else p
        elif nb < ch.total and ch.is_change(nb):
            target = near_pc(ch.at(nb).bass, prev, lo, hi)
            opts = [target - 1, target + 1] if rng.random() < 0.7 else [target + 7, target - 5, target + 2, target - 2]
            opts = [o for o in opts if lo <= o <= hi and o != prev] or [target - 1]
            p = nearest(opts, prev)
        else:
            if prev >= hi - 3:
                direction = -1
            elif prev <= lo + 3:
                direction = 1
            elif rng.random() < 0.3:
                direction = -direction
            tones = pitches_in(c.tones(), lo, hi)
            scale = pitches_in(c.scale(), lo, hi)
            cands = [t for t in tones if 0 < (t - prev) * direction <= 5] * 2
            cands += [s for s in scale if 0 < (s - prev) * direction <= 2]
            p = cands[rng.integers(len(cands))] if cands else step_in(scale, prev, direction)
        part.note(offset + beat, 0.9, p, vel * rng.uniform(0.85, 1.05))
        prev = p


COMP_PATTERNS = [
    ([(0, 1.0), (1.5, 0.5)], 3),
    ([(1.5, 1.0)], 2),
    ([(0, 0.5), (2.5, 0.8)], 2),
    ([(1, 0.5), (3, 0.5)], 2),
    ([(0.5, 0.4), (2, 1.0)], 1),
    ([(2.5, 1.2)], 2),
    ([(0, 2.0)], 1),
    ([(3.5, 0.5)], 1),
    ([], 1),
]


def jazz_comp(part, ch, b0, b1, rng, lo=50, hi=74, vel=0.55, offset=0, density=1.0):
    pats = [p for p, _ in COMP_PATTERNS]
    w = np.array([wt for _, wt in COMP_PATTERNS], dtype=float)
    w /= w.sum()
    prev = None
    for bar in range(b0, b1):
        pat = pats[rng.choice(len(pats), p=w)]
        if rng.random() > density:
            pat = pat[:1]
        for b, d in pat:
            beat = bar * ch.bpb + b
            c = ch.at(beat + (0.5 if b % 1 else 0))  # «подталкивание» следующего аккорда
            v = voice(c.rootless(), lo, hi, prev)
            prev = v
            part.chord(offset + beat, d, v, vel * rng.uniform(0.8, 1.1), strum=0.006)


def ballad_comp(part, ch, b0, b1, rng, lo=48, hi=72, vel=0.45, offset=0):
    prev = None
    for bar in range(b0, b1):
        for b in np.arange(0, ch.bpb, 2):
            beat = bar * ch.bpb + b
            if not ch.is_change(beat) and b != 0:
                continue
            c = ch.at(beat)
            L = ch.bpb - b if not ch.is_change(beat + 2) or b else 2
            v = voice(c.rootless(), lo, hi, prev)
            prev = v
            part.chord(offset + beat, L * 0.97, v, vel * rng.uniform(0.85, 1.05), strum=0.025)


def swing_drums(part, b0, b1, rng, style='ride', vel=0.8, fills=8, offset=0, sweep_part=None):
    for bar in range(b0, b1):
        B = offset + bar * 4
        last = (bar - b0) % fills == fills - 1
        if style == 'ride':
            for b, v in ((0, 0.7), (1, 0.85), (1.5, 0.5), (2, 0.7), (3, 0.85), (3.5, 0.5)):
                part.hit(B + b, 'ride', vel * v * rng.uniform(0.9, 1.05))
            for b in (1, 3):
                part.hit(B + b, 'pedal', vel * 0.7)
            for b in range(4):
                part.hit(B + b, 'kick', vel * 0.22)
            for b in (0.5, 1.5, 2.5, 3.5):
                if rng.random() < 0.13:
                    part.hit(B + b, 'snare', vel * rng.uniform(0.18, 0.35))
            if last:
                for b in (2.5, 3, 3.5):
                    part.hit(B + b, 'snare', vel * rng.uniform(0.45, 0.7))
                part.hit(B + 3.5, 'kick', vel * 0.5)
        else:  # щётки
            for b, v in ((0, 0.5), (1, 0.8), (1.5, 0.35), (2, 0.5), (3, 0.8), (3.5, 0.35)):
                part.hit(B + b, 'brush', vel * v * rng.uniform(0.85, 1.05))
            for b in (1, 3):
                part.hit(B + b, 'pedal', vel * 0.4)
            part.hit(B, 'kick', vel * 0.25)
            part.hit(B + 2, 'kick', vel * 0.18)
            if sweep_part is not None:
                sweep_part.note(B, 2, 0, vel)
                sweep_part.note(B + 2, 2, 0, vel)
            if last:
                part.hit(B + 3.5, 'brush', vel * 0.7)


# --------------------------------------------------------------------------
# Мелодии по мотивам
# --------------------------------------------------------------------------
def make_contour(n, rng, leap=0.2, rep=0.08):
    c = [0]
    d = 1 if rng.random() < 0.5 else -1
    leapt = False
    for _ in range(1, n):
        if leapt:
            d = -d
            leapt = False
        elif rng.random() < 0.28:
            d = -d
        r = rng.random()
        if r < rep:
            s = 0
        elif r < rep + leap:
            s = d * int(rng.choice([2, 3, 4]))
            leapt = abs(s) >= 3
        else:
            s = d * int(rng.choice([1, 1, 1, 2]))
        c.append(s)
    return c


def realize(ch, b0, rhythm, contour, start, lo, hi, scale_fn=None, strong_fn=None, tones_n=4):
    """Раскладывает ритм+контур по аккордам: сильные доли — на аккордовые звуки."""
    scale_fn = scale_fn or (lambda c: c.scale())
    strong_fn = strong_fn or (lambda b, d: (b % 1 == 0 and d >= 1) or d >= 1.5)
    out = []
    prev = start
    for i, (b, d) in enumerate(rhythm):
        beat = b0 + b
        c = ch.at(beat)
        sc = pitches_in(scale_fn(c), lo, hi)
        ct = pitches_in(c.tones(tones_n), lo, hi)
        if i == 0:
            p = nearest(ct, prev)
        else:
            p = step_in(sc, prev, contour[i])
            if strong_fn(b, d):
                p = nearest(ct, p, int(np.sign(contour[i])))
        out.append([beat, d, p])
        prev = p
    return out


def end_on(notes, pcs, lo, hi, scale):
    """Последняя нота фразы — на заданную ступень, предпоследняя — плавно к ней."""
    if not notes:
        return notes
    last = notes[-1]
    last[2] = nearest([p for p in range(lo, hi + 1) if p % 12 in pcs], last[2])
    if len(notes) > 1 and abs(notes[-2][2] - last[2]) > 4:
        sc = [p for p in scale if p != last[2]]
        notes[-2][2] = nearest(sc, last[2] + (1 if notes[-2][2] > last[2] else -1))
    return notes


class Tune:
    """Сочиняет секции мелодии из мотивов: M, M' (секвенция), M, каденция."""

    def __init__(self, ch, rng, rhythms, cadences, lo, hi, tonic, cell_bars=2,
                 scale_fn=None, strong_fn=None, key_scale=None):
        self.ch, self.rng = ch, rng
        self.rhythms, self.cadences = rhythms, cadences
        self.lo, self.hi, self.tonic = lo, hi, tonic
        self.cell = cell_bars
        self.scale_fn = scale_fn
        self.strong_fn = strong_fn
        self.key_scale = key_scale or MAJOR

    def _cell(self, cad=False):
        lib = self.cadences if cad else self.rhythms
        r = lib[self.rng.integers(len(lib))]
        return r, make_contour(len(r), self.rng)

    def section(self, bar0, nbars, plan=None, start=None, ending='tonic'):
        """plan — по символу на клетку: заглавная буква = именованный мотив (повтор
        играется с той же высоты), строчная = его секвенция, C/H = каденция на тонику /
        половинная (на II, V или VII ступень)."""
        bpb = self.ch.bpb
        ncell = nbars // self.cell
        plan = plan or {4: 'AaAC', 8: 'AaBHAaDC'}.get(ncell, 'A' * (ncell - 1) + 'C')
        cells, starts = {}, {}
        cur = start if start is not None else (self.lo + self.hi) // 2
        notes = []
        key_pcs = {(self.tonic + x) % 12 for x in self.key_scale}
        key_pitches = pitches_in(key_pcs, self.lo, self.hi)
        tonic = {self.tonic}
        half = {(self.tonic + x) % 12 for x in (2, 7, 11)} & key_pcs or {(self.tonic + 7) % 12}
        for i, kind in enumerate(plan):
            b0 = (bar0 + i * self.cell) * bpb
            K = kind.upper()
            if kind in 'CH':
                r, c = self._cell(cad=True)
                s = cur
            else:
                if K not in cells:
                    cells[K] = self._cell()
                r, c = cells[K]
                if kind.isupper():
                    s = starts.get(K, cur)
                else:
                    c = list(c)
                    if len(c) > 2 and self.rng.random() < 0.5:
                        c[-1] = -c[-1]
                    s = starts.get(K, cur) + int(self.rng.choice([-3, 2, 3, 4]))
            ph = realize(self.ch, b0, r, c, s, self.lo, self.hi, self.scale_fn, self.strong_fn)
            if kind.isupper() and kind not in 'CH' and K not in starts:
                starts[K] = ph[0][2]
            last = i == len(plan) - 1
            if kind == 'C' or (last and ending == 'tonic'):
                ph = end_on(ph, tonic, self.lo, self.hi, key_pitches)
            elif kind == 'H' or (last and ending == 'half'):
                ph = end_on(ph, half, self.lo, self.hi, key_pitches)
            notes += ph
            cur = ph[-1][2] if ph else cur
        return notes


def key_scale_fn(tonic, minor=False):
    """Лад тональности; хроматические звуки аккорда вытесняют соседние ступени."""
    base = {(tonic + x) % 12 for x in (AEOLIAN if minor else MAJOR)}

    def fn(c):
        pcs = set(base)
        for p in c.pcs:
            if p not in pcs:
                for q in ((p - 1) % 12, (p + 1) % 12):
                    if q in pcs and q not in c.pcs:
                        pcs.discard(q)
                pcs.add(p)
        return pcs
    return fn


def play_notes(part, notes, offset=0, vel=0.8, rng=None, legato=0.95, accent_offbeats=0.0, **kw):
    for b, d, p in notes:
        v = vel
        if rng is not None:
            v *= rng.uniform(0.88, 1.06)
        if accent_offbeats and b % 1:
            v *= 1 + accent_offbeats
        part.note(offset + b, d * legato, p, v, **kw)


def improvise(part, ch, b0, b1, rng, lo, hi, density=0.55, vel=0.8, scale_fn=None,
              offset=0, approach=0.2, legato=0.92, triplets=0.0, **kw):
    """Импровизация: фразы-«волны» по ладу аккорда, аккордовые звуки на сильных долях."""
    scale_fn = scale_fn or (lambda c: c.scale())
    beat = b0 * ch.bpb
    end = b1 * ch.bpb
    p = (lo + hi) // 2
    d_ = 1
    while beat < end - 1:
        L = int(rng.choice([3, 4, 5, 6, 7, 8]))
        t = beat + (0.5 if rng.random() < 0.35 else 0.0)
        pend = min(t + L, end - 0.5)
        while t < pend:
            if triplets and t % 1 == 0 and rng.random() < triplets and t + 1 <= pend:
                c = ch.at(t)
                sc = pitches_in(scale_fn(c), lo, hi)
                for k in range(3):
                    p = step_in(sc, p, d_)
                    part.note(offset + t + k / 3, 0.3, p, vel * rng.uniform(0.75, 0.95), **kw)
                t += 1
                continue
            d = 0.5 if rng.random() < density else (1.0 if rng.random() < 0.8 else 1.5)
            if t % 1 and d > 0.5:
                d = 0.5 if rng.random() < 0.6 else d
            c = ch.at(t)
            sc = pitches_in(scale_fn(c), lo, hi)
            ct = pitches_in(c.tones(), lo, hi)
            if rng.random() < 0.2:
                d_ = -d_
            if p >= hi - 3:
                d_ = -1
            elif p <= lo + 3:
                d_ = 1
            p = step_in(sc, p, d_ * (1 if rng.random() < 0.75 else 2))
            if t % 1 == 0 and rng.random() < 0.7:
                p = nearest(ct, p, d_)
            nxt = t + d
            if d == 0.5 and nxt % 1 == 0 and rng.random() < approach and nxt < pend:
                tgt = nearest(pitches_in(ch.at(nxt).tones(), lo, hi), p + d_ * 2)
                p = tgt - 1 if rng.random() < 0.7 else tgt + 1
            v = vel * rng.uniform(0.8, 1.0) * (1.08 if t % 1 else 1.0)
            last = nxt >= pend
            dd = d * legato if not last else d + rng.choice([0.5, 1.0])
            if last:
                p = nearest(ct, p)
            part.note(offset + t, dd, p, v, **kw)
            t = nxt
        beat = pend + float(rng.choice([1, 1.5, 2, 2.5]))


# --------------------------------------------------------------------------
# Блюз
# --------------------------------------------------------------------------
def blues_changes(key, minor=False, quick=False, ext='7'):
    I, IV, V = key, key + 5, key + 7
    if minor:
        n = lambda pc, q: chord_name(pc, q)
        return [n(I, 'm7'), n(IV, 'm7'), n(I, 'm7'), n(I, 'm7'), n(IV, 'm7'), n(IV, 'm7'),
                n(I, 'm7'), n(I, 'm7'), n(key + 8, '7'), n(V, '7#9'), n(I, 'm7'), n(V, '7#9')]
    n = lambda pc: chord_name(pc, ext)
    return [n(I), n(IV) if quick else n(I), n(I), n(I), n(IV), n(IV), n(I), n(I),
            n(V), n(IV), n(I), n(V)]


T3 = 1 / 3
# (доля, длительность, полутоны от тоники, бенд, вибрато)
LICKS = [
    [(0, 2 * T3, 3, 1, 0), (2 * T3, T3, 0, 0, 0), (1, 1, -2, 0, 0), (2, 1.5, 0, 0, 1)],
    [(0, 1, 7, 2, 0), (1, 2 * T3, 7, 0, 0), (1 + 2 * T3, T3, 5, 0, 0), (2, 2 * T3, 3, 0, 0),
     (2 + 2 * T3, T3, 0, 0, 0), (3, 1, 0, 0, 1)],
    [(0, T3, 12, 0, 0), (T3, T3, 10, 0, 0), (2 * T3, T3, 7, 0, 0), (1, T3, 10, 0, 0), (1 + T3, T3, 7, 0, 0),
     (1 + 2 * T3, T3, 5, 0, 0), (2, T3, 7, 0, 0), (2 + T3, T3, 5, 0, 0), (2 + 2 * T3, T3, 3, 0, 0),
     (3, 1, 0, 0, 1)],
    [(0, 2 * T3, 12, 0, 0), (2 * T3, T3, 12, 0, 0), (1, 2 * T3, 12, 2, 0), (1 + 2 * T3, T3, 10, 0, 0),
     (2, 1.5, 12, 0, 1)],
    [(0, 2 * T3, 14, 0, 0), (2 * T3, T3, 12, 0, 0), (1, 1, 14, 2, 0), (2, 2 * T3, 12, 0, 0),
     (2 + 2 * T3, T3, 9, 0, 0), (3, 1, 12, 0, 1)],
    [(0, 2 * T3, -5, 0, 0), (2 * T3, T3, -2, 0, 0), (1, 2 * T3, 0, 0, 0), (1 + 2 * T3, T3, 3, 0, 0),
     (2, 1, 4, 1, 0), (3, 1, 0, 0, 1)],
    [(0, T3, 7, 0, 0), (T3, T3, 6, 0, 0), (2 * T3, T3, 5, 0, 0), (1, T3, 3, 0, 0), (1 + T3, T3, 0, 0, 0),
     (1 + 2 * T3, T3, -2, 0, 0), (2, 1.5, 0, 0, 1)],
    [(0, 2, 7, 2, 1), (2, 2 * T3, 5, 0, 0), (2 + 2 * T3, T3, 3, 0, 0), (3, 1, 0, 0, 0)],
    [(0, 2 * T3, 10, 0, 0), (2 * T3, T3, 7, 0, 0), (1, 2 * T3, 10, 0, 0), (1 + 2 * T3, T3, 7, 0, 0),
     (2, 2 * T3, 5, 2, 0), (2 + 2 * T3, T3, 3, 0, 0), (3, 1, 5, 0, 1)],
    [(0, T3, 0, 0, 0), (T3, T3, 3, 0, 0), (2 * T3, T3, 5, 0, 0), (1, T3, 6, 0, 0), (1 + T3, T3, 7, 0, 0),
     (1 + 2 * T3, T3, 10, 0, 0), (2, 2, 12, 0, 1)],
]
TURNAROUND = [(0, 2 * T3, 12, 0, 0), (2 * T3, T3, 10, 0, 0), (1, 2 * T3, 9, 0, 0), (1 + 2 * T3, T3, 8, 0, 0),
              (2, 1, 7, 0, 0), (3, 1, 4, 1, 0), (4, 2, 7, 0, 1)]


def blues_line(part, licks, start, ref, rng, vel=0.85, minor=False, bend_style='bend', transpose=0, **kw):
    """Играет последовательность ликов с start; bend_style: bend | slide | scoop."""
    t = start
    for lick in licks:
        for b, d, s, bend, vib in lick:
            s = s + transpose
            if minor and s % 12 == 4:
                s -= 1
            p = ref + s
            extra = {}
            if bend:
                if bend_style == 'bend':
                    extra['bends'] = [(0.03, 0.03 + 0.12 * min(1, d), bend)]
                    p -= bend
                elif bend_style == 'slide':
                    extra['bends'] = [(0.0, 0.08, bend)]
                    p -= bend
            if vib and bend_style in ('bend', 'slide'):
                extra['vib'] = 0.35 if bend_style == 'bend' else 0.25
            part.note(t + b, d * 0.95, p, vel * rng.uniform(0.85, 1.05), **extra, **kw)
        t += max(b + d for b, d, *_ in lick)
    return t


def lick_len(lick):
    return max(b + d for b, d, *_ in lick)


def shuffle_drums(part, b0, b1, rng, style='shuffle', vel=0.8, offset=0, fill_every=4, crash_first=True):
    for bar in range(b0, b1):
        B = offset + bar * 4
        last = (bar - b0) % fill_every == fill_every - 1
        if crash_first and bar == b0:
            part.hit(B, 'crash', vel * 0.8)
        for beat in range(4):
            b = B + beat
            if style == 'slow':
                cym = 'ride' if (bar // 4) % 2 else 'hat'
                for k in range(3):
                    part.hit(b + k * T3, cym, vel * (0.75 if k == 0 else 0.45) * rng.uniform(0.9, 1.05))
            elif style == 'train':
                for k, v in ((0, 0.55), (2 * T3, 0.35)):
                    part.hit(b + k, 'snare', vel * (v + (0.3 if beat % 2 and k == 0 else 0)) * rng.uniform(0.9, 1.05))
                part.hit(b, 'hat', vel * 0.4)
            else:
                cym = 'ride' if style == 'ride' else 'hat'
                part.hit(b, cym, vel * 0.7 * rng.uniform(0.9, 1.05))
                part.hit(b + 2 * T3, cym, vel * 0.45 * rng.uniform(0.9, 1.05))
            if beat in (0, 2):
                part.hit(b, 'kick', vel * 0.85)
            if style != 'train' and beat in (1, 3):
                part.hit(b, 'snare', vel * 0.8 * rng.uniform(0.95, 1.05))
            if style != 'train' and rng.random() < 0.12:
                part.hit(b + 2 * T3, 'snare', vel * 0.2)
        if rng.random() < 0.3:
            part.hit(B + 1 + 2 * T3, 'kick', vel * 0.5)
        if last:
            for k in range(3):
                part.hit(B + 3 + k * T3, 'snare' if k < 2 else 'tom_lo', vel * (0.5 + 0.15 * k))


def boogie_bass(part, ch, b0, b1, rng, lo=28, hi=48, pattern='walk8', vel=0.85, offset=0, minor=False):
    for bar in range(b0, b1):
        c = ch.at(bar * 4)
        r = near_pc(c.root, (lo + hi) // 2 - 4, lo, hi - 10)
        third = 3 if minor or c.qual.startswith('m') else 4
        B = offset + bar * 4
        if pattern == 'walk8':
            seq = [0, third, 7, 9, 10, 9, 7, third]
            for i, s in enumerate(seq):
                part.note(B + (i // 2) + (i % 2) * 2 * T3, 0.6 if i % 2 == 0 else 0.3, r + s, vel * (1 if i % 2 == 0 else 0.8))
        elif pattern == 'walk4':
            seq = [0, third, 7, 9] if bar % 2 == 0 else [10, 9, 7, third]
            nxt = ch.at((bar + 1) * 4) if (bar + 1) * 4 < ch.total else c
            for i, s in enumerate(seq):
                p = r + s
                if i == 3 and nxt.sym != c.sym:
                    tgt = near_pc(nxt.root, p, lo, hi)
                    p = tgt - 1 if rng.random() < 0.6 else tgt + 1
                part.note(B + i, 0.9, p, vel)
                if rng.random() < 0.25 and i < 3:
                    part.note(B + i + 2 * T3, 0.25, p + (12 if p + 12 <= hi else 0), vel * 0.5)
        elif pattern == 'root5':
            for i, s in enumerate([0, 7, 9, 7]):
                part.note(B + i, 0.85, r + s, vel)
        elif pattern == 'thumb':
            for i in range(4):
                part.note(B + i, 0.35, r, vel * (1 if i % 2 == 0 else 0.85))


def guitar_boogie(part, ch, b0, b1, rng, lo=40, vel=0.7, offset=0):
    """Ритм-гитара: чередование квинты и сексты (приглушённые двойные ноты)."""
    for bar in range(b0, b1):
        c = ch.at(bar * 4)
        r = near_pc(c.root, lo + 4, lo, lo + 11)
        B = offset + bar * 4
        for beat in range(4):
            top = 7 if beat % 2 == 0 else 9
            for k in (0, 2 * T3):
                part.chord(B + beat + k, 0.3, [r, r + top], vel * (1 if k == 0 else 0.8), strum=0.008)


def blues_comp_stabs(part, ch, b0, b1, rng, lo=55, hi=74, vel=0.55, offset=0, pattern=(1, 3)):
    prev = None
    for bar in range(b0, b1):
        c = ch.at(bar * 4)
        v = voice(c.rootless(), lo, hi, prev)
        prev = v
        for b in pattern:
            part.chord(offset + bar * 4 + b, 0.4, v, vel * rng.uniform(0.85, 1.1), strum=0.01)


def pads(part, ch, b0, b1, rng, lo=52, hi=74, vel=0.5, offset=0, rootless=True):
    prev = None
    for bar in range(b0, b1):
        for b in range(ch.bpb):
            beat = bar * ch.bpb + b
            if b and not ch.is_change(beat):
                continue
            c = ch.at(beat)
            L = 1
            while b + L < ch.bpb and not ch.is_change(beat + L):
                L += 1
            v = voice(c.rootless() if rootless else c.pcs, lo, hi, prev)
            prev = v
            part.chord(offset + beat, L * 0.98, v, vel * rng.uniform(0.9, 1.05))
