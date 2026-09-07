#!/bin/sh
set -eu

send_message() {
  msg="$1"
  curl -s -X POST "https://api.telegram.org/bot${8986607750:AAEiDZpc-b4XztkYKEJ5Qi93K55oFuRt-Bo}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="${msg}" > /dev/null
}

send_message "🟢 Watcher запущен, слежу за: ${WATCH_CONTAINERS}"

# Собираем --filter container=... для каждого имени из WATCH_CONTAINERS (через запятую)
FILTERS=""
OLD_IFS="$IFS"
IFS=','
for name in $WATCH_CONTAINERS; do
  FILTERS="$FILTERS --filter container=$name"
done
IFS="$OLD_IFS"

# Слушаем событие "die" — оно срабатывает и при docker stop, и при падении/крэше
# shellcheck disable=SC2086
docker events --filter 'event=die' $FILTERS \
  --format '{{.Actor.Attributes.name}}|{{.Actor.Attributes.exitCode}}' |
while IFS='|' read -r name exit_code; do
  if [ "$exit_code" = "0" ]; then
    send_message "🟡 Контейнер ${name} остановлен штатно (exit code 0)"
  else
    send_message "🔴 Контейнер ${name} упал! Exit code: ${exit_code}"
  fi
done
