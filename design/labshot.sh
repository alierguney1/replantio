#!/bin/zsh
O=$1; W=${2:-1600}; H=${3:-1500}
rm -f "$O" /tmp/lab-dom.html; D=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-sandbox \
 --window-size=$W,$H --virtual-time-budget=15000 --user-data-dir=$D --screenshot="$O" \
 "http://localhost:8877/design/tree-lab.html" >/dev/null 2>&1 &
P=$!; for i in $(seq 1 60); do perl -e 'select(undef,undef,undef,1)'; [ -s "$O" ] && break; done
perl -e 'select(undef,undef,undef,1)'; kill $P 2>/dev/null
D2=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-sandbox \
 --virtual-time-budget=15000 --user-data-dir=$D2 --dump-dom "http://localhost:8877/design/tree-lab.html" > /tmp/lab-dom.html 2>/dev/null &
P2=$!; for i in $(seq 1 60); do perl -e 'select(undef,undef,undef,1)'; grep -q "grain8" /tmp/lab-dom.html 2>/dev/null && break; done
kill $P2 2>/dev/null
perl -0777 -ne 'print $1 if /<pre id="stats">(.*?)<\/pre>/s' /tmp/lab-dom.html
[ -s "$O" ] && echo "OK $O" || echo "FAIL"
