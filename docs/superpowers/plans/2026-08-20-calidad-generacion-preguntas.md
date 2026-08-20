# Plan de Implementación: Calidad y Generación de Preguntas (Sección 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar las 5 mejoras de la Sección 3 (items 9 al 13) en `generador.py` para robustecer la generación de opciones, distractores, feedback pedagógico y parametrización de preguntas Moodle.

**Architecture:** Modificar el parser y el generador de preguntas para soportar normalización de distractores numéricos/texto, garantía de distractores mínimos, soporte de metadatos `/*penalty*/`, `/*defaultgrade*/`, `/*type*/` (`multichoice`, `shortanswer`, `numerical`), y `/*feedback*/` dinámico evaluable.

**Tech Stack:** Python 3, `xml.etree.ElementTree`, `unittest`, `argparse`.

## Global Constraints
- Mantener compatibilidad hacia atrás con todos los templates existentes.
- Cada cambio debe acompañarse de tests unitarios específicos.
- Commits semánticos por cada ítem implementado (`fix:`, `feat:`).

---

### Task 1: Normalización de distractores duplicados por formateo (Item 9)
### Task 2: Garantizar mínimo estricto de distractores (Item 10)
### Task 3: Configuración de peso/penalización por pregunta (Item 11)
### Task 4: Soporte para múltiples tipos de preguntas Moodle (Item 12)
### Task 5: Retroalimentación dinámica y feedback pedagógico (Item 13)
