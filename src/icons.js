// SVG-иконки. Контурные рисуются через stroke, «кнопочные» — заливкой.
const outline = (body) =>
  `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;

const solid = (body) =>
  `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">${body}</svg>`;

const speaker = '<path d="M11 5 6 9H2v6h4l5 4V5z"/>';

export const icons = {
  library: outline('<path d="M5 3.5v17M10 3.5v17M14.5 4l5 16.5"/>'),
  music: outline('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
  play: solid('<path d="M8 5.2v13.6a1 1 0 0 0 1.52.85l10.9-6.8a1 1 0 0 0 0-1.7L9.52 4.35A1 1 0 0 0 8 5.2z"/>'),
  pause: solid('<rect x="6.5" y="5" width="3.6" height="14" rx="1"/><rect x="13.9" y="5" width="3.6" height="14" rx="1"/>'),
  prev: solid('<rect x="5" y="5" width="2.4" height="14" rx="1"/><path d="M19 6.1v11.8a1 1 0 0 1-1.54.84L9.1 12.84a1 1 0 0 1 0-1.68l8.36-5.9A1 1 0 0 1 19 6.1z"/>'),
  next: solid('<rect x="16.6" y="5" width="2.4" height="14" rx="1"/><path d="M5 6.1v11.8a1 1 0 0 0 1.54.84l8.36-5.9a1 1 0 0 0 0-1.68L6.54 5.26A1 1 0 0 0 5 6.1z"/>'),
  shuffle: outline('<path d="M16 3h5v5M4 20 21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>'),
  repeat: outline('<path d="m17 1 4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="m7 23-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'),
  heart: outline('<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'),
  heartFilled: solid('<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'),
  volumeHigh: outline(`${speaker}<path d="M15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14"/>`),
  volumeLow: outline(`${speaker}<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>`),
  volumeMute: outline(`${speaker}<path d="m23 9-6 6M17 9l6 6"/>`),
  speaker: solid('<path d="M3 9h3.5L11 5v14l-4.5-4H3z"/><path d="M14.5 8.5a5 5 0 0 1 0 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'),
  clock: outline('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
  sun: outline('<circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2.5M12 20v2.5M4.22 4.22l1.77 1.77M18.01 18.01l1.77 1.77M1.5 12H4M20 12h2.5M4.22 19.78l1.77-1.77M18.01 5.99l1.77-1.77"/>'),
  moon: outline('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'),
};

// Подставляет иконки во все элементы с атрибутом data-icon
export function mountIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach((el) => {
    const svg = icons[el.dataset.icon];
    if (svg) el.innerHTML = svg;
  });
}
