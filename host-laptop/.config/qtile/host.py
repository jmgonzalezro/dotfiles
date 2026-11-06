# Overrides del PORTÁTIL (los instala el paquete host-laptop).

# Si hace falta forzar resolución/refresh del panel, mira `xrandr -q` para el
# nombre de la salida (normalmente eDP-1) y añade la línea, p. ej.:
#   ["xrandr", "--output", "eDP-1", "--mode", "1920x1080", "--rate", "60.00"],
host_autostart = []
