#!/bin/bash
CAPACITY=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || cat /sys/class/power_supply/BAT1/capacity 2>/dev/null)
STATUS=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || cat /sys/class/power_supply/BAT1/status 2>/dev/null)

STATE_FILE="/tmp/battery_last_status"
LAST_STATUS=$(cat "$STATE_FILE" 2>/dev/null)

if [ "$STATUS" = "Charging" ]; then
    PREFIX=" "
    CLASS="charging"
    if [[ "$LAST_STATUS" != "Charging" && "$LAST_STATUS" != "Full" ]]; then
        powerprofilesctl set performance
        echo "Charging" > "$STATE_FILE"
    fi

#!elif [ "$STATUS" = "Full" ]; then
#!    PREFIX="100%"
#!    if [[ "$LAST_STATUS" != "Charging" && "$LAST_STATUS" != "Full" ]]; then
#!        powerprofilesctl set performance
#!        echo "Charging" > "$STATE_FILE"
#!    fi

elif [ "$STATUS" = "Discharging" ]; then
    if [ "$LAST_STATUS" != "Discharging" ]; then
        powerprofilesctl set power-saver
        echo "Discharging" > "$STATE_FILE"
    fi
    if [ "$CAPACITY" -le 19 ]; then
        PREFIX="Bro charge yo shit"
        CLASS=""
    else
        PREFIX=""
        CLASS="discharging-normal"
    fi

else
    PREFIX=" "
    CLASS="charging"
fi

echo "{\"text\": \"${PREFIX}\", \"class\": \"${CLASS}\", \"tooltip\": \"${CAPACITY}% | ${STATUS}\"}"
