#!/bin/bash

until hyprctl monitors > /dev/null 2>&1; do
    sleep 0.5
done

hyprctl dispatch workspace 1
until hyprctl activeworkspace | grep -q "workspace ID 1 "; do
    sleep 0.1
done

until pactl info > /dev/null 2>&1; do
    sleep 0.5
done



# Kill remaining dashboard windows on workspace 1
hyprctl clients -j | jq -r '.[] | select(.workspace.id == 1) | .pid' | while read -r pid; do
    kill -9 "$pid" 2>/dev/null
done

sleep 0.5

#launch kitty
kitty --title "fetche" &
while ! hyprctl clients | grep -q "title: fetche"; do
    sleep 0.1
done


#launch clock
hyprctl dispatch layoutmsg preselect r
kitty --title "clocke" -e tty-clock -c -r -C 7 &
while ! hyprctl clients | grep -q "title: clocke"; do
    sleep 0.1
done


#launch cava
hyprctl dispatch layoutmsg preselect d
kitty --title "cavae" -e cava &
while ! hyprctl clients | grep -q "title: cavae"; do
    sleep 0.1
done
hyprctl dispatch resizewindowpixel exact 930 600,title:cavae


#launch matrix
hyprctl dispatch focuswindow title:clocke
hyprctl dispatch layoutmsg preselect r
kitty --title "matrixe" -e cmatrix -C white &

#focus terminal
sleep 1
hyprctl dispatch focuswindow title:fetche
