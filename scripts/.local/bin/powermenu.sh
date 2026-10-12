#!/bin/bash
option=$(echo -e "Apagar\nReiniciar\nCerrar sesión" | rofi -dmenu -p "Power")

case $option in
    "Apagar") systemctl poweroff ;;
    "Reiniciar") systemctl reboot ;;
    "Cerrar sesión") qtile cmd-obj -o cmd -f shutdown ;;
esac
