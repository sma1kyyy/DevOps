#!/bin/bash
set -e
mkdir -p /tmp && chmod 777 /tmp

# 1. uWSGI ПЕРВЫМ
uwsgi --ini uwsgi.ini &
sleep 3

# 2. Nginx ПОТОМ  
nginx
wait
