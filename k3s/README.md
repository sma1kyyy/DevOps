## k8s + flask + nginx + uwsgi + helm + ansible + argocd

# ТЗ 
Домашка: делайн 4 дня
Все делаем с тем же приложением что писали в 5 домашке

1. Настроить uwsgi чтобы слушал unix socket
2. В одном контейнере поднять nginx + uwsgi/gunicorn
3. Запушить все на dockerhub
4. Поднять на виртуалке minicube/k3s через ansible
5. Написать деплоймент для деплоя через kubectl 
6. Написать helm для деплоя приложеньки (полностью с 
7. натыкать тот же helm в argocd

Dod: деплой приложения на новую виртуалку происходит без ручных вмешательств, только через одну команду применения ансибла
*** - если слишком сложно - поднимаем просто flask+nginx
upd: постарайтесь разделить базку, мониторинг и приложение на разные helm чарты чтобы в argocd у вас все было логично разделено на несколько helm чартов

## что находится в каталоге и для чего это нужно

папка app: это исходный код flask приложения, внутри есть создание приложения, маршруты, модели, подключение к базе и кешу

файл wsgi.py: это точка входа для uwsgi, uwsgi поднимает flask приложение именно через этот файл

файл Dockerfile: инструкция сборки образа приложения, в образ ставятся python и nginx, потом копируется код и конфиги, дальше контейнер запускается через entrypoint.sh

файл uwsgi.ini: конфиг uwsgi, главная идея в том что uwsgi слушает unix socket /tmp/uwsgi.sock ```именно это требование задания```

файл nginx/default.conf: конфиг nginx, nginx слушает 80 порт и передает запросы в uwsgi socket

файл entrypoint.sh: стартовый скрипт контейнера, он запускает uwsgi и потом запускает nginx в foreground

файл docker-compose.yaml: локальный стенд, он поднимает postgresql redis и контейнер приложения, через этот файл удобно быстро проверить что все работает до k3s

папка k8s: сырые kubernetes манифесты, они нужны чтобы деплоить напрямую через kubectl, это удобно для базовой диагностики если нужно проверить yaml без helm

папка charts: helm чарты, здесь разделение на три части: chart postgres поднимает базу, chart flask app поднимает приложение и redis, chart monitoring поднимает prometheus и grafana, такое разделение удобно в argocd потому что каждый блок живет отдельно

папка ansible: автоматизация для новой виртуалки, playbook ставит k3s, ставит helm и деплоит три chart

папка argocd: манифесты application для gitops, после применения argocd сам следит за состоянием и синхронизирует изменения из репозитория

## как запускать локально и что проверять

шаг 1
перейти в папку проекта
cd k3s

шаг 2
поднять локальный стенд
docker compose up -d --build

шаг 3
проверить что контейнеры живые
docker compose ps

шаг 4
проверить health
curl http://127.0.0.1:8080/api/health
ожидается json со статусом ok

шаг 5
проверить создание задачи
curl -X POST http://127.0.0.1:8080/api/tasks -h 'content-type: application/json' -d '{"title":"первая задача","description":"проверка api"}'

шаг 6
проверить чтение списка
curl http://127.0.0.1:8080/api/tasks

шаг 7
остановить стенд
docker compose down

если нужно удалить том базы
docker compose down -v

## как отправить образ в docker hub

зачем? в k3s узел тянет образ из registry, если образ не загружен в docker hub то будет imagepullbackoff

шаг 1
войти в docker hub
docker login

шаг 2
собрать образ с вашим логином
docker build -t docker.io/логин/flask-k3s:latest .

шаг 3
отправить образ
docker push docker.io/логин/flask-k3s:latest

шаг 4
обновить ссылки на образ
нужно проверить k8s/flask.yaml и charts/flask-app/values.yaml там должен быть ваш repository и ваш tag

---

## как поднять k3s на arch linux если установка через curl зависает

если скрипт k3s через curl завис на скачивании airgap архива можно поставить пакет из aur

yay -s k3s-bin

sudo systemctl enable k3s

sudo systemctl start k3s

mkdir -p ~/.kube

sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config

sudo chown $USER ~/.kube/config

export KUBECONFIG=~/.kube/config

kubectl get nodes

зачем эти команды? они запускают k3s как systemd сервис и настраивают kubeconfig для текущего пользователя, после этого kubectl работает без sudo

## как деплоить сырые yaml через kubectl

шаг 1
создать namespace
kubectl create namespace flask-stack

шаг 2
применить манифесты
kubectl apply -f k8s/

шаг 3
проверка
kubectl get pods -n flask-stack

kubectl get svc -n flask-stack

если видите imagepullbackoff, значит что в k8s/flask.yaml указан несуществующий образ и тогда нужно указать ваш docker hub путь и перезапустить deployment

пример
kubectl set image deployment/flask-app flask-app=docker.io/логин/flask-k3s:latest -n flask-stack
kubectl rollout restart deployment/flask-app -n flask-stack

## как подключить argocd и показать gitops

шаг 1
установить argocd
kubectl create namespace argocd

kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

шаг 2
доступ к web интерфейсу

kubectl port-forward svc/argocd-server -n argocd 8081:443

шаг 3
применить application манифесты проекта

kubectl apply -f argocd/
 
будет по итогу 3 apps: postgres,flask-app,monitoring


