//# -----------------------------------------------------------------------------
//# PLANTILLA: FGETS SEGURO - LECTURA CON LÍMITE
//# -----------------------------------------------------------------------------
//# Esta plantilla evalúa la comprensión de manejo seguro de cadenas en C.
//# Demuestra que fgets lee con un límite de tamaño, lo que previene buffer overflow.
//# El programa usa fgets correctamente con sizeof(buf), haciéndolo seguro.

//# --- Macros para desarrollo y prueba ---
#define __buffer_size__ 10
//# ------------------------------------

// Analiza el siguiente código que usa fgets para leer entrada de forma segura:
#include <stdio.h>
int main() {
    char buf[__buffer_size__];
    // fgets lee hasta buffer_size-1 caracteres + '\0'
    // Es seguro porque respeta el límite del buffer
    if (fgets(buf, sizeof(buf), stdin) != NULL) {
        printf("OK\n");
    }
    return 0;
}
// ¿Qué imprime el programa con la entrada dada?

/*name
Cadenas Seguras - fgets con límite de buffer
*/

/*var
//# Tamaño del buffer para almacenar la entrada
buffer_size: range(8, 16)
*/

/*opciones
Error de compilación
Segmentation fault
Buffer overflow
No imprime nada
El texto ingresado
*/

/*distractors
# "Error de lectura"
# "Buffer overflow"
# "Segmentation fault"
# "Comportamiento indefinido"
*/

/*STDIN
//# Texto de prueba que es seguro para cualquier buffer >= 8
Hola
*/
