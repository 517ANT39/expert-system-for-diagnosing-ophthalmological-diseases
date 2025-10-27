FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости, включая необходимые для WeasyPrint
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    libpq-dev \
    gcc \
    python3-dev \
    # Зависимости для WeasyPrint
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    libgirepository-1.0-1 \
    gir1.2-pango-1.0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY . .

ENTRYPOINT ["bash","docker-entrypoint.sh"]