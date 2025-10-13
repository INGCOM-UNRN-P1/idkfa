//# -----------------------------------------------------------------------------
//# PLANTILLA: Suma con STDIN Dinámico
//# -----------------------------------------------------------------------------
//# Esta plantilla demuestra el uso de STDIN con variables dinámicas.

//# --- Macros para desarrollo y prueba ---
#define __num_a__ 5
#define __num_b__ 3
//# ------------------------------------

// Analiza el siguiente código que lee dos números y los suma:
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d", &a);
    scanf("%d", &b);
    printf("%d\n", a + b);
    return 0;
}
// ¿Qué valor imprime el programa?

/*name
Suma de dos números con scanf
*/

/*var
num_a: range(1, 20)
num_b: range(1, 20)
*/

/*STDIN
__num_a__
__num_b__
*/

/*distractors
# Error común: multiplicar
__num_a__ * __num_b__
# Error común: restar
__num_a__ - __num_b__
# Error común: solo el primero
__num_a__
*/
