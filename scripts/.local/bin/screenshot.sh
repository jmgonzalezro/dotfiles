#!/bin/bash
# screenshot.sh [full|area] — captura, guarda en ~/Images y copia al portapapeles
dir="$HOME/Images"
mkdir -p "$dir"
file="$dir/$(date +%Y-%m-%d-%H%M%S)-screenshot.png"

if [ "$1" = "area" ]; then
    scrot -s "$file" || exit 1
else
    scrot "$file"
fi

xclip -selection clipboard -t image/png < "$file"
dunstify -a "Screenshot" -r 9997 -t 2000 "$(basename "$file") → portapapeles"
