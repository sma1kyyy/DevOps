<!-- Prometheus & Grafana на Flask -->

## ТЗ

Задание: у вас есть после 5 лабы приложение на flask которое работает с БД
Теперь вам необходимо соорудить у себя мониторинг этого сервиса

Что конкретно необходимо:
1. Поднять ваше приложение внутри docker 
2. Рядом написать compose внутри которого будет prometheus + grafana (данные должны сохранятся после up/down)
3. Почитать про prometheus-node-exporter 
https://prometheus.io/docs/guides/node-exporter/
https://hub.docker.com/r/prom/node-exporter

4. Подключить Node exporter к прометеусу и внутри prometheus сделать один-два запроса чтобы научитсья работать с ним (построить график потребляния RAM)
5. Подключить данные из prometheus в графану
6. Повторить П3-5 для nginx и postgresql (как научить nginx отдавать метрики - загуглите)
7. С помощью wrk "пострелять в свой сервис" и понять при каком RPS он начинает отказывать 

DOD (что есть выполненная работа):
Формат сдачи: физически очно показываете лабу

1. nginx вашего сервиса умеет отдавать метрики
2. В prometheus есть данные по хосту, nginx, базке
3. Сделаны дашборды в grafana по каждому кусочку сервиса (бд, хост, вебка)
4. На графиках можно явно увидеть что происходит не так

## источники для работы
- https://prometheus.io/docs/guides/node-exporter/
- https://hub.docker.com/r/prom/node-exporter
- https://medium.com/@MetricFire/use-grafana-to-monitor-flask-apps-with-prometheus-d687d6fdd799
- https://pypi.org/project/prometheus-flask-exporter/ (удобная бибилотека экспортера flask, имеет встроенные метрики `flask_http_request_duration_seconds`, `flask_http_request_total`) 

### погна с описания работы

1. я оставил flask с 5 задания просто скопировав папку и создав новую, под новый таск
2. в compose оставил volume postgres_data, чтобы данные не терялись при down/up
3. также оставил volume nginx_cache, чтобы кеш reserve proxy жил отдельно своей жизнью 

по факту код можно пересобрать, а данные будут дальше жить в именнованых томах

### добавление prometheus & grafana с сохранением данных 

1. в compose добавил сервис prometheus и подключил ему конфиг файл из prometheus/prometheus.yaml
2. подключил volume prometheus_data для хранения tsdb (временные ряды бдшки)
3. также добавил сервис grafana и подключил volume grafana_data для сохранения всяких дашбордов и ручных настроек
4. для входа задал admin admin через переменные окружения grafana  
 
теперь и метрик prometheus & дашборды grafana не будут пропадать при down/up

### метрики flask

1. в зависимостях добавляю библиотеку `prometheus-flask-exporter==0.23.2` (ссылку на источник прикрепил выше)
2. в инициализации flask app подключил PrometheusMetrics и эндпоинт ручки /metrics
3. в prometheus добавил job flask_app и указал путь до ручки /metrics
   
теперь можно будет видеть технические метрики веб прилоежния и можно строить дашборды веб части

### метрики хоста через node_exporter
1. в compose добавил сервис node_exporter
2. подключил монтирование хоста в режиме readonly через path.rootfs (как в примере доки)
3. в prometheus добавоил job node_exporter 
   
теперь можно будеть видеть cpu ram disk network метрики хоста, в том числе для графика по памяти 

примеры запросов:

1. node_memory_memavailable_bytes (доступная память)
2. 100 * (1 - (node_memory_memavailable_bytes / node_memory_memtotal_bytes)) (процент занятой памяти)

### метрики nginx

1. в nginx/default.conf добавли location /nginx_status с stub_status (базовая статистика о состоянии сервера, по типу кол-во активных соединений, запросов и кол-во принятых и обработанных коннектов)
2. в compose добавил сервис nginx_exporter
3. exporter настроил на чтение http://nginx/nginx_status
4. и в prometheus добавил job nginx_exporter
   
теперь получаем метрики активных соединений, обработанных запросов, общее состояние nginx 

### метрики постгря

1. добавил в compose сервис postgres_exporter
2. передал в него data source строку подключения к контейнеру db 
3. в prometheus добавил job postgres_exporter

теперь в графане можно будет анализировать нагрузку на базку, кол-во запросов, размеры таблицы, состояние коннектов и тд

### проверка и запуск

сначала билдим
`docker compose up --build -d`

после проверяем контейнеры 
`docker compose ps`

теперь надо глянуть prometheus на порту 9090

после графана на порту 3000

в prometheus:

1. раздел targets, все jobы должны быть подняты
2. запрос по node_exporter для памяти
3. глянуть метрики nginx_exporter и postgres_exporter

в grafana:

1. добавление источника метрик/данных prometheus url `http://prometheus:9090`
2. создать дашборды (по ТЗ бд, хост, вебка)
   - дашборд nginx по nginx_exporter
   - дашборд хоста по node_exporter
   - дашборд базы по postgres_exporter
   - дашборд вебки пот метрикам flask

### нагрузочный тест

нагрузочное тестирование по ТЗ будет через wrk (утилита для нагрузочного тестирования HTTP серверов)

-  wrk -t4 -c100 -d30s http://localhost/api/tasks
тут -t4 это кол-во потоков (threads) генерации нагрузки
а -c100 кол-во одновременно открытых соединений (connections) и эти 100 коннектов будут распределять между 4 потоками 
-d30s длительность теста 
в течение 30 секунд wrk будет слать запросы и собирать стату 

- постепенно можно увеличивать потоки и соединения 
- параллельно чек графиков в графане и запросов в прометеусе 

как зафиксировать момент отказа:
- рост latency и timeout
- падение rps при росте
- появление 500 ошибок в nginx или приложении
- рост утиля cpu и памяти до их пределов

### dod

по итогу 

- nginx отдает метрики через /nginx_status и их читает exporter
- в prometheus есть данные по хосту nginx и postgresql 
- в grafana можно отдельно собрать дашборды по хосту, вебке и базе
- на графиках можно наблюдать тестирование при wrk нагрузке
  
для быстрого повтора:
docker compose up --build -d
docker compose ps
docker compose logs -f prometheus
docker compose logs -f grafana 
docker compose down

если надо оставить данные, но удалить контейнеры, то юзайте docker compose down, если хотите еще и данные удалить, то docker compose down -v 



