# ⚙️ CNC Master Cloud

Рабочее ядро Telegram-платформы для операторов, наладчиков и технологов ЧПУ.

**Создатель:** Єрошов Іван  
**Версия:** 0.1.0

## Что уже работает

- Telegram-бот на русском языке.
- Создание профиля станка.
- Выбор типа оборудования.
- Выбор производителя и модели стойки.
- Онлайн-база PostgreSQL.
- Стартовые производители: Siemens, FANUC, HEIDENHAIN, Haas, Mitsubishi Electric, Mazak, Okuma, Fagor.
- Поиск G/M-кодов.
- Справочник материалов.
- REST API с автоматической документацией.
- Защищённая веб-админка.
- Redis для состояний Telegram-диалогов.
- Запуск всей системы через Docker Compose.
- Автоматическое создание таблиц и стартовое наполнение базы.

## Важно по безопасности ЧПУ

Стартовые G/M-коды имеют статус `needs_review`. Команды, циклы, M-функции и поведение могут отличаться:

- между производителями стоек;
- между версиями ПО;
- между токарной и фрезерной конфигурацией;
- из-за параметров и опций изготовителя станка.

Никакую сгенерированную или найденную программу нельзя запускать вслепую. Нужны графическая проверка, холостой прогон, Single Block, сниженный Rapid Override и проверка коррекций.

## Быстрый запуск

### 1. Установите Docker Desktop

Нужны Docker и Docker Compose.

### 2. Создайте файл `.env`

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Откройте `.env` и замените:

```env
BOT_TOKEN=PASTE_TELEGRAM_BOT_TOKEN_HERE
ADMIN_KEY=replace-with-a-long-random-secret
```

Токен берётся у официального бота `@BotFather`.

### 3. Запустите

```bash
docker compose up -d --build
```

### 4. Проверьте

- API: `http://localhost:8000`
- Документация API: `http://localhost:8000/docs`
- Админка: `http://localhost:8000/admin`
- Логи: `docker compose logs -f`

В админке вставьте значение `ADMIN_KEY` из `.env`.

## Команды управления

```bash
docker compose ps
docker compose logs -f --tail=200
docker compose restart
docker compose down
```

Данные PostgreSQL и Redis сохраняются в Docker volumes.

## Структура

```text
Telegram
   ↓
bot (aiogram)
   ↓
api (FastAPI)
   ↓
PostgreSQL + Redis
   ↓
веб-админка
```

## API

Основные маршруты:

- `GET /api/v1/manufacturers`
- `GET /api/v1/controllers`
- `GET /api/v1/codes/search?q=G96`
- `GET /api/v1/materials`
- `POST /api/v1/users/upsert`
- `GET /api/v1/users/{telegram_id}/machines`
- `POST /api/v1/machines`
- `GET /api/v1/admin/stats`

Административные запросы требуют заголовок:

```text
X-Admin-Key: значение ADMIN_KEY
```

## Следующие модули

Архитектура уже подготовлена для расширения:

1. каталог державок и пластин;
2. расчёт режимов по материалу и инструменту;
3. версии документации и история правок;
4. ошибки/аварии стоек;
5. циклы обработки;
6. загрузка PDF и чертежей;
7. генератор техпроцесса;
8. безопасный анализ G-кода;
9. перевод программ между стойками с предупреждениями;
10. роли эксперта, модератора, администратора и владельца;
11. подписки и корпоративные кабинеты.

## Разработка без Docker

Нужны Python 3.12, PostgreSQL и Redis.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.api_main:app --reload
```

Во втором терминале:

```bash
python -m app.bot_main
```
