# Temas de Qtile (y apps)

Cada `*.toml` de esta carpeta es un tema. El tema activo se guarda en
`~/.local/state/qtile/theme` (no se versiona: es estado de la máquina).

Un tema cubre **cuatro** consumidores: la barra de Qtile, Alacritty, Rofi y
Dunst. Los tres últimos no pueden leer TOML ni incluir archivos libremente, así
que `theme-apps.py` los traduce a los archivos que cada app sí entiende.

## Uso

```sh
theme.sh                 # tema actual + disponibles
theme.sh washed          # aplicar por nombre
theme.sh toggle          # alternar (ciclo entre todos)
theme.sh menu            # selector con rofi
theme.sh render          # regenerar archivos de app sin recargar (lo usa el arranque)
```

Atajos: `mod+shift+t` alterna, `mod+shift+ctrl+t` abre el menú.

## Cómo se propaga

```
themes/<nombre>.toml  (fuente de verdad)
        │
        ├─ config.py ................ barra de Qtile (recarga: mod+ctrl+r / theme.sh)
        └─ theme-apps.py ─┬─ ~/.local/state/qtile/app/alacritty.toml  (import)
                          ├─ ~/.local/state/qtile/app/rofi.rasi       (?import)
                          └─ ~/.local/state/qtile/app/dunstrc         (config completa)
```

Reglas de carga que condicionan el diseño:

| App | Cómo recibe el tema | Recarga |
|---|---|---|
| Alacritty | `[general].import` en `alacritty.toml` | `theme.sh` toca el config principal: relee la cadena en caliente |
| Rofi | `?import` **al final** de `config.rasi` (gana la última declaración) | al abrirse; `rofi -dump-theme` para inspeccionar |
| Dunst | no tiene *include* → se copia el `dunstrc` entero cambiando color y fuente | `dunstctl reload <ruta>`; el arranque lo lanza con `--config` |

Dos trampas documentadas aquí porque ya nos costaron una depuración:

1. **Alacritty carga el archivo que importa al final**, así que cualquier
   `[colors]` o `window.opacity` en `alacritty.toml` sobrescribiría el tema.
   Esos valores deben vivir solo en el archivo generado.
2. **En rasi no se puede escribir `/*` dentro de un comentario** (aunque sea
   texto, p. ej. `themes/*.toml`): abre un comentario anidado y rofi se traga
   el resto del archivo. Además rofi falla en silencio (vuelve al solarized por
   defecto con `rc=0`), por eso `theme.sh` valida el tema ya parseado.

## Aplicación atómica

`theme.sh <tema>` no toca nada hasta que todo valida:

1. ejecuta `config.py` con `QTILE_THEME=<tema>`;
2. renderiza los tres archivos a `app.staging/`;
3. parsea el `rofi.rasi` con rofi y comprueba fuente y color de fondo (si rofi
   no entiende el archivo, vuelve al tema por defecto sin avisar);
4. solo entonces escribe el estado y sustituye `app/` de golpe.

Si algo falla, se queda el tema anterior. Nada de esto toca arranque, systemd,
Xorg ni NVIDIA.

## Campos

### Qtile

| Clave | Significado |
|---|---|
| `font`, `fontsize` | tipografía de la barra y widgets |
| `bar_size` | alto de la barra en px |
| `bar_position` | `top` o `bottom` |
| `bar_background` | color con alfa `#RRGGBBAA` (`00` = transparente, `99` = negro al 60%) |
| `bar_border_width`, `bar_border_color` | borde de la barra |
| `bar_opacity` | opacidad global de la ventana de la barra (1.0 = texto nítido) |
| `groupbox_borderwidth` | grosor del marco del grupo activo |
| `groupbox_highlight_method` | `border` (caja) o `text` (solo color, como la captura) |
| `colors.*` | `bg`, `fg`, `accent`, `dim`, `border_focus`, `border_normal`, `urgent` |
| `layout.*` | `margin`, `border_width`, `ratio_tall`, `ratio_wide` |

### Alacritty — `[alacritty]`

| Clave | Significado |
|---|---|
| `background`, `foreground` | colores base |
| `cursor`, `cursor_text` | cursor |
| `selection_background`, `selection_foreground` | selección (opcionales) |
| `normal_*`, `bright_*` | los 8 + 8 colores ANSI (`black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`) |
| `indexed_16`, `indexed_17` | colores indexados extra (opcionales) |
| `opacity` | 1.0 = opaca |

### Rofi — `[rofi]`

| Clave | Significado |
|---|---|
| `background` | admite alfa `#RRGGBBAA` (rofi la respeta vía picom) |
| `foreground`, `dim`, `urgent`, `accent` | paleta |
| `selection_background`, `selection_foreground` | fila seleccionada (invertida) |
| `border`, `border_color`, `radius` | ventana |
| `font` | fuente con tamaño |

### Dunst — `[dunst]`

| Clave | Significado |
|---|---|
| `frame_width`, `frame_color` | marco de la notificación |
| `font` | fuente con tamaño |
| `low_*`, `normal_*`, `critical_*` | `background`, `foreground`, `frame_color` por urgencia |

## Añadir un tema

Copia `monochrome.toml` (que reproduce el estado previo al selector) y cambia
valores. Valida antes de aplicar:

```sh
QTILE_THEME=mi-tema python3 ~/.config/qtile/config.py && echo ok
theme.sh mi-tema
```
