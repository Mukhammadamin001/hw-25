#!/usr/bin/env python3
"""Генератор демо-музыки для плеера.

Все 21 трек — оригинальные композиции: ноты сочиняются алгоритмически
(scripts/music/songs.py), звук синтезируется с нуля (scripts/music/synth.py),
результат кодируется в MP3 и раскладывается по public/music/{jazz,classic,blues}.
Заодно пересобирается public/tracks.json.

    python3 -m venv .venv
    .venv/bin/pip install -r scripts/requirements.txt
    .venv/bin/python scripts/generate_music.py              # все треки
    .venv/bin/python scripts/generate_music.py jazz/3       # только один
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from music import songs  # noqa: E402
from music.synth import SR  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALBUM = 'Claude Sessions'

# (категория, название, исполнитель, функция-партитура)
TRACKS = [
    ('jazz', 'Midnight Avenue', 'Leo Carter', 'midnight_avenue'),
    ('jazz', 'Blue Velvet Rain', 'Nora Hayes', 'blue_velvet_rain'),
    ('jazz', 'Smoke & Saxophone', 'The Quiet Trio', 'smoke_and_saxophone'),
    ('jazz', 'Late Night Samarkand', 'Aziz Rahimov Quartet', 'late_night_samarkand'),
    ('jazz', 'Autumn Coffee', 'Mila Stone', 'autumn_coffee'),
    ('jazz', 'Brass Reflections', 'Jonah Reed', 'brass_reflections'),
    ('classic', 'Morning Prelude', 'Elena Voss', 'morning_prelude'),
    ('classic', 'Serenade in G', 'Aurora String Quartet', 'serenade_in_g'),
    ('classic', 'Nocturne of the Silent Lake', 'Adrian Morel', 'nocturne_silent_lake'),
    ('classic', 'Waltz of the Lanterns', 'Sofia Lindqvist', 'waltz_of_the_lanterns'),
    ('classic', 'Canon in Autumn', 'Aurora String Quartet', 'canon_in_autumn'),
    ('classic', 'Spring Dance (Allegro)', 'Camerata Nova', 'spring_dance'),
    ('classic', 'Adagio for a Grey Morning', 'Camerata Nova', 'adagio_grey_morning'),
    ('classic', 'Pastorale for Harp and Flute', 'Isabelle Fontaine & Lucas Meyer', 'pastorale_harp_flute'),
    ('blues', 'Crossroads at Dawn', 'Delta Joe Walker', 'crossroads_at_dawn'),
    ('blues', 'Whiskey Rain Shuffle', 'Johnny Ray Coleman', 'whiskey_rain_shuffle'),
    ('blues', 'Blue Monday Boogie', 'Eddie "Keys" Morgan', 'blue_monday_boogie'),
    ('blues', 'Muddy Road Home', 'Sam Tucker', 'muddy_road_home'),
    ('blues', 'Midnight Train Blues', 'Harmonica Slim & The Rail Riders', 'midnight_train_blues'),
    ('blues', 'Minor Mood Blues', 'Lena Brooks Trio', 'minor_mood_blues'),
    ('blues', "Last Call at Joe's", 'Otis Grant', 'last_call_at_joes'),
]


def track_list():
    out, counters = [], {}
    for i, (cat, title, artist, fn) in enumerate(TRACKS, start=1):
        counters[cat] = counters.get(cat, 0) + 1
        out.append(dict(id=i, key=f'{cat}/{counters[cat]}', category=cat, title=title, artist=artist,
                        fn=fn, file=f'music/{cat}/{counters[cat]}.mp3'))
    return out


def id3_tag(title, artist, genre, track):
    def frame(fid, text):
        data = b'\x00' + text.encode('latin-1')
        return fid.encode() + len(data).to_bytes(4, 'big') + b'\x00\x00' + data

    frames = (frame('TIT2', title) + frame('TPE1', artist) + frame('TALB', ALBUM)
              + frame('TCON', genre.capitalize()) + frame('TRCK', str(track)))
    n = len(frames)
    size = bytes([(n >> 21) & 0x7F, (n >> 14) & 0x7F, (n >> 7) & 0x7F, n & 0x7F])
    return b'ID3\x03\x00\x00' + size + frames


def encode_mp3(x, bitrate):
    import lameenc
    enc = lameenc.Encoder()
    enc.set_bit_rate(bitrate)
    enc.set_in_sample_rate(SR)
    enc.set_channels(2)
    enc.set_quality(2)
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    return enc.encode(pcm.tobytes()) + enc.flush()


def render(job):
    tr, bitrate, out_dir = job
    t0 = time.time()
    x = getattr(songs, tr['fn'])().render()
    path = os.path.join(out_dir, tr['category'], os.path.basename(tr['file']))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    num = int(tr['key'].split('/')[1])
    with open(path, 'wb') as f:
        f.write(id3_tag(tr['title'], tr['artist'], tr['category'], num) + encode_mp3(x, bitrate))
    dur = len(x) / SR
    peak = float(np.abs(x).max())
    print(f"  {tr['key']:10s} {tr['title']:26s} {int(dur // 60)}:{int(dur % 60):02d}  "
          f"peak {peak:.2f}  {os.path.getsize(path) / 1e6:.1f} MB  ({time.time() - t0:.0f}s)", flush=True)
    return tr['key'], round(dur, 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('only', nargs='*', help='ключи треков, например jazz/1 classic/3')
    ap.add_argument('--out', default=os.path.join(ROOT, 'public', 'music'))
    ap.add_argument('--json', default=os.path.join(ROOT, 'public', 'tracks.json'))
    ap.add_argument('--bitrate', type=int, default=128)
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    tracks = track_list()
    todo = [t for t in tracks if not args.only or t['key'] in args.only]
    print(f'Рендер {len(todo)} трек(ов)...')
    with Pool(max(1, min(args.jobs, len(todo)))) as pool:
        durations = dict(pool.imap_unordered(render, [(t, args.bitrate, args.out) for t in todo]))

    # tracks.json: длительности уже отрендеренных треков берём из старого файла
    old = {}
    if os.path.exists(args.json):
        with open(args.json, encoding='utf-8') as f:
            old = {t['file']: t.get('duration') for t in json.load(f)}
    data = []
    for t in tracks:
        dur = durations.get(t['key'], old.get(t['file']))
        item = {k: t[k] for k in ('id', 'title', 'artist', 'category', 'file')}
        if dur:
            item['duration'] = dur
        data.append(item)
    with open(args.json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'Готово: {args.json}')


if __name__ == '__main__':
    main()
