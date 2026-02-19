<!-- CRUD на Flask -->

# Django когда-нибудь потом, ес ср.

## ТЗ

- Написать CRUD приложение на Flask  (если вдруг кто умеет на Django тоже можно)
- Что это значит
1. У вас должна быть поднята база данных (postgres) с данными внутри
2. Приложение должно уметь выполнять CRUD операции над этими данными
3. Приложение должно запускаться через uwsgi/gunicorn
4. Над приложением должен быть nginx который проксирует запросы пользоватлей в ваш back
5. Настроить кеширование запросов на стороне:
• nginx
• redis
Все должно запускаться в docker
—— Кому мало
1. Настроить кеширование запросов с nginx в redis

Пример и дока тут:
1. https://github.com/bob4inski/admin-starterpack/tree/main/full-course/week-2/mini-flask

## источники для работы

в первую очередь гит роберто с мини примером
-  https://github.com/bob4inski/admin-starterpack/tree/main/full-course/week-2/mini-flask
  далее уже 
- официальный flask patterns https://flask.palletsprojects.com/en/stable/patterns/ (application factory, blueprints)
- официальный sqlalchemy + flask-sqlalchemy подход https://flask.palletsprojects.com/en/stable/patterns/sqlalchemy/ и https://flask-russian-docs.readthedocs.io/ru/0.10.1/patterns/sqlalchemy.html
- официальный gunicorn deployment flow https://reharish.medium.com/deploying-flask-using-gunicorn-b0c0e8a58e07 и https://flask.palletsprojects.com/en/stable/deploying/gunicorn/

---

## архитектура

```text
чел -> nginx:80 -> gunicorn(flask app):8000 -> постгря
                          |
                          -> redis (кеш /api/tasks)
```
## почему так (для тех, кто не был на паре и в целом не знает базы, по типу вида кеширования nginx, архитектуры rest/soap и прочее)
- flask app отделен от infra, ну просто для удосбтва
- gunicorn нужен как wsgi сервер, он отлично работает в связке с nginx
- nginx отвечает за входящий трафик и micro-cache
- redis хранит кеш ответа списка задач на уровне приложения
- ну и compose для поднятия всего одной командой

# я решил реализовать дерево проекта так:

```text
 @kirill  tree -h
[4.0K]  .
├── [4.0K]  app
│   ├── [   0]  cache.py
│   ├── [   0]  config.py
│   ├── [   0]  extensions.py
│   ├── [   0]  __init__.py
│   ├── [   0]  models.py
│   └── [   0]  routes.py
├── [   0]  docker-compose.yaml
├── [   0]  Dockerfile
├── [4.0K]  nginx
│   └── [   0]  default.conf
├── [1.1K]  README.md
├── [   0]  requirements.txt
├── [4.0K]  tests
│   ├── [   0]  conftest.py
│   └── [   0]  test_tasks_api.py
└── [   0]  wsgi.py

4 directories, 14 files
```

# вм для запуска

как и в прошлой работе я буду использовать арендованную вм на яндекс клауде

- vm1: `178.154.199.20`, debian 11, 2 vcpu, 1 gb ram, 10 gb hdd


## океееей, леттс гооо

# 1 docker + compose plugin 
задаемся вопросом, а как нам поставить докер + композ плагин на вм?
ответ:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

надо еще ребутнутся потом, чтобы docker без sudo запускался

# 2 папка проекта

```bash
cd Flask
```

должны быть здесь

# 3 поднятие всего стенда

```bash
docker compose up --build -d
```

# 4 проверка здоровья у нашего братика 

``` bash
curl http://localhost/api/health
```

ожидаемый ответ в виде статуса: ок

---

## CRUD поинты

# создаю задачу

```bash
curl -X POST http://localhost/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"сделать дз","description":"проверить все пункты"}'
```

# получить список задач 

```bash
curl http://localhost/api/tasks
```
в ответе будет source и тут надо различать, если будет postgres - список прочитался из бд, если будет redis-cache - список пришел из redis

# получаем задачу id

```bash
curl http://localhost/api/tasks/1
```

# обновить задачу

```bash
curl -X  PUT http://localhost/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"title": "flask task", "is done": "true"}'
```

# удалить задачу 

```bash
curl -X DELETE http://localhost/api/tasks/1
```

---

## как работает кеш

- поинт на '/api/tasks' сначала смотрит ключ 'tasks:list' в redis 
- если ключа нет, читаем postgres, перебираем и кладем в redis с ttl 
- при add/update/delete кеш инвалидируется 

# nginx кеш 

- в `nginx/default.conf` включен `proxy_cache`
- кешуиреются только `GET/HEAD`
- в ответ добавляется `X-Nginx-Cache: HIT|MISS|BYPASS` 
- 
---

## тестирование

локально:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requiremenets.txt
pytest -q
```

# выполнено:

- сценарий CRUD
- проверка что второй `GET /api/tasks` отдается уже из кеша
  
---

# итоги епт
