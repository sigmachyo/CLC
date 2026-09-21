# ==============================================================================
# Production Dockerfile for KCLC Church Platform
# ==============================================================================
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Установка системных зависимостей для сборки psycopg2, Pillow, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY . .

# Создание директорий для статики и медиа
RUN mkdir -p /app/staticfiles /app/media

# Создание непривилегированного пользователя appuser для безопасности
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Сборка статических файлов через WhiteNoise
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Запуск продакшен-сервера Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn kclc.wsgi:application --bind 0.0.0.0:${PORT} --workers 3 --threads 2 --timeout 120 --access-logfile - --error-logfile -"]
