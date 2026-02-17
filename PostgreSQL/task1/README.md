<!-- выполнение задачи 1 для первой виртуальной машины как primary сервера -->

## ТЗ: 

- установить postgresql
- Руками проинициализировать инстанс БД с данными в папке /pg_data/16/

   На Первой виртуалке
    1. Создать отдельного пользователя pgbench с правами на database bench
    2. подключить несколько модулей https://postgrespro.ru/docs/postgrespro/18/installing-additional-modules
    3. настроить логирование всех запросов
    4. c помощью утилиты pgbench проведите нагрузочное тестирование на базку
    5. После завершения нагрузочного тестирования, получите список самых ресурсоемких по IO time write и самых длительных запросов (execution time) из представления pg_stat_statements
    6. логах показать что делал pg_bench

    7. Создать пользователя для репликации
    8. Настроить доступы пользователю чтобы с другой виртуалки можно было подключиться

## 1 подготовка через ansible

## перед запуском нужно скорректировать ip адреса в inventory
```bash
# запускаем playbook подготовки primary
ansible-playbook -i inventory.ini main.yaml
```

## 2. ручная инициализация кластера в `/pg_data/16` (я сделал его еще в task0)

# этот шаг делается вручную по тз
```bash
# создаем каталог данных и права
sudo mkdir -p /pg_data/16
sudo chown postgres:postgres /pg_data/16
sudo chmod 700 /pg_data/16

# инициализируем кластер
sudo -u postgres /usr/lib/postgresql/16/bin/initdb -D /pg_data/16 --locale=C --encoding=UTF8

# запускаем кластер напрямую через pg_ctl
sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl -D /pg_data/16 -l /var/log/postgresql/postgresql-16-manual.log start
```

## 3 создание базы, роли и расширений

## все sql команды выполняются под postgres
```sql
-- коннект
sudo -u postgres psql -d postgres

-- создаем базу для теста
create database bench;

-- создаем пользователя для pgbench
create role pgbench login password 'StrongPgbenchPass_2026';

-- даем права на базу
grant all privileges on database bench to pgbench;

-- подключаемся к базе bench
\c bench

-- подключаем расширение для статистики запросов
create extension if not exists pg_stat_statements;

-- подключаем расширение для удобной диагностики блокировок
create extension if not exists pgrowlocks;
```
## 4 настройка конфига postgresql  и pg_hba 

## вносим ключевые параметры для логирования, статистики и репликации
```conf
# включаем сбор статистики для pg stat  satement
shared_preload_libraries = 'pg_stat_statements'

# включаем логирование всех запросов
log_statement = 'all'

# полезный префикс для анализа лога
log_line_prefix = '%m [%p] %u@%d %r '

# параметры для физической и логической репликации (должны помнить с пары)
wal_level = logical # сегодня роберт любимый рассказывал # я гей
max_wal_senders = 10 
max_replication_slots = 10
listen_addresses = '*'
```

```conf
# разрешаем подключение пользователя репликации со второй виртуалки
host replication repl_user 89.169.182.136/32 scram-sha-256

# разрешаем рабочее подключение пользователя pgbench со второй виртуалки
host bench pgbench 89.169.182.136/32 scram-sha-256
```
## 5 запуск pgbench и проверка логов

## для начала инициализируем схему ауже затем запускаем тест
```bash
# инициализация тестовой схемы
PGPASSWORD='StrongPgbenchPass_2026' pgbench -i -h 127.0.0.1 -U pgbench -d bench

# нагрузка 3 минуты, 10 клиентов, 4 потока
PGPASSWORD='StrongPgbenchPass_2026' pgbench -h 127.0.0.1 -U pgbench -d bench -c 10 -j 4 -T 180

# проверяем, что в логе есть операции pgbench
sudo grep -n "pgbench" /var/log/postgresql/postgresql-16-manual.log | tail -n 20
```

после инициализации схемы и нагрузки, при которой у многих припотели попки и они в ужасе ждали, когда тестирование закончится, проверяем логи
вот для начала скрин после нагрузки 
![alt text](image.png)
474 tps при 10 клиентах... (транзакицйи в секунду при 10 пользователях) как по мне хороший результат для ВМ за копейки. лееетс го дальше

вот скрин логов
![alt text](image-1.png)

как мы видим, pgbench создает таблицы от имени postgres, но потом идет запуск от пользователя pgbench у которого нет прав  

в таком случае просто покдлючаемся как постгрес 
```sql
# делаем его владельцем
postgres=# ALTER DATABASE bench OWNER TO pgbench;
ALTER DATABASE
# полнвые права на схему 
postgres=# GRANT ALL PRIVILEGES ON DATABASE bench TO pgbench;
GRANT
postgres=# GRANT ALL ON SCHEMA public TO pgbench;
GRANT
postgres=# GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pgbench;
GRANT
postgres=# GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pgbench;
GRANT
# попытки перенести таблицы, но анлак, т.к постгрес суперпользователь системы и постгря так сказать защищает его права
postgres=# REASSIGN OWNED BY postgres TO pgbench;
ERROR:  cannot reassign ownership of objects owned by role postgres because they are required by the database system
postgres=# \dt pgbench_*
Did not find any relation named "pgbench_*".
postgres=# PGPASSWORD='StrongPgbenchPass_2026' pgbench -i -h 127.0.0.1 -U pgbench -d bench

# sudo -u postgres psql -d bench -c "\dt pgbench_*" # проверяем созданные таблицы 

```
опять:
# нагрузка
PGPASSWORD='StrongPgbenchPass_2026' pgbench -h 127.0.0.1 -U pgbench -d bench -c 10 -j 4 -T 180

# логи
sudo grep -n "pgbench" /var/log/postgresql/postgresql-16-manual.log | tail -n 20

теперь ошибки от неудачных запусков и потому что прав на таблиц нет, но уже лучше
![alt text](image-2.png)

## 6 и самое потное............................................................................................................ это............................................................................... запросы любимые фулл хард сучки потеем

## отчеты по io write time и execution time
```sql
-- топ запросов по суммарному времени записи io
select
    query,
    calls,
    round(total_exec_time::numeric,2) as total_ms
from pg_stat_statements
order by total_exec_time desc
limit 10;


-- топ запросов по средеему времени на запрос
select
    query,
    calls,
    round(mean_exec_time::numeric,2) as avg_ms
from pg_stat_statements
order by mean_exec_time desc
limit 10;

```

вот скрины запросов 
# среднее время на запрос
![alt text](image-3.png)

# суммарное время
![alt text](image-4.png)

## 7 создание пользователя репликации

## пользователь нужен для pg_basebackup и потока wal
```sql
create role repl_user with replication login password 'StrongReplPass_2026';
```
### итоги епт

- primary сервер поднят из ручного `initdb` в `/pg_data/16`
- база `bench`, роль `pgbench` и расширения созданы
- логирование всех запросов включено
- нагрузка `pgbench` проведена и видна в логах
- отчеты из `pg_stat_statements` подготовлены
- роль `repl_user` создана и доступы для второй vm настроены
