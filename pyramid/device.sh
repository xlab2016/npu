#!/bin/bash
# Адаптер GERON для нейропроцессора. Настройки в device.conf: REPO BRANCH REMOTE CLONE_URL BUILD_TARGET CONFIG APPHOST RESOURCE HEALTH_URL
set -u
cd "$(dirname "$0")"; . "${NPU_DEVICE_CONF:-./device.conf}"
: "${DOTNET:=dotnet}" "${ASPIRE:=aspire}" "${REMOTE:=origin}" "${BRANCH:=main}" "${CONFIG:=Release}"
g() { git -C "$REPO" "$@"; }
aspire_state() { "$ASPIRE" describe "$RESOURCE" --format Json --apphost "$APPHOST" --non-interactive 2>/dev/null; }
observe() {
  if [ ! -d "$REPO/.git" ]; then echo REPOSITORY_MISSING; [ -n "${CLONE_URL:-}" ] && echo CLONE_CONFIGURED || echo "BLOCK репозиторий отсутствует и CLONE_URL не задан"; else
    echo REPOSITORY_EXISTS
    [ "$(g rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] && echo ON_TARGET_BRANCH || echo "BLOCK ветка не $BRANCH"
    merge=0; [ -f "$REPO/.git/MERGE_HEAD" ] && merge=1
    if [ -z "$(g status --porcelain)" ]; then echo WORKTREE_CLEAN; else echo WORKTREE_DIRTY; [ $merge = 0 ] && echo "BLOCK рабочая копия содержит локальные изменения"; fi
    if [ $merge = 1 ]; then echo MERGE_IN_PROGRESS; if [ -z "$(g diff --name-only --diff-filter=U)" ] && [ -z "$(g diff --name-only)" ]; then echo MERGE_READY_TO_COMMIT; echo MERGE_COMPLETION_ALLOWED; else echo "BLOCK слияние нельзя завершить автоматически"; fi; fi
    if g fetch -q "$REMOTE" "$BRANCH" 2>/dev/null; then
      read -r ahead behind < <(g rev-list --left-right --count HEAD...FETCH_HEAD | tr '\t' ' ')
      [ $merge = 0 ] && echo GIT_PULL_REQUIRED
      [ "$behind" -gt 0 ] && [ "$ahead" = 0 ] && echo GIT_UPDATE_REQUIRED
      [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ] && [ $merge = 0 ] && echo GIT_DIVERGED
    else echo "BLOCK удалённая ветка недоступна"; fi
  fi
  [ -z "${APPHOST:-}" ] && echo "BLOCK AppHost не настроен"
  st=$(aspire_state) || { echo "BLOCK Aspire CLI недоступен или ресурс не найден"; }
  case "${st:-}" in *Running*) echo ASPIRE_RUNNING;; *Starting*) echo SERVICE_STARTING;; *) echo ASPIRE_STOPPED;; esac
  echo NO_OPERATION_ERROR
}
fail() { echo "$1"; exit 1; }
run() { case "$1" in
  GIT_CLONE) git clone -q -b "$BRANCH" "$CLONE_URL" "$REPO" || fail ERROR:GIT_NETWORK;;
  GIT_PULL_MAIN) g fetch -q "$REMOTE" "$BRANCH" || fail ERROR:GIT_NETWORK; g merge -q --no-edit FETCH_HEAD || { g diff --name-only --diff-filter=U | grep -q . && fail ERROR:GIT_MERGE_CONFLICT; fail ERROR:GIT_DIVERGED; };;
  GIT_COMPLETE_MERGE) g commit -q --no-edit || fail ERROR:GIT_MERGE_NOT_READY;;
  ASPIRE_STOP) "$ASPIRE" resource "$RESOURCE" stop --apphost "$APPHOST";;
  DOTNET_CLEAN) "$DOTNET" clean "$BUILD_TARGET" -c "$CONFIG" -v q;;
  DOTNET_RESTORE) "$DOTNET" restore "$BUILD_TARGET" -v q;;
  DOTNET_BUILD) "$DOTNET" build "$BUILD_TARGET" -c "$CONFIG" --no-restore -v q;;
  ASPIRE_START) "$ASPIRE" resource "$RESOURCE" start --apphost "$APPHOST";;
  WAIT_SERVICE_READY) for i in $(seq 1 "${READY_TRIES:-90}"); do aspire_state | grep -q Running && exit 0; sleep "${READY_SLEEP:-1}"; done; exit 1;;
  HEALTH_CHECK) for i in $(seq 1 "${HEALTH_TRIES:-30}"); do curl -fsS -o /dev/null "$HEALTH_URL" && exit 0; sleep "${READY_SLEEP:-1}"; done; exit 1;;
  WAIT_NETWORK) sleep "${NETWORK_WAIT:-5}";;
  *) echo "неизвестная операция $1"; exit 2;;
 esac; }
case "$1" in observe) observe;; run) run "$2";; esac
