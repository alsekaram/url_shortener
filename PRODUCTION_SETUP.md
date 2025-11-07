# 🚀 Production Setup для /opt/url_shortener

## 📍 Расположение

- **На сервере:** `/opt/url_shortener/`
- **В контейнере:** `/app/` (автоматически)
- **База данных:**
  - На сервере: `/opt/url_shortener/data/links.db`
  - В контейнере: `/app/data/links.db`

## 🔧 Настройка .env

### 1. Создайте .env файл

```bash
cd /opt/url_shortener
nano .env
```

### 2. Заполните по шаблону

```bash
# Server
HOST=0.0.0.0
PORT=8000
DATABASE_PATH=/app/data/links.db

# Telegram (ОБЯЗАТЕЛЬНО заменить!)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Reports Schedule
DAILY_REPORT_TIME=09:00
WEEKLY_REPORT_DAY=monday
WEEKLY_REPORT_TIME=09:00
TIMEZONE=Europe/Moscow

# Logging
LOG_LEVEL=INFO
```

### 3. Важные моменты

#### ✅ DATABASE_PATH должен быть `/app/data/links.db`
**НЕ** `/opt/url_shortener/data/links.db` - это путь внутри контейнера!

Почему это работает:
```yaml
# docker-compose.yml содержит:
volumes:
  - ./data:/app/data
```

Это означает:
- `/opt/url_shortener/data/` на хосте → `/app/data/` в контейнере
- Файл `/opt/url_shortener/data/links.db` доступен как `/app/data/links.db` в контейнере

#### ✅ HOST должен быть `0.0.0.0`
Чтобы сервис был доступен снаружи контейнера.

#### ✅ PORT по умолчанию `8000`
Можно изменить, если порт занят.

## 🔐 Получение Telegram credentials

### Получить Bot Token

