# Используем официальный образ Python в качестве базового
FROM python:3.13.6-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /code

# Устанавливаем необходимые инструменты для сборки и Poetry
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Добавляем путь к Poetry в PATH
ENV PATH="/root/.local/bin:$PATH"

# Копируем только файлы pyproject.toml и poetry.lock для кэширования зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости (без dev-зависимостей) и отключаем создание virtualenv
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

# Копируем остальной код приложения
COPY . .

# Определяем переменные окружения
ENV DJANGO_SETTINGS_MODULE=config.settings

# Создаем директорию для медиафайлов
RUN mkdir -p /code/media

# Пробрасываем порт, который будет использовать Django
EXPOSE 8000

# Команда для запуска приложения (замените runserver на ваш production сервер)
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--settings=config.settings"]
