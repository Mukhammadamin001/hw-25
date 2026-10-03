import { icons, mountIcons } from './icons.js';
import { clamp, formatTime, pluralTracks, storage } from './utils.js';

// Категории: порядок вкладок, подписи и цвет обложки
const CATEGORIES = [
  { id: 'jazz', name: 'Jazz', color: '#733ee3' },
  { id: 'classic', name: 'Classic', color: '#a95923' },
  { id: 'blues', name: 'Blues', color: '#2b4dcf' },
];

// ОДИН объект Audio на весь плеер — при переключении треков меняем только src
const audio = new Audio();
audio.preload = 'metadata';

// iOS не даёт менять громкость из JS (audio.volume всегда 1) — там ползунок прячем
const canSetVolume = (() => {
  const probe = new Audio();
  probe.volume = 0.5;
  return probe.volume === 0.5;
})();

let tracks = [];

const state = {
  category: 'jazz', // активная категория
  trackId: null, // какой трек выбран
  isPlaying: false, // играет или на паузе
  volume: 0.7, // текущая громкость
  lastVolume: 0.7, // громкость до mute — к ней возвращаемся
  shuffle: storage.get('player:shuffle', false) === true,
  repeat: storage.get('player:repeat', false) === true,
  liked: new Set(storage.get('player:liked', [])),
};

const durations = new Map(); // точные длительности, известные после loadedmetadata

// Shuffle без повторов: трек не звучит снова, пока не сыграны все треки категории.
// playedHistory — сыгранные треки, по ним «назад» в режиме shuffle возвращает к предыдущему
const shuffled = new Set();
const playedHistory = [];

const $ = (id) => document.getElementById(id);
const el = {
  root: document.documentElement,
  main: $('main'),
  mainScroll: $('mainScroll'),
  player: $('player'),
  categories: $('categories'),
  heroTitle: $('heroTitle'),
  tracks: $('tracks'),
  playlistPlay: $('playlistPlay'),
  playlistShuffle: $('playlistShuffle'),
  nowTitle: $('nowTitle'),
  nowArtist: $('nowArtist'),
  likeBtn: $('likeBtn'),
  shuffleBtn: $('shuffleBtn'),
  prevBtn: $('prevBtn'),
  playBtn: $('playBtn'),
  nextBtn: $('nextBtn'),
  repeatBtn: $('repeatBtn'),
  currentTime: $('currentTime'),
  durationTime: $('durationTime'),
  progress: $('progress'),
  progressFill: $('progressFill'),
  progressThumb: $('progressThumb'),
  muteBtn: $('muteBtn'),
  volumeIcon: $('volumeIcon'),
  volumeRange: $('volumeRange'),
  themeToggle: $('themeToggle'),
  themeColor: document.querySelector('meta[name="theme-color"]'),
  toast: $('toast'),
};

// ---------------------------------------------------------------------------
// Данные
// ---------------------------------------------------------------------------
const getTrack = (id) => tracks.find((t) => t.id === id) || null;
const getCategory = (id) => CATEGORIES.find((c) => c.id === id) || CATEGORIES[0];
const tracksOf = (category) => tracks.filter((t) => t.category === category);
const currentTrack = () => getTrack(state.trackId);
const trackDuration = (t) => durations.get(t.id) ?? t.duration;

async function loadTracks() {
  const response = await fetch('public/tracks.json');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error('tracks.json должен быть массивом');
  return data;
}

// ---------------------------------------------------------------------------
// Отрисовка
// ---------------------------------------------------------------------------
function renderCategories() {
  el.categories.innerHTML = CATEGORIES.map((c) => {
    const count = tracksOf(c.id).length;
    return `
      <button class="category scope" type="button" data-category="${c.id}" style="--accent: ${c.color}">
        <span class="cover category__cover">${icons.music}</span>
        <span class="category__text">
          <span class="category__name">${c.name}</span>
          <span class="category__meta">Плейлист · ${pluralTracks(count)}</span>
        </span>
        <span class="category__speaker" aria-hidden="true">${icons.speaker}</span>
      </button>`;
  }).join('');
  updateCategories();
}

function updateCategories() {
  const playingCategory = currentTrack()?.category;
  el.categories.querySelectorAll('.category').forEach((btn) => {
    const id = btn.dataset.category;
    btn.classList.toggle('is-active', id === state.category);
    btn.classList.toggle('is-current', id === playingCategory);
    btn.classList.toggle('is-playing', id === playingCategory && state.isPlaying);
    btn.setAttribute('aria-pressed', String(id === state.category));
  });
}

