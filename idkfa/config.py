"""Módulo de configuración centralizada y tipada para idkfa."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import os

DEFAULT_SUBSTITUTIONS: Dict[str, str] = {
    "==": "⩵",
    "=": "＝",
    ";": ";",
    "#": "＃",
    "{": "｛",
    "}": "｝",
    "    ": "    ",  # Espacio de 4 caracteres
    "\n": "↵\n",
    ">": "＞",
    "<": "＜",
    "[": "［",
    "]": "］",
}

@dataclass
class AppConfig:
    source_directory: str = "templates"
    output_file: str = "cuestionario_moodle.xml"
    questions_per_template: int = 5
    moodle_base_category: str = "programacion1_gen_codigo"
    compiler: str = "gcc"
    compiler_flags: List[str] = field(default_factory=lambda: ["-Wall", "-Wextra"])
    execution_timeout: int = 3
    min_distractors: int = 3
    default_grade: str = "1.0000000"
    default_penalty: str = "0.3333333"
    compilation_error_log: str = "compile_errors.log"
    parsing_error_log: str = "parsing_errors.log"
    substitutions: Dict[str, str] = field(default_factory=lambda: DEFAULT_SUBSTITUTIONS.copy())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_directory": self.source_directory,
            "output_file": self.output_file,
            "questions_per_template": self.questions_per_template,
            "moodle_base_category": self.moodle_base_category,
            "compiler": self.compiler,
            "compiler_flags": self.compiler_flags,
            "execution_timeout": self.execution_timeout,
            "min_distractors": self.min_distractors,
            "default_grade": self.default_grade,
            "default_penalty": self.default_penalty,
            "compilation_error_log": self.compilation_error_log,
            "parsing_error_log": self.parsing_error_log,
            "substitutions": self.substitutions,
        }

    @classmethod
    def load_from_file(cls, path: str) -> "AppConfig":
        """Carga configuración desde un archivo JSON si existe."""
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})

# Diccionario compatible hacia atrás
CONFIG: Dict[str, Any] = AppConfig().to_dict()
