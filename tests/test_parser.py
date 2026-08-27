import unittest
from idkfa.parser import parse_c_template, TemplateInfo, DistractorDef

class TestParser(unittest.TestCase):
    def test_distractor_def_dataclass(self):
        d = DistractorDef(expression="x + 1", feedback="Sumaste uno")
        self.assertEqual(d.expression, "x + 1")
        self.assertEqual(d.feedback, "Sumaste uno")

    def test_template_info_methods(self):
        info = TemplateInfo(status="success", name="Test Q", custom_flags=["-Wall"])
        d = info.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["name"], "Test Q")
        self.assertEqual(info.get("name"), "Test Q")
        self.assertEqual(info.get("non_existent", "default_val"), "default_val")
        self.assertEqual(info["name"], "Test Q")
        self.assertTrue("name" in info)
        self.assertFalse("non_existent_key_123" in info)

    def test_parse_missing_intro_comment(self):
        content = "#include <stdio.h>\nint main(){}"
        res = parse_c_template(content)
        self.assertEqual(res["status"], "error")
        self.assertIn("No se encontró el comentario de introducción", res["reason"])

    def test_parse_missing_outro_comment(self):
        content = "// Intro comment only\n#include <stdio.h>\nint main(){}"
        res = parse_c_template(content)
        self.assertEqual(res["status"], "error")
        self.assertIn("No se encontró el comentario de cierre", res["reason"])

    def test_parse_all_metadata_blocks(self):
        content = """// Enunciado intro
#define __val__ 10
#include <stdio.h>
#include <math.h>

int main() {
    int x = __val__;
    printf("%d", x);
    return 0;
}
// Enunciado cierre

/*name
Pregunta Completa
*/

/*var
val: range(1, 5)
*/

/*opciones
Opcion1
Opcion2
*/

/*distractors
//# Comentario ignorado
# __val__ + 1 -> Sumaste uno
__val__ * 2 // Duplicaste
f"{10 // 2}"
*/

/*flags -O3 -g*/

/*penalty 0.25*/

/*defaultgrade 3.0*/

/*type numerical*/

/*feedback
//# Comentario ignorado en feedback
El valor era __val__
*/
"""
        res = parse_c_template(content)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["name"], "Pregunta Completa")
        self.assertEqual(res["var_defs"], {"val": "range(1, 5)"})
        self.assertEqual(res["predefined_options"], ["Opcion1", "Opcion2"])
        self.assertEqual(res["penalty"], "0.25")
        self.assertEqual(res["default_grade"], "3.0")
        self.assertEqual(res["question_type"], "numerical")
        self.assertEqual(res["feedback_template"], "El valor era __val__")
        
        # Verify custom flags including -lm from math.h
        self.assertIn("-O3", res["custom_flags"])
        self.assertIn("-g", res["custom_flags"])
        self.assertIn("-lm", res["custom_flags"])
        
        # Verify distractors
        self.assertEqual(len(res["distractor_defs"]), 3)
        self.assertEqual(res["distractor_defs"][0].expression, "__val__ + 1")
        self.assertEqual(res["distractor_defs"][0].feedback, "Sumaste uno")
        self.assertEqual(res["distractor_defs"][1].expression, "__val__ * 2")
        self.assertEqual(res["distractor_defs"][1].feedback, "Duplicaste")

    def test_parse_math_with_lm_already_present(self):
        content = """// Q
#include <math.h>
int main(){ return 0; }
// A
/*flags -lm -O2*/
"""
        res = parse_c_template(content)
        self.assertEqual(res["custom_flags"].count("-lm"), 1)

    def test_parse_correcta_expression(self):
        content = """// Q
int main(){ return 0; }
// A
/*correcta
# __val__ * 2
*/
"""
        res = parse_c_template(content)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["correct_answer_expression"], "__val__ * 2")
        self.assertIsNone(res["fixed_correct_answer"])

    def test_parse_correcta_fixed_text(self):
        content = """// Q
int main(){ return 0; }
// A
/*correcta
//# Comentario ignorado
Respuesta Fija
Segunda Linea
*/
"""
        res = parse_c_template(content)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["fixed_correct_answer"], "Respuesta Fija\nSegunda Linea")

    def test_parse_stdin_block(self):
        content = """// Q
int main(){ int x; scanf("%d", &x); return 0; }
// A
/*STDIN
//# Comentario
linea 1
linea 2
*/
"""
        res = parse_c_template(content)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["stdin_template"], "linea 1\nlinea 2")

    def test_parse_unrecognized_question_type(self):
        content = """// Q
int main(){ return 0; }
// A
/*type essay*/
"""
        res = parse_c_template(content)
        self.assertEqual(res["question_type"], "multichoice")

    def test_semantic_validation_all_input_functions(self):
        funcs = ["fgets(buf, 10, stdin)", "getchar()", "getc(stdin)", "read(0, buf, 10)", "fscanf(stdin, \"%d\", &x)"]
        for fn in funcs:
            content = f"// Q\nint main() {{ {fn}; return 0; }}\n// A\n"
            res = parse_c_template(content)
            self.assertEqual(res["status"], "error")
            self.assertIn("Validación semántica", res["reason"])

    def test_parse_exception_handling(self):
        # Passing invalid type to trigger exception in parse_c_template (lines 228-229)
        res = parse_c_template(None)
        self.assertEqual(res["status"], "error")
        self.assertIsNotNone(res["reason"])
