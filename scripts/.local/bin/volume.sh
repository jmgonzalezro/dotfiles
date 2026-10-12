#!/bin/bash
# volume.sh up|down|mute — controla el volumen con pactl y muestra un OSD ASCII con dunst
case "$1" in
    up)   pactl set-sink-volume @DEFAULT_SINK@ +5% ;;
    down) pactl set-sink-volume @DEFAULT_SINK@ -5% ;;
    mute) pactl set-sink-mute @DEFAULT_SINK@ toggle ;;
    *)    exit 1 ;;
esac

vol=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oE '[0-9]+%' | head -1 | tr -d '%')
mute=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -oE 'yes|no')

(( vol > 100 )) && vol=100
filled=$(( vol / 5 ))
empty=$(( 20 - filled ))

bar="["
for ((i = 0; i < filled; i++)); do bar+="#"; done
for ((i = 0; i < empty; i++)); do bar+="."; done
bar+="]"

if [ "$mute" = "yes" ]; then
    dunstify -a "volume" -r 9999 -t 1500 " MUTE $bar 0%"
else
    dunstify -a "volume" -r 9999 -t 1500 " $bar ${vol}%"
fi
