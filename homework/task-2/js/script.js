// Базовый адрес API
const API_URL = 'https://jsonplaceholder.typicode.com';
const SKELETON_COUNT = 6;

const authorEl = document.getElementById('author');
const userSelect = document.getElementById('userSelect');
const countEl = document.getElementById('count');
const postsEl = document.getElementById('posts');
const errorEl = document.getElementById('error');
const errorTextEl = document.getElementById('errorText');
const retryBtn = document.getElementById('retryBtn');

let users = [];
// Номер последнего запроса постов: если пользователя сменили, пока ждали ответ,
// старый ответ уже не нужен и не должен затереть новый
let lastRequestId = 0;
// Что повторить по кнопке «Попробовать снова»
let retryAction = null;

// Экранируем текст перед вставкой в innerHTML, чтобы данные не превратились в разметку
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Инициалы для аватара: «Mrs. Dennis Schulist» → «DS» (обращения вроде «Mrs.» пропускаем)
function getInitials(name) {
  return name
    .split(' ')
    .filter((word) => word && !word.endsWith('.'))
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join('');
}

// Заголовки в API написаны с маленькой буквы — делаем первую заглавной
function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// Склонение: 1 пост, 2 поста, 5 постов
function pluralPosts(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return 'пост';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'поста';
  return 'постов';
}

function showError(message, onRetry) {
  errorTextEl.textContent = message;
  retryAction = onRetry;
  errorEl.hidden = false;
}

// Пока идёт запрос, показываем «скелеты» постов
function renderSkeletons() {
  postsEl.innerHTML = '<div class="post post--skeleton"></div>'.repeat(SKELETON_COUNT);
}

function renderUserOptions() {
  userSelect.innerHTML = users
    .map((user) => `<option value="${user.id}">${escapeHtml(user.name)}</option>`)
    .join('');
  userSelect.disabled = false;
}

function renderAuthor(user) {
  // Цвет аватара зависит от id — как в задаче 1
  const hue = (user.id * 37) % 360;

  authorEl.innerHTML = `
    <div class="author__avatar" style="--hue: ${hue}">${escapeHtml(getInitials(user.name))}</div>
    <div>
      <h2 class="author__name">${escapeHtml(user.name)}</h2>
      <p class="author__meta">
        @${escapeHtml(user.username)} ·
        <a href="mailto:${escapeHtml(user.email)}">${escapeHtml(user.email)}</a>
      </p>
    </div>
  `;
}

// Разметка одного поста
function createPostCard(post, index) {
  return `
    <article class="post">
      <span class="post__number">Пост #${index + 1}</span>
      <h3 class="post__title">${escapeHtml(capitalize(post.title))}</h3>
      <p class="post__body">${escapeHtml(post.body)}</p>
    </article>
  `;
}

function renderPosts(posts) {
  postsEl.innerHTML = posts.length
    ? posts.map(createPostCard).join('')
    : '<p class="posts__empty">У этого пользователя пока нет постов.</p>';
  countEl.textContent = `${posts.length} ${pluralPosts(posts.length)}`;
  countEl.hidden = false;
}

async function loadPosts(userId) {
  const requestId = ++lastRequestId;
  const user = users.find((item) => item.id === userId);

  errorEl.hidden = true;
  countEl.hidden = true;
  postsEl.setAttribute('aria-busy', 'true');
  renderAuthor(user);
  renderSkeletons();

  try {
    // params превратится в строку запроса: /posts?userId=1
    const response = await axios.get(`${API_URL}/posts`, { params: { userId } });
    if (requestId !== lastRequestId) return;
    renderPosts(response.data);
  } catch (error) {
    if (requestId !== lastRequestId) return;
    console.error('Ошибка загрузки постов:', error.message);
    postsEl.innerHTML = '';
    showError('Не удалось загрузить посты.', () => loadPosts(userId));
  } finally {
    if (requestId === lastRequestId) postsEl.setAttribute('aria-busy', 'false');
  }
}

// Сначала загружаем пользователей для списка, затем посты первого из них
async function init() {
  errorEl.hidden = true;
  postsEl.setAttribute('aria-busy', 'true');
  renderSkeletons();

  try {
    const response = await axios.get(`${API_URL}/users`);
    users = response.data;
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error.message);
    postsEl.innerHTML = '';
    postsEl.setAttribute('aria-busy', 'false');
    showError('Не удалось загрузить пользователей.', init);
    return;
  }

  renderUserOptions();
  loadPosts(users[0].id);
}

userSelect.addEventListener('change', () => loadPosts(Number(userSelect.value)));
retryBtn.addEventListener('click', () => retryAction());

init();
