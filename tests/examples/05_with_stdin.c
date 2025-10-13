// What does this program output?
#define __num_a__ 5
#define __num_b__ 3

#include <stdio.h>
int main() {
    int a, b;
    scanf("%d", &a);
    scanf("%d", &b);
    printf("%d", a + b);
    return 0;
}
// Answer:

/*name
Example with STDIN
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
__num_a__ * __num_b__
__num_a__ - __num_b__
__num_a__
*/