function renderHero() {
  const cat = getCategory(state.category);
  el.main.style.setProperty('--accent', cat.color);
  el.heroTitle.textContent = cat.name;
}

function renderTracks() {
  const list = tracksOf(state.category);
  if (!list.length) {
    el.tracks.innerHTML = '<li class="tracks__message">В этой категории пока нет треков</li>';
    return;
  }
  el.tracks.innerHTML = list.map((t, i) => `
    <li>
      <button class="track" type="button" data-id="${t.id}"
              aria-label="${escapeHtml(t.title)} — ${escapeHtml(t.artist)}">
        <span class="track__index">
          <span class="track__num">${i + 1}</span>
          <span class="track__eq" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
          <span class="track__action track__action--play" aria-hidden="true">${icons.play}</span>
          <span class="track__action track__action--pause" aria-hidden="true">${icons.pause}</span>
        </span>
        <span class="track__thumb" aria-hidden="true"></span>
        <span class="track__info">
          <span class="track__title">${escapeHtml(t.title)}</span>
          <span class="track__artist">${escapeHtml(t.artist)}</span>
        </span>
        <span class="track__time">${trackDuration(t) ? formatTime(trackDuration(t)) : '—:—'}</span>
      </button>
    </li>`).join('');
  updateTracks();
}

function updateTracks() {
  el.tracks.querySelectorAll('.track').forEach((row) => {
    const isCurrent = Number(row.dataset.id) === state.trackId;
    row.classList.toggle('is-active', isCurrent);
    row.classList.toggle('is-playing', isCurrent && state.isPlaying);
    if (isCurrent) row.setAttribute('aria-current', 'true');
    else row.removeAttribute('aria-current');
  });
}

function updatePlayButtons() {
  const track = currentTrack();
  const cat = getCategory(track ? track.category : state.category);
  el.player.style.setProperty('--accent', cat.color);

  el.playBtn.classList.toggle('is-playing', state.isPlaying);
  el.playBtn.setAttribute('aria-label', state.isPlaying ? 'Пауза' : 'Воспроизвести');

  // Большая кнопка над списком управляет именно открытым плейлистом
  const listIsPlaying = state.isPlaying && track?.category === state.category;
  el.playlistPlay.classList.toggle('is-playing', listIsPlaying);
  el.playlistPlay.setAttribute('aria-label', listIsPlaying ? 'Пауза' : 'Воспроизвести плейлист');

  for (const btn of [el.shuffleBtn, el.playlistShuffle]) {
    btn.classList.toggle('is-on', state.shuffle);
    btn.setAttribute('aria-pressed', String(state.shuffle));
  }
  el.repeatBtn.classList.toggle('is-on', state.repeat);
  el.repeatBtn.setAttribute('aria-pressed', String(state.repeat));

  if ('mediaSession' in navigator) {
    navigator.mediaSession.playbackState = track ? (state.isPlaying ? 'playing' : 'paused') : 'none';
  }
}

function renderNowPlaying() {
  const track = currentTrack();
  el.nowTitle.textContent = track ? track.title : 'Ничего не играет';
  el.nowArtist.textContent = track ? track.artist : 'Выберите трек';
  el.likeBtn.disabled = !track;
  const liked = !!track && state.liked.has(track.id);
  el.likeBtn.classList.toggle('is-on', liked);
  el.likeBtn.setAttribute('aria-pressed', String(liked));
  el.likeBtn.setAttribute('aria-label', liked ? 'Убрать из понравившихся' : 'Нравится');
  document.title = track ? `${state.isPlaying ? '▶ ' : ''}${track.title} — ${track.artist}` : 'Музыкальный плеер';
}

// Всё, что зависит от выбранного трека и play/pause
function updatePlayback() {
  updateCategories();
  updateTracks();
  updatePlayButtons();
  renderNowPlaying();
}

// ---------------------------------------------------------------------------
// Воспроизведение
// ---------------------------------------------------------------------------
function play() {
  const promise = audio.play();
  // play() возвращает Promise: при быстрой смене трека он отклоняется с AbortError —
  // это нормально, поэтому ошибку глушим (иначе она упадёт в консоль)
  if (promise) promise.catch(() => {});
}

