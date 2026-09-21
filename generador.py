#!/usr/bin/env python3
"""Script de conveniencia: la implementación vive en `idkfa.generacion`.

Se conserva `generador.py` porque el README y los flujos existentes lo invocan
(`./generador.py`, `import generador`). El módulo se reemplaza por
`idkfa.generacion`, así que parchear `generador.X` afecta al código real.
"""

import sys

from idkfa import generacion

if __name__ == "__main__":
    generacion.main()
else:
    sys.modules[__name__] = generacion
