// What does fgets do with this buffer?
#include <stdio.h>
int main() {
    char buf[10];
    fgets(buf, sizeof(buf), stdin);
    printf("Success");
    return 0;
}
// Answer:

/*name
Example with Fixed Correct Answer
*/

/*correcta
Success
*/

/*opciones
Error
Undefined Behavior
Segmentation Fault
Buffer Overflow
*/