function loadTrack(track, { back = false } = {}) {
  if (!back && state.trackId !== null && state.trackId !== track.id) {
    playedHistory.push(state.trackId);
    if (playedHistory.length > 100) playedHistory.shift();
  }
  state.trackId = track.id;
  shuffled.add(track.id);
  el.player.classList.remove('is-buffering');
  audio.src = track.file;
  const known = trackDuration(track);
  setProgress(0, known);
  updateMediaSession(track);
}

function playTrack(id) {
  // Клик по уже выбранному треку — пауза / продолжение
  if (id === state.trackId) {
    togglePlay();
    return;
  }
  const track = getTrack(id);
  if (!track) return;
  loadTrack(track);
  play();
  updatePlayback();
}

function togglePlay() {
  if (state.trackId === null) {
    playCategory(state.category);
    return;
  }
  if (audio.paused) play();
  else audio.pause();
}

function playCategory(category) {
  const list = tracksOf(category);
  if (!list.length) return;
  const track = state.shuffle ? pickShuffled(list, null) : list[0];
  playTrack(track.id);
}

// Случайный трек из ещё не сыгранных; когда сыграны все — начинаем новый круг
function pickShuffled(list, currentId) {
  const others = list.filter((t) => t.id !== currentId);
  if (!others.length) return list[0];
  let pool = others.filter((t) => !shuffled.has(t.id));
  if (!pool.length) {
    list.forEach((t) => shuffled.delete(t.id));
    pool = others;
  }
  return pool[Math.floor(Math.random() * pool.length)];
}

// Prev / Next — по кругу внутри категории ИГРАЮЩЕГО трека
function playNextTrack(step = 1) {
  const track = currentTrack();
  if (!track) {
    playCategory(state.category);
    return;
  }
  const list = tracksOf(track.category);
  let next;
  let back = false;
  if (state.shuffle && step > 0) {
    next = pickShuffled(list, track.id);
  } else if (state.shuffle && getTrack(playedHistory.at(-1))?.category === track.category) {
    next = getTrack(playedHistory.pop());
    back = true;
  } else {
    const index = list.findIndex((t) => t.id === track.id);
    next = list[(index + step + list.length) % list.length];
  }
  loadTrack(next, { back });
  play();
  updatePlayback();
}

const playPrevTrack = () => playNextTrack(-1);

// ---------------------------------------------------------------------------
// Прогресс
// ---------------------------------------------------------------------------
let dragging = false;

function setProgress(current, duration) {
  const ratio = duration > 0 ? clamp(current / duration, 0, 1) : 0;
  const percent = ratio * 100 + '%';
  el.progressFill.style.width = percent;
  el.progressThumb.style.left = percent;
  el.currentTime.textContent = formatTime(current);
  el.durationTime.textContent = formatTime(duration);
  el.progress.setAttribute('aria-valuemax', String(Math.floor(duration || 0)));
  el.progress.setAttribute('aria-valuenow', String(Math.floor(current || 0)));
  el.progress.setAttribute('aria-valuetext', `${formatTime(current)} из ${formatTime(duration)}`);
}

function ratioFromEvent(event) {
  const rect = el.progress.getBoundingClientRect();
  return clamp((event.clientX - rect.left) / rect.width, 0, 1);
}

function seekTo(seconds) {
  if (!Number.isFinite(audio.duration)) return;
  audio.currentTime = clamp(seconds, 0, audio.duration);
  setProgress(audio.currentTime, audio.duration);
  updatePositionState();
}

// ---------------------------------------------------------------------------
// Громкость
// ---------------------------------------------------------------------------
function setVolume(value) {
  state.volume = clamp(value, 0, 1);
  if (state.volume > 0) state.lastVolume = state.volume;
  audio.volume = state.volume;
  audio.muted = state.volume === 0; // muted работает и там, где volume менять нельзя (iOS)

  const percent = Math.round(state.volume * 100);
  el.volumeRange.value = String(percent);
  el.volumeRange.style.setProperty('--fill', percent + '%');

  const icon = state.volume === 0 ? 'volumeMute' : state.volume < 0.5 ? 'volumeLow' : 'volumeHigh';
  el.volumeIcon.innerHTML = icons[icon];
  el.muteBtn.setAttribute('aria-label', state.volume === 0 ? 'Включить звук' : 'Выключить звук');
  el.muteBtn.classList.toggle('is-muted', state.volume === 0);
  storage.set('player:volume', { volume: state.volume, lastVolume: state.lastVolume });
}

function toggleMute() {
  if (state.volume > 0) setVolume(0);
  else setVolume(state.lastVolume || 0.7); // возвращаем ПРЕЖНЮЮ громкость
}

