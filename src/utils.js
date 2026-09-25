// Секунды -> «м:сс»: formatTime(84) === '1:24'
export function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return min + ':' + String(sec).padStart(2, '0');
}

// «1 трек», «3 трека», «6 треков»
export function pluralTracks(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  let word = 'треков';
  if (mod10 === 1 && mod100 !== 11) word = 'трек';
  else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) word = 'трека';
  return `${n} ${word}`;
}

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

// localStorage может быть недоступен (приватный режим, запрет cookies) — не падаем
export const storage = {
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* ignore */
    }
  },
};
