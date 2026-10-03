// Адрес API со списком пользователей
const API_URL = 'https://jsonplaceholder.typicode.com/users';
const USERS_LIMIT = 10;

const usersEl = document.getElementById('users');
const countEl = document.getElementById('count');
const errorEl = document.getElementById('error');
const retryBtn = document.getElementById('retryBtn');

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

// Номер для ссылки tel: — без добавочного («x56442») и лишних символов
function getPhoneHref(phone) {
  return phone.split(' x')[0].replace(/[^\d+]/g, '');
}

// Склонение: 1 пользователь, 2 пользователя, 5 пользователей
function pluralUsers(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return 'пользователь';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'пользователя';
  return 'пользователей';
}

// Разметка одной карточки
function createUserCard(user) {
  const { id, name, username, email, phone, website, address, company } = user;
  // У каждого пользователя свой цвет аватара — оттенок зависит от id
  const hue = (id * 37) % 360;

  return `
    <article class="card">
      <div class="card__head">
        <div class="card__avatar" style="--hue: ${hue}">${escapeHtml(getInitials(name))}</div>
        <div>
          <h2 class="card__name">${escapeHtml(name)}</h2>
          <p class="card__username">@${escapeHtml(username)}</p>
        </div>
      </div>

      <dl class="card__info">
        <dt>Email</dt>
        <dd><a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a></dd>

        <dt>Телефон</dt>
        <dd><a href="tel:${escapeHtml(getPhoneHref(phone))}">${escapeHtml(phone)}</a></dd>

        <dt>Сайт</dt>
        <dd><a href="https://${escapeHtml(website)}" target="_blank" rel="noopener">${escapeHtml(website)}</a></dd>

        <dt>Адрес</dt>
        <dd>${escapeHtml(address.city)}, ${escapeHtml(address.street)}, ${escapeHtml(address.suite)}</dd>
      </dl>

      <footer class="card__company">
        <p class="card__company-name">${escapeHtml(company.name)}</p>
        <p class="card__company-phrase">«${escapeHtml(company.catchPhrase)}»</p>
      </footer>
    </article>
  `;
}

// Пока идёт запрос, показываем «скелеты» карточек
function renderSkeletons() {
  usersEl.innerHTML = '<div class="card card--skeleton"></div>'.repeat(USERS_LIMIT);
}

function renderUsers(users) {
  usersEl.innerHTML = users.map(createUserCard).join('');
  countEl.textContent = `${users.length} ${pluralUsers(users.length)}`;
  countEl.hidden = false;
}

async function loadUsers() {
  errorEl.hidden = true;
  countEl.hidden = true;
  usersEl.setAttribute('aria-busy', 'true');
  renderSkeletons();

  try {
    // _limit — параметр jsonplaceholder: сколько записей вернуть
    const response = await axios.get(API_URL, { params: { _limit: USERS_LIMIT } });
    renderUsers(response.data);
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error.message);
    usersEl.innerHTML = '';
    errorEl.hidden = false;
  } finally {
    usersEl.setAttribute('aria-busy', 'false');
  }
}

retryBtn.addEventListener('click', loadUsers);

loadUsers();