1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/BotFather)
3. Отправьте команду: `/newbot`
4. Следуйте инструкциям (имя бота, username)
5. Скопируйте токен (формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Получить Chat ID (личный)

1. Найдите [@userinfobot](https://t.me/userinfobot)
2. Отправьте любое сообщение
3. Скопируйте ваш ID (число, например: `123456789`)

### Получить Chat ID (группа)

1. Создайте группу в Telegram
2. Добавьте туда вашего бота
3. Отправьте любое сообщение в группу
4. Откройте в браузере:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
5. Найдите `"chat":{"id":-1001234567890}` в ответе
6. Скопируйте ID (с минусом, если есть)

## 📂 Структура на сервере

```
/opt/url_shortener/
├── .env                    # Ваша конфигурация (НЕ коммитить!)
├── .env.production.example # Пример для продакшена
├── data/                   # База данных (создается автоматически)
│   ├── .gitkeep
│   └── links.db           # SQLite база (создается при первом запуске)
├── docker-compose.yml      # Docker конфигурация
├── Makefile               # Удобные команды
├── src/                   # Исходный код
└── ...
```

## 🚀 Развертывание

### Первый запуск

```bash
cd /opt/url_shortener

# 1. Создать .env файл
nano .env
# Заполнить по шаблону выше

# 2. Создать папку для данных (если нет)
mkdir -p data

# 3. Запустить сервисы
make up

# 4. Проверить здоровье
curl http://localhost:8000/health

# 5. Проверить логи
make logs

# 6. Создать тестовую ссылку
make create CODE=test URL=https://google.com TITLE="Test Link"

# 7. Проверить список
make list

# 8. Отправить тестовый отчет в Telegram
make report-daily
```

### Обновление

```bash
cd /opt/url_shortener

# 1. Backup БД
make backup

# 2. Получить изменения
git pull

# 3. Пересобрать (данные сохранятся!)
make rebuild

# 4. Проверить
make health
make check-data
```

## 🔒 Безопасность

### Права доступа

```bash
# .env должен быть доступен только root/владельцу
chmod 600 /opt/url_shortener/.env

# База данных
chmod 600 /opt/url_shortener/data/links.db

# Папка данных
chmod 700 /opt/url_shortener/data
```

### Проверка .env

```bash
# Убедитесь, что .env НЕ в git
cat /opt/url_shortener/.gitignore | grep .env
# Должно быть: .env

# Проверить содержимое (без паролей в логах!)
head -n 5 /opt/url_shortener/.env
```

## 🔍 Проверка конфигурации

### Проверить переменные окружения в контейнере

```bash
cd /opt/url_shortener

# Зайти в контейнер
make shell

# Внутри контейнера:
echo $DATABASE_PATH
echo $TELEGRAM_BOT_TOKEN
echo $TIMEZONE
exit
```

### Проверить пути

```bash
# На хосте
ls -lh /opt/url_shortener/data/links.db

# В контейнере
docker compose exec web ls -lh /app/data/links.db

# Должен быть ОДИН файл, доступный с обеих сторон!
```

## 📊 Мониторинг

### Автоматический запуск при загрузке сервера

Создайте systemd service:

```bash
sudo nano /etc/systemd/system/url-shortener.service
```

```ini
[Unit]
Description=Doctor Link Tracker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/url_shortener
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активировать:

```bash
sudo systemctl daemon-reload
sudo systemctl enable url-shortener
sudo systemctl start url-shortener
sudo systemctl status url-shortener
```

### Логи через systemd

```bash
# Логи сервиса
sudo journalctl -u url-shortener -f

# Логи приложения
cd /opt/url_shortener
make logs
```

### Автоматический backup (cron)

```bash
sudo crontab -e
```

Добавить:

```bash
# Backup каждый день в 3:00
0 3 * * * cd /opt/url_shortener && make backup

# Удалять старые backups (>30 дней)
0 4 * * * find /opt/url_shortener/data -name "links.db.backup.*" -mtime +30 -delete
```

## 🌐 Nginx (опционально)

Если хотите использовать доменное имя с HTTPS:

```nginx
server {
    listen 80;
    server_name links.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Затем SSL через certbot:

```bash
sudo certbot --nginx -d links.yourdomain.com
```

## 🆘 Troubleshooting

### База данных не создается

```bash
# Проверить права
ls -la /opt/url_shortener/data/

# Проверить путь в .env
grep DATABASE_PATH /opt/url_shortener/.env
# Должно быть: DATABASE_PATH=/app/data/links.db

# Проверить монтирование
docker compose exec web ls -la /app/data/

# Создать вручную
docker compose exec web uv run python -m src.cli init-db
```

### Telegram отчеты не приходят

```bash
# Проверить токен и chat_id
grep TELEGRAM /opt/url_shortener/.env

# Отправить тестовый отчет
cd /opt/url_shortener
make report-daily

# Проверить логи scheduler
make logs-scheduler
```

### Порт занят

Измените PORT в .env:

```bash
PORT=8080
```

Перезапустите:

```bash
make restart
```

## 📝 Полезные команды

```bash
cd /opt/url_shortener

# Статус
make health
make check-data

# Управление
make up / down / restart / rebuild

# Backup
make backup

# Статистика
make list
make stats CODE=doctor1
make clicks CODE=doctor1

# Логи
make logs
make logs-web
make logs-scheduler

# Отчеты
make report-daily
make report-weekly
```

## ✅ Checklist для продакшена

- [ ] `.env` создан и заполнен корректными данными
- [ ] `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` настроены
- [ ] `DATABASE_PATH=/app/data/links.db` (НЕ путь на хосте!)
- [ ] Папка `/opt/url_shortener/data/` существует
- [ ] Права доступа настроены (chmod 600 .env)
- [ ] Сервис запущен: `make up`
- [ ] Health check работает: `curl http://localhost:8000/health`
- [ ] Telegram отчеты работают: `make report-daily`
- [ ] Настроен systemd для автозапуска
- [ ] Настроен cron для backup
- [ ] (Опционально) Настроен Nginx с SSL

Готово! 🎉

