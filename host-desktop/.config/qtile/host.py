# Overrides del SOBREMESA (los instala el paquete host-desktop).

# xrandr del monitor principal: DP-2 a 1920x1080@144.
# En el portátil esto no debe ejecutarse (no existe DP-2).
host_autostart = [
    ["xrandr", "--output", "DP-2", "--mode", "1920x1080", "--rate", "144.00"],
]
