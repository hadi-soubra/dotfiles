#!/bin/bash
CAPACITY=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || cat /sys/class/power_supply/BAT1/capacity 2>/dev/null)
STATUS=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || cat /sys/class/power_supply/BAT1/status 2>/dev/null)

BLOCKS=10
FILLED=$(( CAPACITY * BLOCKS / 100 ))
EMPTY=$(( BLOCKS - FILLED ))

BAR=""
for i in $(seq 1 $FILLED); do BAR="${BAR}█ "; done
for i in $(seq 1 $EMPTY); do BAR="${BAR}░ "; done

if [ "$STATUS" = "Discharging" ] && [ "$CAPACITY" -gt 20 ]; then
    CLASS="no-prefix"
else
    CLASS=""
fi

echo "{\"text\": \"┃${BAR}\", \"class\": \"${CLASS}\", \"tooltip\": \"${CAPACITY}% | ${STATUS}\"}"
