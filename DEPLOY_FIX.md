# 🚀 Деплой исправления статистики на сервер

## 📋 Что исправлено

**Файл:** `src/database.py`

Исправлена проблема с timezone - заменено `datetime.now()` на `datetime.utcnow()` в трёх функциях:
- `get_daily_stats()` (строки 308-310)
- `get_weekly_stats()` (строка 358)
- `get_link_stats()` (строка 270)

## 🔧 Шаги деплоя на сервер

### 1. Подключитесь к серверу

```bash
ssh your-server
```

### 2. Перейдите в директорию проекта

```bash
cd /opt/url_shortener
```

### 3. Создайте backup базы данных

```bash
make backup
# Или вручную:
cp data/url_shortener.db data/url_shortener.db.backup.$(date +%Y%m%d_%H%M%S)
```

### 4. Получите изменения из репозитория

**Вариант A: Если используете git**
```bash
git pull origin main
```

**Вариант B: Если НЕ используете git (копирование вручную)**

На локальном компьютере создайте патч:
```bash
cd /Users/aleksandrmotor/code/life/url_shortener
git diff HEAD~1 src/database.py > timezone_fix.patch
```

Скопируйте файл на сервер:
```bash
scp timezone_fix.patch your-server:/opt/url_shortener/
```

На сервере примените патч:
```bash
cd /opt/url_shortener
patch -p1 < timezone_fix.patch
```

**Вариант C: Прямая замена файла**

На локальном компьютере:
```bash
scp src/database.py your-server:/opt/url_shortener/src/database.py
```

### 5. Перезапустите сервисы

```bash
cd /opt/url_shortener

# Пересобрать образы с новым кодом
docker compose build

# Перезапустить все сервисы
docker compose restart

# Или полный перезапуск:
docker compose down
docker compose up -d
```

### 6. Проверьте, что сервисы работают

```bash
# Проверка здоровья
make health
# или
curl http://localhost:8000/health

# Проверка логов
make logs
```

### 7. Отправьте тестовый отчет

```bash
make report-daily
```

Проверьте Telegram - должен прийти отчет с корректными данными!

## 🧪 Проверка исправления

### Проверить данные напрямую в базе

```bash
# Зайдите в shell контейнера
make shell

# Запустите Python
python3

# В Python:
from datetime import datetime, timedelta
from src.database import get_daily_stats
import asyncio

# Проверим текущее время
print("UTC now:", datetime.utcnow())
print("Local now:", datetime.now())
print("24h ago UTC:", datetime.utcnow() - timedelta(days=1))

# Получим статистику
stats = asyncio.run(get_daily_stats())
print(f"\nFound {len(stats)} links with activity")
for s in stats:
    print(f"- {s.title}: {s.clicks_period} clicks today")

exit()
```

### Посмотреть сырые данные в базе

```bash
# На сервере
cd /opt/url_shortener

# Откройте базу данных
sqlite3 data/url_shortener.db

# Посмотрите последние клики с их временем
SELECT id, link_id, clicked_at, 
       datetime(clicked_at, 'localtime') as local_time
FROM clicks 
ORDER BY clicked_at DESC 
LIMIT 10;

# Посмотрите клики за последние 24 часа
SELECT COUNT(*) as count_last_24h
FROM clicks
WHERE clicked_at >= datetime('now', '-1 day');

# Выход
.quit
```

## 📊 Ожидаемый результат

После исправления отчет должен показывать:

```
📊 Статистика за 24 часа
📅 19.11.2025
━━━━━━━━━━━━━━━━━━━━

👨‍⚕️ Доктор Гальченко
├─ Сегодня: 3 👆
├─ Всего: 9
└─ +50% 📈

━━━━━━━━━━━━━━━━━━━━
Всего: 3 переходов
```

## ❓ Если что-то пошло не так

### Откатить изменения

```bash
cd /opt/url_shortener

# Если использовали git
git checkout HEAD~1 src/database.py

# Восстановить из backup
cp data/url_shortener.db.backup.YYYYMMDD_HHMMSS data/url_shortener.db

# Перезапустить
docker compose restart
```

### Проверить логи ошибок

```bash
make logs-scheduler
make logs-web
```

## 📝 Заметки

- ✅ База данных остается нетронутой
- ✅ Старые данные не теряются
- ✅ Изменения только в коде Python
- ✅ Downtime минимален (только перезапуск контейнеров)

## 🎯 Краткая версия (если все работает)

```bash
# 1. Подключиться
ssh your-server

# 2. Перейти в проект
cd /opt/url_shortener

# 3. Backup
make backup

# 4. Обновить код
git pull
# или скопировать файл вручную

# 5. Перезапустить
docker compose build
docker compose restart

# 6. Проверить
make report-daily

# Готово! ✅
```
