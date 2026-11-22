"""Тесты декодера: машинный код -> внутреннее представление."""

import unittest

from uvm.decoder import DecodeError, decode_instruction
from uvm.encoder import encode_instruction
from uvm.translator import Instruction, translate

SPEC_CASES = (
    (
        bytes([0x8C, 0xB6, 0x5D, 0x00, 0x00, 0x00]),
        "LOAD",
        {"A": 140, "B": 54, "C": 374},
    ),
    (
        bytes([0x15, 0x89, 0x80, 0x00, 0x00, 0x00]),
        "READ",
        {"A": 21, "B": 9, "C": 514},
    ),
    (
        bytes([0xAB, 0x76, 0xB8, 0x00, 0x00, 0x00]),
        "WRITE",
        {"A": 171, "B": 54, "C": 737},
    ),
    (bytes([0x92, 0x89, 0x0D]), "ABS", {"A": 146, "B": 9, "C": 54}),
)

MAX_REGISTER = (1 << 6) - 1
MAX_VALUE = (1 << 31) - 1


class SpecDecodeTest(unittest.TestCase):
    """Байтовые последовательности из спецификации разбираются в поля."""

    def test_each_command(self):
        """Каждая последовательность даёт команду, поля и размер."""
        for code, command, fields in SPEC_CASES:
            with self.subTest(command=command):
                instruction, size = decode_instruction(code)
                self.assertEqual(instruction.command, command)
                self.assertEqual(instruction.fields, fields)
                self.assertEqual(size, len(code))

    def test_offset(self):
        """Команда разбирается по смещению внутри программы."""
        program = b"".join(case[0] for case in SPEC_CASES)
        offset = len(SPEC_CASES[0][0]) + len(SPEC_CASES[1][0])
        instruction, _ = decode_instruction(program, offset)
        self.assertEqual(instruction.command, "WRITE")


class RoundTripTest(unittest.TestCase):
    """Кодирование и декодирование взаимно обратны."""

    def test_round_trip(self):
        """decode(encode(x)) возвращает исходную команду."""
        sources = (
            "r0 = 0",
            f"r{MAX_REGISTER} = {MAX_VALUE}",
            f"r1 = mem[{MAX_VALUE}]",
            f"mem[{MAX_VALUE}] = r{MAX_REGISTER}",
            f"mem[r{MAX_REGISTER}] = abs(r0)",
            f"mem[r0] = abs(r{MAX_REGISTER})",
            "mem[r12] = abs(r34)",
        )
        for source in sources:
            with self.subTest(source=source):
                [original] = translate(source)
                code = encode_instruction(original)
                decoded, size = decode_instruction(code)
                self.assertEqual(decoded, original)
                self.assertEqual(size, len(code))
                self.assertIsInstance(decoded, Instruction)


class DecodeErrorsTest(unittest.TestCase):
    """Диагностика некорректного машинного кода."""

    def test_unknown_opcode(self):
        """Неизвестный код операции."""
        with self.assertRaises(DecodeError):
            decode_instruction(bytes([0xFF, 0x00, 0x00]))

    def test_truncated_command(self):
        """Команда обрезана посередине."""
        with self.assertRaises(DecodeError):
            decode_instruction(bytes([0x8C, 0xB6, 0x5D]))

    def test_offset_past_end(self):
        """Смещение за концом программы."""
        with self.assertRaises(DecodeError):
            decode_instruction(bytes([0x92, 0x89, 0x0D]), 3)


if __name__ == "__main__":
    unittest.main()
