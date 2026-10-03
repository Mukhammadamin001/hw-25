# Homework #27 — Vibe Coding

Данные берутся с тестового API [jsonplaceholder.typicode.com](https://jsonplaceholder.typicode.com),
запросы делаются через **axios** (подключён в каждом `index.html` через CDN).

```
homework/
  task-1/   index.html, css/style.css, js/script.js
  task-2/   index.html, css/style.css, js/script.js
```

Каждую задачу можно открыть двойным кликом по `index.html` или через Live Server.

## Задача 1 — Список пользователей

`GET /users?_limit=10` → 10 карточек: аватар с инициалами, имя, `@username`, email, телефон,
сайт, адрес и компания с её девизом.

- пока идёт запрос, показываются «скелеты» карточек;
- если запрос не удался, появляется сообщение и кнопка «Попробовать снова»;
- карточки строятся в JS из ответа API, в HTML их нет;
- адаптивная сетка, светлая и тёмная тема (по настройке системы).

## Задача 2

Заготовка: подключены axios, `css/style.css` и `js/script.js`.
