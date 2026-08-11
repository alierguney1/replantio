#!/bin/zsh
# usage: shot.sh <url> <outpath> [w] [h] [budget_ms]
U=$1; O=$2; W=${3:-1600}; H=${4:-1000}; B=${5:-20000}
rm -f "$O"; D=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-sandbox \
  --window-size=$W,$H --virtual-time-budget=$B --user-data-dir=$D --screenshot="$O" "$U" >/dev/null 2>&1 &
P=$!
for i in $(seq 1 90); do perl -e 'select(undef,undef,undef,1)'; [ -s "$O" ] && break; done
perl -e 'select(undef,undef,undef,1)'; kill $P 2>/dev/null; rm -rf $D
[ -s "$O" ] && echo "OK $O" || echo "FAIL $O"
