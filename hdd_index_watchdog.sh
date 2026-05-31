#!/bin/zsh
set -euo pipefail

BASE_DIR="/Users/KemalKaya/YO_OS_VIL"
LOG_DIR="$BASE_DIR/ops_logs"
STATE_DIR="$BASE_DIR/data"
WATCHDOG_PID_FILE="$STATE_DIR/hdd_index_watchdog.pid"
RUN_PID_FILE="$STATE_DIR/hdd_index_runner.pid"
PHASE_FILE="$STATE_DIR/hdd_index_phase.txt"
HDD_LOG="$LOG_DIR/hdd_index_run.log"
PHOTOS_LOG="$LOG_DIR/photos_index_run.log"
WATCHDOG_LOG="$LOG_DIR/index_watchdog.log"

mkdir -p "$LOG_DIR" "$STATE_DIR"

# Tek watchdog instance
if [[ -f "$WATCHDOG_PID_FILE" ]]; then
  old_pid="$(cat "$WATCHDOG_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "$(date '+%F %T') watchdog already running pid=$old_pid" >> "$WATCHDOG_LOG"
    exit 0
  fi
fi

echo $$ > "$WATCHDOG_PID_FILE"
trap 'rm -f "$WATCHDOG_PID_FILE"' EXIT INT TERM

if [[ ! -f "$PHASE_FILE" ]]; then
  echo "hdd" > "$PHASE_FILE"
fi

echo "$(date '+%F %T') watchdog started pid=$$" >> "$WATCHDOG_LOG"

resolve_phase() {
  local phase
  phase="$(cat "$PHASE_FILE" 2>/dev/null || true)"
  case "$phase" in
    hdd|photos|done) echo "$phase" ;;
    *) echo "hdd" ;;
  esac
}

find_existing_pid_for_phase() {
  local phase="$1"
  local pattern=""
  if [[ "$phase" == "hdd" ]]; then
    pattern="index_memory_daily.py --mode hdd --external-root /Volumes/LaCie Travel"
  elif [[ "$phase" == "photos" ]]; then
    pattern="index_memory_daily.py --mode photos"
  else
    return 0
  fi
  ps aux | grep "$pattern" | grep -v grep | awk '{print $2}' | head -n 1 || true
}

hdd_is_mounted() {
  [[ -d "/Volumes/LaCie Travel" ]] && [[ -n "$(ls -A '/Volumes/LaCie Travel' 2>/dev/null)" ]]
}

start_indexer() {
  local phase="$1"
  local run_log="$HDD_LOG"
  local cmd=()

  if [[ "$phase" == "hdd" ]]; then
    if ! hdd_is_mounted; then
      echo "$(date '+%F %T') LaCie not mounted, skipping hdd phase" >> "$WATCHDOG_LOG"
      return 1
    fi
    cmd=(
      command python3 -u "$BASE_DIR/index_memory_daily.py"
      --mode hdd
      --external-root "/Volumes/LaCie Travel"
      --daily-limit 0
      --best-limit 1
      --batch-size 200
      --progress-interval 500
      --min-quality 0.60
      --min-selection 0.55
      --min-pixels 600000
      --report-sample 30
    )
    run_log="$HDD_LOG"
  elif [[ "$phase" == "photos" ]]; then
    cmd=(
      command python3 -u "$BASE_DIR/index_memory_daily.py"
      --mode photos
      --daily-limit 0
      --best-limit 1
      --batch-size 200
      --progress-interval 500
      --min-quality 0.60
      --min-selection 0.55
      --min-pixels 600000
      --report-sample 30
    )
    run_log="$PHOTOS_LOG"
  else
    return 0
  fi

  echo "$(date '+%F %T') starting phase=$phase" >> "$WATCHDOG_LOG"
  (
    cd "$BASE_DIR"
    PYTHONPATH="$BASE_DIR" "${cmd[@]}" >> "$run_log" 2>&1
    exit_code=$?
    if [[ "$exit_code" -eq 0 ]]; then
      if [[ "$phase" == "hdd" ]]; then
        echo "photos" > "$PHASE_FILE"
      else
        echo "done" > "$PHASE_FILE"
      fi
    fi
    echo "$(date '+%F %T') phase=$phase finished exit=$exit_code next=$(cat "$PHASE_FILE" 2>/dev/null || echo "$phase")" >> "$WATCHDOG_LOG"
  ) &
  echo $! > "$RUN_PID_FILE"
  echo "$(date '+%F %T') phase=$phase pid=$(cat "$RUN_PID_FILE")" >> "$WATCHDOG_LOG"
}

while true; do
  phase="$(resolve_phase)"
  running_pid=""
  if [[ -f "$RUN_PID_FILE" ]]; then
    running_pid="$(cat "$RUN_PID_FILE" 2>/dev/null || true)"
  fi

  if [[ "$phase" == "done" ]]; then
    echo "$(date '+%F %T') all phases done — next cycle in 6h" >> "$WATCHDOG_LOG"
    sleep 21600
    echo "hdd" > "$PHASE_FILE"
    echo "$(date '+%F %T') phase reset → hdd for next cycle" >> "$WATCHDOG_LOG"
    continue
  fi

  # HDD phase: wait for mount
  if [[ "$phase" == "hdd" ]] && ! hdd_is_mounted; then
    echo "$(date '+%F %T') LaCie not mounted, retry in 60s" >> "$WATCHDOG_LOG"
    sleep 60
    continue
  fi

  if [[ -n "$running_pid" ]] && kill -0 "$running_pid" 2>/dev/null; then
    echo "$(date '+%F %T') phase=$phase alive pid=$running_pid" >> "$WATCHDOG_LOG"
  else
    existing_pid="$(find_existing_pid_for_phase "$phase" || true)"
    if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
      echo "$existing_pid" > "$RUN_PID_FILE"
      echo "$(date '+%F %T') phase=$phase attached existing pid=$existing_pid" >> "$WATCHDOG_LOG"
    else
      start_indexer "$phase" || {
        echo "$(date '+%F %T') phase=$phase failed to start, retry in 120s" >> "$WATCHDOG_LOG"
        sleep 120
        continue
      }
    fi
  fi

  sleep 1800
done