// ---------------------------------------------------------------------------
// Прочее: тема, «нравится», media session, уведомления
// ---------------------------------------------------------------------------
function applyTheme(theme) {
  el.root.dataset.theme = theme;
  el.themeColor.content = theme === 'light' ? '#e7e6eb' : '#000000';
  el.themeToggle.setAttribute('aria-label', theme === 'light' ? 'Включить тёмную тему' : 'Включить светлую тему');
}

function toggleTheme() {
  const next = el.root.dataset.theme === 'light' ? 'dark' : 'light';
  applyTheme(next);
  storage.set('player:theme', next);
}

function toggleLike() {
  const track = currentTrack();
  if (!track) return;
  if (state.liked.has(track.id)) state.liked.delete(track.id);
  else state.liked.add(track.id);
  storage.set('player:liked', [...state.liked]);
  renderNowPlaying();
}

function updateMediaSession(track) {
  if (!('mediaSession' in navigator) || typeof MediaMetadata === 'undefined') return;
  navigator.mediaSession.metadata = new MediaMetadata({
    title: track.title,
    artist: track.artist,
    album: getCategory(track.category).name,
  });
}

// Полоса прогресса на экране блокировки и в системном мини-плеере
function updatePositionState() {
  if (!('mediaSession' in navigator) || !navigator.mediaSession.setPositionState) return;
  if (!Number.isFinite(audio.duration)) return;
  try {
    navigator.mediaSession.setPositionState({
      duration: audio.duration,
      playbackRate: audio.playbackRate,
      position: clamp(audio.currentTime, 0, audio.duration),
    });
  } catch {
    /* некорректное состояние — пропускаем */
  }
}

function setupMediaSession() {
  if (!('mediaSession' in navigator)) return;
  const handlers = {
    play: () => (state.trackId === null ? playCategory(state.category) : play()),
    pause: () => audio.pause(),
    previoustrack: () => playPrevTrack(),
    nexttrack: () => playNextTrack(),
    seekto: (details) => seekTo(details.seekTime),
    seekbackward: (details) => seekTo(audio.currentTime - (details.seekOffset || 10)),
    seekforward: (details) => seekTo(audio.currentTime + (details.seekOffset || 10)),
  };
  for (const [action, handler] of Object.entries(handlers)) {
    try {
      navigator.mediaSession.setActionHandler(action, handler);
    } catch {
      /* действие не поддерживается браузером */
    }
  }
}

let toastTimer = 0;
function showToast(text) {
  el.toast.textContent = text;
  el.toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.toast.classList.remove('is-visible'), 3500);
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
}

// ---------------------------------------------------------------------------
// События audio
// ---------------------------------------------------------------------------
audio.addEventListener('play', () => {
  state.isPlaying = true;
  updatePlayback();
});

audio.addEventListener('pause', () => {
  state.isPlaying = false;
  el.player.classList.remove('is-buffering');
  updatePlayback();
  updatePositionState();
});

// Данных не хватает (медленная сеть) — крутим индикатор вокруг кнопки play
audio.addEventListener('waiting', () => el.player.classList.add('is-buffering'));
audio.addEventListener('playing', () => {
  el.player.classList.remove('is-buffering');
  updatePositionState();
});

// Файл загрузился — известна точная длительность
audio.addEventListener('loadedmetadata', () => {
  const track = currentTrack();
  if (!track) return;
  durations.set(track.id, audio.duration);
  setProgress(audio.currentTime, audio.duration);
  updatePositionState();
  const row = el.tracks.querySelector(`.track[data-id="${track.id}"] .track__time`);
  if (row) row.textContent = formatTime(audio.duration);
});

// Несколько раз в секунду — двигаем полосу и таймер
audio.addEventListener('timeupdate', () => {
  if (!dragging) setProgress(audio.currentTime, audio.duration);
});

// Трек доиграл — включаем следующий (или повторяем, если включён повтор)
audio.addEventListener('ended', () => {
  if (state.repeat) {
    audio.currentTime = 0;
    play();
  } else {
    playNextTrack();
  }
});

audio.addEventListener('error', () => {
  const track = currentTrack();
  if (!track || !audio.getAttribute('src')) return;
  state.isPlaying = false;
  el.player.classList.remove('is-buffering');
  updatePlayback();
  showToast(`Не удалось загрузить «${track.title}»`);
});

