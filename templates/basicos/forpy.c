//# -----------------------------------------------------------------------------
//# PLANTILLA: BUCLE FOR SIN LLAVES (GOTCHA)
//# -----------------------------------------------------------------------------
//# Esta plantilla evalúa la comprensión de una trampa común en C: un bucle 'for'
//# sin llaves solo ejecuta la primera instrucción que le sigue. La indentación
//# es engañosa y no afecta el comportamiento del código.

// Analiza el siguiente código. ¿Cuál es el valor final de 'acumulador'?
#include <stdio.h>
//# Acceso a miembro mediante operador punto.
#include <stdlib.h>

//# --- Macros para desarrollo y prueba ---
//# Permiten que este archivo .c sea compilable para pruebas.
#define __loop_limit__ 5
#define __multiplier__ 2
// ------------------------------------

int main() {
    int acumulador = 0;
    int i;

    //# A pesar de la indentación, solo la línea "acumulador += i;" está dentro del bucle.
    //# La línea "acumulador *= __multiplier__;" se ejecutará UNA SOLA VEZ cuando el bucle termine.
    for (int i = 0; i < __loop_limit__; i++);
        acumulador = acumulador + i;
        acumulador = acumulador * __multiplier__;
    
    //# Imprimimos el valor final de 'acumulador' para que el script lo capture.
    printf("%d", acumulador);
    
    return EXIT_SUCCESS;
}
// ¿Qué valor se imprime en la consola?

/*name
//# El nombre que aparecerá en el banco de preguntas de Moodle.
Bucles - El 'Gotcha' del for sin Llaves y 'a la Python'
*/

/*var
//# --- Variables Dinámicas ---
//# El script seleccionará valores aleatorios de estos rangos.

//# El límite superior del bucle (no inclusivo).
loop_limit: range(4, 8)

//# El valor por el que se multiplica el acumulador al final.
multiplier: range(2, 4)
*/

/*correcta
# __loop_limit__ * __multiplier__
*/

/*opciones
Error de compilación.
Bucle infinito.
Comportamiento indefinido.
*/

/*distractors
# (lambda limit, mult: (lambda f, x, n: f(f, x, n))(lambda f, x, n: x if n == 0 else (f(f, x, n-1) + (n-1)) * mult, 0, limit))(__loop_limit__, __multiplier__)
# sum(range(__loop_limit__))
*/
