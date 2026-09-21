# 🚀 Инструкция по хостингу и деплою KCLC Church Platform

Проект полностью подготовлен для продакшена. Ниже представлены варианты развертывания от самого простого (облачный хостинг в 3 клика) до классического VPS сервера.

---

## Вариант 1: Облачный хостинг (Render.com или Railway.app) — Самый простой способ

Подходит для мгновенного запуска прямо из GitHub репозитория без настройки Linux серверов.

### Инструкция для Render.com:
1. Зайдите на [Render.com](https://render.com/) и авторизуйтесь через свой GitHub (`sigmachyo`).
2. Нажмите **New +** → **Web Service**.
3. Выберите репозиторий `sigmachyo/CLC`.
4. Задайте настройки:
   - **Name**: `kclc`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn kclc.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 120`
5. В разделе **Environment Variables** добавьте переменные из файла `.env.example`:
   - `DJANGO_SECRET_KEY` = *ваш сгенерированный секретный ключ*
   - `DJANGO_DEBUG` = `False`
   - `DJANGO_ALLOWED_HOSTS` = `.onrender.com,ваш_домен.ru`
   - `CSRF_TRUSTED_ORIGINS` = `https://ваш-проект.onrender.com,https://ваш_домен.ru`
   - `SECURE_SSL_REDIRECT` = `True`
   - `EMAIL_HOST_PASSWORD` = *пароль приложения bot.kclc@mail.ru*
6. *(Опционально)*: Если хотите PostgreSQL вместо SQLite, в Render нажмите **New +** → **PostgreSQL Database** и скопируйте `Internal Database URL` в переменную `DATABASE_URL` веб-сервиса.
7. Нажмите **Deploy Web Service**. Через 2 минуты сайт будет доступен в интернете с автоматическим бесплатным SSL-сертификатом!

---

## Вариант 2: Запуск на VPS через Docker Compose (Рекомендуемый для собственного сервера)

Если у вас есть виртуальный сервер (Timeweb Cloud, Beget, Selectel, Hetzner, Ubuntu 22.04/24.04):

1. **Клонируйте репозиторий на сервер**:
   ```bash
   git clone https://github.com/sigmachyo/CLC.git /opt/kclc
   cd /opt/kclc
   ```

2. **Создайте боевой файл окружения**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Укажите ваш реальный домен в `DJANGO_ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`, задайте пароль для базы данных и почты.

3. **Запустите проект в одну команду**:
   ```bash
   docker compose up -d --build
   ```

4. **Создайте суперпользователя (администратора)**:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

Сайт поднимется на порту `8000` в изолированных контейнерах (Django Gunicorn + PostgreSQL 16), статические файлы отдаются сжатыми через WhiteNoise, база сохраняется в защищенный docker volume.

---

## Вариант 3: Запуск на VPS без Docker (Systemd + Gunicorn + Nginx)

1. **Установите системные пакеты**:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
   ```

2. **Настройте виртуальное окружение**:
   ```bash
   git clone https://github.com/sigmachyo/CLC.git /var/www/kclc
   cd /var/www/kclc
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

3. **Настройте службу Systemd для Gunicorn**:
   Создайте файл `/etc/systemd/system/kclc.service`:
   ```ini
   [Unit]
   Description=Gunicorn daemon for KCLC Church Platform
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/kclc
   ExecStart=/var/www/kclc/venv/bin/gunicorn \
             --workers 3 \
             --threads 2 \
             --bind 127.0.0.1:8000 \
             --timeout 120 \
             kclc.wsgi:application
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   Включите и запустите сервис:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now kclc
   ```

4. **Настройте Nginx**:
   Скопируйте `nginx.conf.example` в `/etc/nginx/sites-available/kclc.conf`, замените домен на ваш и активируйте:
   ```bash
   sudo ln -s /etc/nginx/sites-available/kclc.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d kclc.ru -d www.kclc.ru
   ```

---

## 🔒 Безопасность и оптимизация, которые уже включены:
- **WhiteNoise (Brotli + Gzip)**: мгновенная отдача всей статики с заголовками кеширования на 1 год (`max-age=31536000`).
- **Referrer-Policy: strict-origin-when-cross-origin**: полное устранение ошибки 153 YouTube в соответствии с требованиями Google API.
- **SSL / HSTS**: защита от перехвата трафика и подмены запросов.
- **CSRF & XSS защита**: безопасные HTTP-only cookies, защита от межсайтовых атак.
- **Защита от сбоев БД**: пул соединений (`conn_max_age=600`) с автоматической проверкой работоспособности коннекта.
