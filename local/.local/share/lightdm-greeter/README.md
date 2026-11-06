# Greeter de LightDM — Monochrome Hacker

Tema del greeter (`lightdm-gtk-greeter`) a juego con la paleta de Qtile:
negro `#0a0a0a`, texto `#e6e6e6`, gris `#5c5c5c`, línea `#262626` y rojo
`#ff3b30` solo para errores y apagado.

## Qué incluye

- `theme/MonochromeHacker/`: tema GTK3 que parte de Adwaita dark (para menús,
  diálogos y estados no cubiertos) y estiliza el greeter por sus nombres CSS
  reales (`#login_window`, `#panel_window`, `#prompt_entry`, `#login_button`…).
- `background.png`: fondo 1920×1080 con rejilla tenue y viñeta. Se regenera con
  `python background.py` (Pillow + numpy).
- `lightdm-gtk-greeter.conf`: configuración del greeter (tema, fondo, reloj,
  indicadores, un solo usuario sin avatar).
- `install.sh`: instalador idempotente con respaldos `.bak` y `--uninstall`.
- `preview.png`: captura de referencia del resultado (render del `.glade` real).

## Instalación

```sh
cd ~/dotfiles/local/.local/share/lightdm-greeter
sudo ./install.sh
```

O, si ya has hecho `stow .`:

```sh
sudo ~/.local/share/lightdm-greeter/install.sh
```

El greeter se aplica al **próximo inicio de sesión**. Para probarlo ya:

```sh
# cierra la sesión actual y vuelve al greeter
sudo systemctl restart lightdm
```

`sudo systemctl restart lightdm` termina la sesión gráfica actual: guarda
cualquier trabajo abierto antes.

## Revertir

```sh
sudo ./install.sh --uninstall
```

Restaura el tema y la configuración desde los `.bak` de la primera instalación.

## Detalles de diseño

- **Panel superior** de 32 px: indicadores en mono 11 px y gris; reloj en
  blanco y negrita; icono de apagado en rojo solo al pasar el ratón.
- **Tarjeta de login** de 424 px: cabecera con el usuario (como título de
  terminal), campo de contraseña con foco en blanco, pie separado y botón
  principal blanco. Sin esquinas redondeadas ni degradados.
- **Errores** en una banda roja translúcida dentro de la tarjeta.
- **Menús y diálogo de apagado** en el mismo negro, mono y bordes de 1 px.
- Consumo: es el `lightdm-gtk-greeter` de siempre (GTK3), sin WebKit ni
  compositor. El fondo es un PNG de ~550 KB que se dibuja una vez.

## Notas

- `#clock_menuitem` y `#host_menuitem` son `GtkSeparatorMenuItem`: su nodo CSS
  es `separator`, no `menuitem`. Por eso se estilan aparte.
- `power_title`, `power_text` y `power_icon` no tienen `name` CSS (solo id de
  Glade); se estilan por estructura (`#power_window grid label/image`).
- Este directorio vive dentro del paquete `local` de Stow: aparece como
  `~/.local/share/lightdm-greeter` (nunca como `~/lightdm`). El tema real se
  copia a `/usr/share` y `/etc` con `install.sh`; los enlaces de Stow solo
  versionan las fuentes.
