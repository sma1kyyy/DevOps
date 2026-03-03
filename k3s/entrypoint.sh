#!/usr/bin/env sh
set -e

uwsgi --ini /app/uwsgi.ini &
exec nginx -g 'daemon off;'
