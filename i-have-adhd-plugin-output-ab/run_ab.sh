#!/bin/bash
# A/B the i-have-adhd plugin against Claude Code's default output.
#
#   bash run_ab.sh [runs]        # default: 5 runs per case per condition
#
# Writes transcripts/{case}_{condition}_{run}.txt next to this script.
# Run one batch at a time: the condition switch is a global file, so two
# concurrent batches silently corrupt both arms.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUNS="${1:-5}"
FLAG="$HOME/.claude/.i-have-adhd-always"
BAK="$(mktemp -t adhd-flag)"
WORKROOT="$(mktemp -d -t adhd-ab)"
SETTINGS='{"outputStyle":"default","enabledPlugins":{"learning-output-style@claude-plugins-official":false}}'

had_flag=0
[ -f "$FLAG" ] && had_flag=1 && cp "$FLAG" "$BAK"

restore() {
  if [ "$had_flag" = "1" ] && [ ! -f "$FLAG" ]; then : > "$FLAG"; fi
  rm -f "$BAK"
  rm -rf "$WORKROOT"
}
trap restore EXIT INT TERM HUP

mkdir -p "$HERE/transcripts"

batch() {
  local cond="$1"
  while IFS='|' read -r cid prompt; do
    [ -z "${cid:-}" ] && continue
    for r in $(seq 1 "$RUNS"); do
      work="$WORKROOT/${cond}_${cid}_${r}"
      rm -rf "$work"; cp -R "$HERE/repo" "$work"
      ( cd "$work" && claude -p "$prompt" \
          --permission-mode acceptEdits \
          --settings "$SETTINGS" < /dev/null ) \
        > "$HERE/transcripts/${cid}_${cond}_${r}.txt" 2>&1
      echo "$cid $cond run$r: $(wc -w < "$HERE/transcripts/${cid}_${cond}_${r}.txt") words"
    done
  done < "$HERE/cases.txt"
}

# Verify the arm before spending runs on it.
assert_arm() {
  local want="$1"
  got=$(cd "$HERE/repo" && claude -p \
    'Do you have a ruleset in your context about ADHD-friendly output? Answer YES or NO only.' \
    --settings "$SETTINGS" < /dev/null 2>&1 | head -1 | tr -d '[:space:]')
  case "$got" in
    "$want"*) echo "arm check ok: expected $want, got $got" ;;
    *) echo "ARM CHECK FAILED: expected $want, got '$got'. Aborting."; exit 1 ;;
  esac
}

: > "$FLAG"
assert_arm YES
batch on

rm -f "$FLAG"
assert_arm NO
batch off

restore
[ "$had_flag" = "1" ] && { [ -f "$FLAG" ] && echo "sentinel restored" || echo "WARNING: sentinel missing"; }
