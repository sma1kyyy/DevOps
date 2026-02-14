#!/bin/bash
while sleep 1; do echo -n "$(date +%T) -> "; curl -s -m 2 -o /dev/null -w "кодес: %{http_code}, времес: %{time_total}s\n" https://s3.mdst.yandex.net/ping; done
#while sleep 1; do echo -n "$(date +%T) -> "; curl -s -L -o /dev/null -w "кодес: %{http_code}, времес: %{time_total}s\n" https://ya.ru; done
