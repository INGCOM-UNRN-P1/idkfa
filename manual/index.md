---
title: "Manual de Referencia: idkfa"
subtitle: "Idkfa — Síntesis Procedural de Código C, Cuestionarios Anti-Copia y Trazado para Moodle"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-idkfa)=
# Idkfa — Síntesis Procedural de Código C, Cuestionarios Anti-Copia y Trazado para Moodle

````{abstract}
**Rol en el ecosistema:** Generación de cuestionarios Moodle XML con variantes de código C compiladas y ejecutadas con GCC en tiempo real para obtener las respuestas numéricas exactas de cada tema.
````

---

(manual-idkfa-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`idkfa`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-idkfa-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `idkfa`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
idkfa doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-idkfa-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `idkfa`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `idkfa generate <plantilla.yaml> -n 20 -o banco.xml` | Sintetiza 20 variantes de preguntas C y genera Moodle XML. |
| `idkfa render <plantilla.yaml>` | Previsualiza el código C generado y su salida exacta de ejecución. |
| `idkfa spellcheck <plantilla.yaml>` | Verifica ortografía y enunciados con LanguageTool. |
| `idkfa doctor` | Verifica la instalación de GCC y Moodle XML parser. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-idkfa-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
// Plantilla Idkfa con variables procedurales {{A}}, {{B}}, {{OP}}
#include <stdio.h>
int main(void) {
    int x = {{A}};
    int y = {{B}};
    x {{OP}}= y;
    printf("%d\n", x);
    return 0;
}
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
idkfa generate <plantilla.yaml> -n 20 -o banco.xml
````

### Salida Obtenida en Consola

````{code-block} text
[✓] Compilando variante 1 (A=12, B=4, OP=+): Salida GCC = '16'
[✓] Compilando variante 2 (A=20, B=3, OP=*): Salida GCC = '60'
[✓] Generadas 20 preguntas con retroalimentación paso a paso en banco_moodle.xml
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-idkfa-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`idkfa`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Cuestionario de Punteros y Arreglos
Sintetizar 30 variantes de seguimiento de aritmética de punteros.

**Instrucción de ejecución:**
```bash
idkfa generate templates/punteros.yaml -n 30 -o moodle_ptr.xml
```
````

````{solution} Desafío 1
```bash
idkfa generate templates/punteros.yaml -n 30 -o moodle_ptr.xml
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Preguntas de Seguimiento de Lazos
Generar ejercicios de conteo de iteraciones en lazos anidados.

**Instrucción de ejecución:**
```bash
idkfa generate templates/lazos.yaml -n 25 -o moodle_lazos.xml
```
````

````{solution} Desafío 2
```bash
idkfa generate templates/lazos.yaml -n 25 -o moodle_lazos.xml
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Auditoría Lingüística del Banco
Comprobar ortografía en las explicaciones paso a paso de las respuestas.

**Instrucción de ejecución:**
```bash
idkfa spellcheck templates/punteros.yaml
```
````

````{solution} Desafío 3
```bash
idkfa spellcheck templates/punteros.yaml
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-idkfa-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `idkfa` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-idkfa:
	@echo "=== Ejecutando verificación con idkfa ==="
	idkfa check src/ include/

.PHONY: check-idkfa
````

Ejecutá `make check-idkfa` antes de cada commit para asegurar que tu código conserve el estado de aprobación.

---

(manual-idkfa-arquitectura)=
## 7. Arquitectura Interna y Mecanismo Técnico

La herramienta **`idkfa`** implementa un motor de alta precisión basado en:

- **Tecnología Núcleo:** `Procedural C Template Engine + GCC Runner en Sandbox + Moodle XML Serializer`.
- **Aislamiento y Determinismo:** Diseñada para operar sin efectos colaterales en entornos de integración continua (CI), terminales de estudiantes y servidores docentes headless.
- **Manejo de Errores Pedagógico:** Todo fallo de sintaxis, memoria o lógica se traduce en una acción prescriptiva concreta con su respectiva justificación técnica.

---

(manual-idkfa-ecosistema)=
## 8. Integración y Conexión con el Ecosistema

````{note}
Ninguna herramienta opera de forma aislada. **`idkfa`** forma parte del pipeline integral de evaluación, verificación y enseñanza de la cátedra.
````

### Diagrama de Flujo e Interoperabilidad

````{mermaid}
graph TD
    TPL[Plantillas YAML con Variables] --> IDK[Idkfa: Síntesis Procedural]
    IDK -->|Compilación y Ejecución| GCC[GCC: Cálculo de Respuestas]
    IDK -->|Cuestionarios XML Anti-Copia| MDL[Moodle-Toolbox: Bancos Campus]
    IDK -->|Variantes de Seguimiento| ALU[Alucard: Exámenes Impresos]
````

### Matriz de Intercambio de Datos

| Canal | Herramientas Conectadas | Tipo de Datos Transferidos |
| :--- | :--- | :--- |
| **Entradas (Inputs)** | - `Plantillas YAML con variables aleatorias y código C` | Código fuente, AST, binarios, testcases, contratos |
| **Salidas (Outputs)** | - `moodle-toolbox (bancos XML)`
- `alucarD (preguntas de parcial)` | Informes Markdown, diagnósticos Rich, JSON, actas |
| **Sincronización** | `alucarD`, `moodle-toolbox`, `daedalus` | Validación cruzada, flags compartidos y autofix |

### Pipeline de Integración Recomendado

Podés encadenar `idkfa` con otras herramientas del ecosistema en una única línea de comando:

````{code-block} bash
# Pipeline de integración típico
idkfa generate templates/punteros.yaml -n 50 -o banco_ptr.xml && questions validate banco_ptr.xml
````

