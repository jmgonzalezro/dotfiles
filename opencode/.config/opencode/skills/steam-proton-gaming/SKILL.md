---
name: Steam Proton Gaming
description: Optimización de videojuegos en Linux con Steam, Proton, gamemode, mangohud y rendimiento NVIDIA.
---

## Entorno del usuario
- Steam instalado, juegos de Windows vía Proton.
- GPU NVIDIA RTX 3070, driver 615.78.

## Proton
- Forzar versión por juego: Steam → Biblioteca → clic derecho → Propiedades → Compatibilidad → "Forzar el uso de una herramienta de compatibilidad".
- Variables de lanzamiento (en Propiedades → General → Parámetros de lanzamiento):
  - `PROTON_LOG=1 %command%` → genera ~/steam-<app>.log para depurar.
  - `PROTON_ENABLE_NVAPI=1` → mejora integración NVIDIA.
  - `PROTON_USE_WINED3D=0` → usar Vulkan (DXVK) en vez de OpenGL.
- Proton GE: build con codecs y parches extra; útil cuando la versión oficial falla.

## Rendimiento
- gamemode: `gamemoderun %command%` (requiere paquetes `gamemode` y `lib32-gamemode`).
- mangohud: `mangohud %command%` → overlay con FPS, temperaturas y Uso de GPU (paquete `mangohud`).
- Combinación típica: `MANGOHUD=1 gamemoderun %command%`.
- Shader cache de NVIDIA: mantener habilitado para evitar tirones en la primera ejecución.

## Diagnóstico
- Monitorizar GPU: `nvidia-smi` en otra terminal durante la sesión.
- Versiones de DXVK/VKD3D y de Proton/Wine afectan al rendimiento y a los errores gráficos.
- Algunos anti-cheat (EAC, BattlEye) no son compatibles con Proton salvo que el juego lo soporte.

## Buenas prácticas
- Cambiar una sola variable a la vez y probar antes de acumular cambios.
- Revisar protondb.com para notas de compatibilidad de cada juego.
- Mantener el driver NVIDIA actualizado para mejor soporte de Vulkan.
