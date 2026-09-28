# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versiones según [SemVer](https://semver.org/lang/es/).

## [0.3.0] - 2026-09-28

Primera versión con registro de cambios; lo anterior está en el historial de git.

### Agregado

- **cli**: cumplir el contrato de línea de comandos de LINEAMIENTOS §3.2 (N-ECO-04) (`b6ed9ac`)

### Corregido

- **seguridad**: evaluar las expresiones de plantilla con una lista blanca en lugar de eval (N-IDKFA-02) (`b3ca5ae`)
- **cli**: mostrar los errores de uso como mensajes y agregar --version (N-IDKFA-01) (`427d13a`)

### Documentación

- agregar el texto de la licencia GPL-3.0-or-later que declara pyproject (N-ECO-06) (`c2d86e4`)
- incorporar manual de uso integral y referencia tecnica (idkfa) (`46a89c0`)

### Mantenimiento

- **calidad**: verificar errores de Python y dependencias vulnerables (N-ECO-08, N-ECO-13) (`06d1c80`)
- **deps**: mover las dependencias de desarrollo a dependency-groups (N-ECO-07) (`a802421`)
