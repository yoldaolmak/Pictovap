#!/bin/zsh
set -euo pipefail

BASE_DIR="/Users/KemalKaya/YO_OS_VIL"
LOG_DIR="$BASE_DIR/ops_logs"
STATE_DIR="$BASE_DIR/data"
PHASE_FILE="$STATE_DIR/full_index_phase.txt"
PID_FILE="$STATE_DIR/full_index_auto.pid"
RUN_LOG="$LOG_DIR/full_index_auto.log"
HDD_LOG="$LOG_DIR/hdd_index_run.log"
PHOTOS_LOG="$LOG_DIR/photos_index_run.log"

mkdir -p "$LOG_DIR" "$STATE_DIR"

echo $$ > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT INT TERM

if [[ ! -f "$PHASE_FILE" ]]; then
  echo "hdd" > "$PHASE_FILE"
fi

log(){
  echo "$(date '+%F %T') $1" | tee -a "$RUN_LOG"
}

run_phase(){
  local phase="$1"
  if [[ "$phase" == "hdd" ]]; then
    log "start phase=hdd"
    (
      cd "$BASE_DIR"
      PYTHONPATH="$BASE_DIR" python3 -u "$BASE_DIR/index_memory_daily.py" \
        --mode hdd \
        --external-root "/Volumes/LaCie Travel" \
        --daily-limit 0 \
        --best-limit 1 \
        --batch-size 200 \
        --progress-interval 500 \
        --min-quality 0.60 \
        --min-selection 0.55 \
        --min-pixels 600000 \
        --report-sample 30
    ) >> "$HDD_LOG" 2>&1
    log "done phase=hdd"
    echo "photos" > "$PHASE_FILE"
    return 0
  fi
  if [[ "$phase" == "photos" ]]; then
    log "start phase=photos"
    (
      cd "$BASE_DIR"
      PYTHONPATH="$BASE_DIR" python3 -u "$BASE_DIR/index_memory_daily.py" \
        --mode photos \
        --daily-limit 0 \
        --best-limit 1 \
        --batch-size 200 \
        --progress-interval 500 \
        --min-quality 0.60 \
        --min-selection 0.55 \
        --min-pixels 600000 \
        --report-sample 30
    ) >> "$PHOTOS_LOG" 2>&1
    log "done phase=photos"
    echo "done" > "$PHASE_FILE"
    return 0
  fi
  return 0
}

log "auto-run started"
while true; do
  phase="$(cat "$PHASE_FILE" 2>/dev/null || echo hdd)"
  if [[ "$phase" == "done" ]]; then
    log "all done"
    exit 0
  fi
  if run_phase "$phase"; then
    continue
  fi
  log "phase=$phase failed, retry in 1800s"
  sleep 1800
done
