# базовый образ
FROM python:3.12-slim

# рабочая директория
WORKDIR /app

# копируем файл зависимостей заранее для кеша
COPY requiremenets.txt . 

# ставим зависимости
RUN pip install --no-cache-dir -r requiremenets.txt

# копируем исходники
COPY . . 

# порт приложения
EXPOSE 8000

# запуск gunicorn с 2 воркерами
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "wsgi:app"]

