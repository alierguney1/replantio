#!/bin/bash
# pshot.sh <file#hash> <out.png> [width] [height]
# Headless Chrome writes the screenshot but does not exit, so: launch detached,
# wait for the file to stop growing, then kill it.
URL="http://localhost:8877/design/$1"
OUT="$2"; W="${3:-1600}"; H="${4:-1960}"
rm -f "$OUT"
D=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --window-size="$W,$H" --force-device-scale-factor=2 --hide-scrollbars \
  --virtual-time-budget=5000 --user-data-dir="$D" --disk-cache-dir=/tmp/canopy-cache \
  --no-first-run --no-default-browser-check \
  --screenshot="$OUT" "$URL" >/dev/null 2>&1 &
PID=$!
prev=-1
for i in $(seq 1 60); do
  sleep 1
  if [ -f "$OUT" ]; then
    cur=$(wc -c < "$OUT")
    [ "$cur" = "$prev" ] && [ "$cur" -gt 1000 ] && break
    prev=$cur
  fi
done
kill $PID 2>/dev/null; wait $PID 2>/dev/null
rm -rf "$D"
[ -f "$OUT" ] || { echo "FAILED $OUT"; exit 1; }
X=$(( (W - 16 - 430) * 2 ))
sips -c $((H*2)) 884 --cropOffset 1 $X "$OUT" --out "${OUT%.png}-col.png" >/dev/null 2>&1
echo "ok $OUT $(wc -c < "$OUT") bytes"