// ---------------------------------------------------------------------------
// События интерфейса
// ---------------------------------------------------------------------------
el.categories.addEventListener('click', (event) => {
  const btn = event.target.closest('.category');
  if (!btn || btn.dataset.category === state.category) return;
  // Переключаем только список — играющий трек продолжает звучать
  state.category = btn.dataset.category;
  storage.set('player:category', state.category);
  renderHero();
  renderTracks();
  updatePlayback();
  el.mainScroll.scrollTop = 0;
});

el.tracks.addEventListener('click', (event) => {
  const row = event.target.closest('.track');
  if (row) playTrack(Number(row.dataset.id));
});

el.playlistPlay.addEventListener('click', () => {
  if (currentTrack()?.category === state.category) togglePlay();
  else playCategory(state.category);
});

const toggleShuffle = () => {
  state.shuffle = !state.shuffle;
  shuffled.clear();
  if (state.trackId !== null) shuffled.add(state.trackId);
  storage.set('player:shuffle', state.shuffle);
  updatePlayButtons();
};
el.playlistShuffle.addEventListener('click', toggleShuffle);
el.shuffleBtn.addEventListener('click', toggleShuffle);

el.repeatBtn.addEventListener('click', () => {
  state.repeat = !state.repeat;
  storage.set('player:repeat', state.repeat);
  updatePlayButtons();
});

el.playBtn.addEventListener('click', togglePlay);
el.prevBtn.addEventListener('click', playPrevTrack);
el.nextBtn.addEventListener('click', () => playNextTrack());
el.likeBtn.addEventListener('click', toggleLike);
el.themeToggle.addEventListener('click', toggleTheme);

// Перемотка: клик или перетаскивание по полосе
el.progress.addEventListener('pointerdown', (event) => {
  if (!Number.isFinite(audio.duration) || event.button !== 0) return;
  dragging = true;
  el.progress.setPointerCapture(event.pointerId);
  el.progress.classList.add('is-dragging');
  setProgress(ratioFromEvent(event) * audio.duration, audio.duration);
});

el.progress.addEventListener('pointermove', (event) => {
  if (dragging) setProgress(ratioFromEvent(event) * audio.duration, audio.duration);
});

const finishDrag = (event) => {
  if (!dragging) return;
  dragging = false;
  el.progress.classList.remove('is-dragging');
  // доля клика × длительность
  seekTo(ratioFromEvent(event) * audio.duration);
};
el.progress.addEventListener('pointerup', finishDrag);
el.progress.addEventListener('pointercancel', () => {
  dragging = false;
  el.progress.classList.remove('is-dragging');
});

el.progress.addEventListener('keydown', (event) => {
  const steps = { ArrowRight: 5, ArrowUp: 5, ArrowLeft: -5, ArrowDown: -5 };
  if (event.key in steps) seekTo(audio.currentTime + steps[event.key]);
  else if (event.key === 'Home') seekTo(0);
  else if (event.key === 'End') seekTo(audio.duration - 1);
  else return;
  event.preventDefault();
});

el.volumeRange.addEventListener('input', () => setVolume(Number(el.volumeRange.value) / 100));
el.muteBtn.addEventListener('click', toggleMute);

// Пробел — play/pause, если фокус не на кнопке или поле ввода
document.addEventListener('keydown', (event) => {
  if (event.code !== 'Space' || event.repeat) return;
  if (event.target.closest('button, input, textarea, select, [role="slider"]')) return;
  event.preventDefault();
  togglePlay();
});

// ---------------------------------------------------------------------------
// Старт
// ---------------------------------------------------------------------------
async function init() {
  mountIcons();
  applyTheme(el.root.dataset.theme === 'light' ? 'light' : 'dark');
  el.root.classList.toggle('no-volume', !canSetVolume);

  const savedVolume = storage.get('player:volume');
  if (savedVolume && typeof savedVolume.volume === 'number') {
    state.lastVolume = savedVolume.lastVolume || 0.7;
    setVolume(savedVolume.volume);
  } else {
    setVolume(state.volume);
  }

  const savedCategory = storage.get('player:category');
  if (CATEGORIES.some((c) => c.id === savedCategory)) state.category = savedCategory;

  renderHero();
  updatePlayButtons();
  setupMediaSession();

  try {
    tracks = await loadTracks();
  } catch {
    el.tracks.innerHTML = `<li class="tracks__message tracks__message--error">
      Не удалось загрузить tracks.json. Откройте проект через Live Server (или другой локальный сервер).
    </li>`;
    return;
  }

  renderCategories();
  renderTracks();
  updatePlayback();
}

init();
