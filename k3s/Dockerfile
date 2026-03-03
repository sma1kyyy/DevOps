from python:3.12-slim

# ➜ добавлены build-essential, чтобы собрать uWSGI
run apt-get update \
    && apt-get install -y --no-install-recommends \
    nginx \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

workdir /app

copy requirements.txt ./
run pip install --no-cache-dir -r requiremenets.txt

copy app ./app
copy wsgi.py ./
copy uwsgi.ini ./
copy nginx/default.conf /etc/nginx/conf.d/default.conf
copy entrypoint.sh /entrypoint.sh

run chmod +x /entrypoint.sh

expose 80

cmd ["/entrypoint.sh"]