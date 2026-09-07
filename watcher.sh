#!/bin/sh
set -eu

send_message() {
  msg="$1"
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
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

# Слушаем "die" (остановка/падение) и "start" (запуск/восстановление)
# shellcheck disable=SC2086
docker events --filter 'event=die' --filter 'event=start' $FILTERS \
  --format '{{.Status}}|{{.Actor.Attributes.name}}|{{.Actor.Attributes.exitCode}}' |
while IFS='|' read -r status name exit_code; do
  case "$status" in
    start)
      send_message "🟢 Контейнер ${name} запущен"
      ;;
    die)
      if [ "$exit_code" = "0" ]; then
        send_message "🟡 Контейнер ${name} остановлен штатно (exit code 0)"
      else
        send_message "🔴 Контейнер ${name} упал! Exit code: ${exit_code}"
      fi
      ;;
  esac
done
