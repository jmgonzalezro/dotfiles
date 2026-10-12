#!/usr/bin/env bash
# Notificación al conectar/desconectar un USB
# Monitorea eventos de bloque de udev y envía notificación con dunst.

export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

LOGFILE="${XDG_DATA_HOME:-$HOME/.local/share}/usb-notify.log"

udevadm monitor --udev -s block | while read -r _ _ action devpath _; do
    # Saltar líneas de cabecera
    [[ -z "$devpath" || -z "$action" ]] && continue
    [[ "$devpath" == *"monitor will print"* ]] && continue
    [[ "$devpath" == *"UDEV - the event"* ]] && continue

    # Quitar sufijo " (block)" del path
    devpath="${devpath% (block)}"

    # Solo dispositivos USB: su path contiene "/usb"
    [[ "$devpath" != *"/usb"* ]] && continue

    devname="$(basename "$devpath")"

    # Ignorar particiones (nombres terminados en dígito)
    [[ "$devname" =~ [0-9]$ ]] && continue

    if [[ "$action" == "add" ]]; then
        # Esperar a que udisks2 monte
        mountpoint=""
        for _ in 1 2 3 4 5; do
            mountpoint="$(findmnt -no TARGET -S "/dev/$devname" 2>/dev/null || true)"
            [[ -n "$mountpoint" ]] && break
            sleep 1
        done
        size="$(lsblk -no SIZE "/dev/$devname" 2>/dev/null || echo "?")"
        label="$(lsblk -no LABEL "/dev/$devname" 2>/dev/null || true)"

        msg="Dispositivo: $devname ($size)"
        [[ -n "$label" ]] && msg="$msg
Etiqueta: $label"
        if [[ -n "$mountpoint" ]]; then
            msg="$msg
Montado en: $mountpoint"
        else
            msg="$msg
(No montado automáticamente)"
        fi

        notify-send -u low -a "USB" "USB conectado" "$msg"
        echo "$(date -Iseconds) ADD: $devname -> $mountpoint" >> "$LOGFILE"

    elif [[ "$action" == "remove" ]]; then
        notify-send -u normal -a "USB" "USB desconectado" "Dispositivo: $devname"
        echo "$(date -Iseconds) REMOVE: $devname" >> "$LOGFILE"
    fi
done
