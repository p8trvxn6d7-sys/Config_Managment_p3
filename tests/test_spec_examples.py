"""Тесты из спецификации УВМ: идентичность полей и их значений."""

import unittest
from pathlib import Path

from uvm.translator import translate

EXAMPLE_FILE = (
    Path(__file__).resolve().parent.parent / "examples" / "spec_tests.asm"
)

SPEC_CASES = (
    ("LOAD", "r54 = 374", {"A": 140, "B": 54, "C": 374}),
    ("READ", "r9 = mem[514]", {"A": 21, "B": 9, "C": 514}),
    ("WRITE", "mem[737] = r54", {"A": 171, "B": 54, "C": 737}),
    ("ABS", "mem[r54] = abs(r9)", {"A": 146, "B": 9, "C": 54}),
)

SPEC_DESCRIPTIONS = (
    "A=140, B=54, C=374",
    "A=21, B=9, C=514",
    "A=171, B=54, C=737",
    "A=146, B=9, C=54",
)


class SpecExamplesTest(unittest.TestCase):
    """Проверка тестов из спецификации варианта 31."""

    def test_each_command(self):
        """Каждая команда даёт поля и значения из спецификации."""
        for command, source, fields in SPEC_CASES:
            with self.subTest(command=command):
                [instruction] = translate(source)
                self.assertEqual(instruction.command, command)
                self.assertEqual(instruction.fields, fields)

    def test_describe_format(self):
        """Вывод в режиме тестирования совпадает с форматом спецификации."""
        for (_, source, _), expected in zip(SPEC_CASES, SPEC_DESCRIPTIONS):
            with self.subTest(source=source):
                [instruction] = translate(source)
                self.assertEqual(instruction.describe(), expected)

    def test_example_file(self):
        """Файл examples/spec_tests.asm содержит все тесты по порядку."""
        source = EXAMPLE_FILE.read_text(encoding="utf-8")
        result = [item.describe() for item in translate(source)]
        self.assertEqual(result, list(SPEC_DESCRIPTIONS))


if __name__ == "__main__":
    unittest.main()
