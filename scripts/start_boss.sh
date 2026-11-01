#!/usr/bin/env bash
sleep 3
cd ~/NovaAgent-Clean && setsid python3 scripts/opencode_bridge.py --port 9897 > ~/opencode_bridge.log 2>&1 < /dev/null & disown
sleep 3
bash ~/NovaAgent-Clean/scripts/start.sh > ~/nova_run.log 2>&1 & disown
sleep 12
for p in 9897 17008; do timeout 2 bash -c "echo > /dev/tcp/127.0.0.1/$p" 2>/dev/null && echo "$p OPEN ✓" || echo "$p closed ✗"; done
