"""Тесты машинного кода: байтовые последовательности из спецификации."""

import unittest
from pathlib import Path

from uvm.encoder import encode, encode_instruction, format_bytes
from uvm.spec import COMMANDS
from uvm.translator import translate

EXAMPLE_FILE = (
    Path(__file__).resolve().parent.parent / "examples" / "spec_tests.asm"
)

SPEC_CASES = (
    (
        "LOAD",
        "r54 = 374",
        bytes([0x8C, 0xB6, 0x5D, 0x00, 0x00, 0x00]),
        "0x8C, 0xB6, 0x5D, 0x00, 0x00, 0x00",
    ),
    (
        "READ",
        "r9 = mem[514]",
        bytes([0x15, 0x89, 0x80, 0x00, 0x00, 0x00]),
        "0x15, 0x89, 0x80, 0x00, 0x00, 0x00",
    ),
    (
        "WRITE",
        "mem[737] = r54",
        bytes([0xAB, 0x76, 0xB8, 0x00, 0x00, 0x00]),
        "0xAB, 0x76, 0xB8, 0x00, 0x00, 0x00",
    ),
    (
        "ABS",
        "mem[r54] = abs(r9)",
        bytes([0x92, 0x89, 0x0D]),
        "0x92, 0x89, 0x0D",
    ),
)

MAX_REGISTER = (1 << 6) - 1
MAX_VALUE = (1 << 31) - 1


class SpecBytesTest(unittest.TestCase):
    """Проверка тестов из спецификации варианта 31."""

    def test_each_command(self):
        """Каждая команда даёт байты из спецификации."""
        for command, source, expected, _ in SPEC_CASES:
            with self.subTest(command=command):
                [instruction] = translate(source)
                self.assertEqual(encode_instruction(instruction), expected)

    def test_format_bytes(self):
        """Строка байтов совпадает с форматом спецификации."""
        for command, _, code, text in SPEC_CASES:
            with self.subTest(command=command):
                self.assertEqual(format_bytes(code), text)

    def test_example_file(self):
        """Файл examples/spec_tests.asm даёт все тестовые последовательности."""
        source = EXAMPLE_FILE.read_text(encoding="utf-8")
        expected = b"".join(case[2] for case in SPEC_CASES)
        self.assertEqual(encode(translate(source)), expected)


class EncodingTest(unittest.TestCase):
    """Проверка размера команд и граничных значений."""

    def test_instruction_sizes(self):
        """Длина кода команды равна размеру из спецификации."""
        for command, source, _, _ in SPEC_CASES:
            with self.subTest(command=command):
                [instruction] = translate(source)
                size = COMMANDS[command].size
                self.assertEqual(len(encode_instruction(instruction)), size)

    def test_empty_program(self):
        """Пустая программа даёт пустой машинный код."""
        self.assertEqual(encode([]), b"")

    def test_max_load(self):
        """Максимальные значения полей помещаются в 6 байт."""
        [instruction] = translate(f"r{MAX_REGISTER} = {MAX_VALUE}")
        code = encode_instruction(instruction)
        self.assertEqual(code, bytes([0x8C, 0xFF, 0xFF, 0xFF, 0xFF, 0x1F]))

    def test_max_abs(self):
        """Максимальные значения полей помещаются в 3 байта."""
        source = f"mem[r{MAX_REGISTER}] = abs(r{MAX_REGISTER})"
        [instruction] = translate(source)
        code = encode_instruction(instruction)
        self.assertEqual(code, bytes([0x92, 0xFF, 0x0F]))

    def test_programs_are_concatenated(self):
        """Команды разных размеров записываются подряд без выравнивания."""
        source = "r1 = 2\nmem[r1] = abs(r1)\nmem[3] = r1"
        code = encode(translate(source))
        self.assertEqual(len(code), 6 + 3 + 6)


if __name__ == "__main__":
    unittest.main()
