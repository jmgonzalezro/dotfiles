#!/bin/bash
# Test de velocidad de internet -> notificación dunst.
# Invocado desde el botón de la barra de qtile.

ID=9996  # libre: 9999 volumen, 9998 urgentes, 9997 capturas
LOCK=/tmp/speedtest.lock
OUT=/tmp/speedtest.out

# Evita tests simultáneos (el segundo clic no lanza otro proceso).
if [ -e "$LOCK" ] && kill -0 "$(cat "$LOCK")" 2>/dev/null; then
    dunstify -r "$ID" -t 3000 -a qtile "Test ya en curso" "Espera a que termine el actual."
    exit 0
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# Notificación persistente (-t 0) mientras mide.
dunstify -r "$ID" -t 0 -a qtile "Midiendo velocidad" "Espera unos segundos…"

# --secure usa HTTPS. timeout evita que se cuelgue si no hay red.
timeout 90 speedtest-cli --secure --simple > "$OUT" 2>&1
status=$?

if [ $status -ne 0 ]; then
    err=$(tr '\n' ' ' < "$OUT" | head -c 200)
    dunstify -r "$ID" -t 8000 -u critical -a qtile "Test de velocidad fallido" \
        "Sin resultado (código $status). $err"
    exit 1
fi

ping=$(awk '/^Ping:/{print $2}' "$OUT")
down=$(awk '/^Download:/{print $2}' "$OUT")
up=$(awk '/^Upload:/{print $2}' "$OUT")

if [ -z "$down" ]; then
    dunstify -r "$ID" -t 8000 -u critical -a qtile "Test de velocidad" "Salida inesperada: $(tr '\n' ' ' < "$OUT" | head -c 200)"
    exit 1
fi

dunstify -r "$ID" -t 15000 -a qtile "Velocidad de internet" \
    "$(printf 'Ping     %s ms\nDescarga %s Mbit/s\nSubida   %s Mbit/s' \
        "${ping:-?}" "$down" "${up:-?}")"
