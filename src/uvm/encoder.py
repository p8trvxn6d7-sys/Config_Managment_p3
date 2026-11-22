"""Преобразование промежуточного представления в машинный код УВМ.

Поля команды собираются в одно целое число: поле занимает биты от
first_bit до last_bit. Число записывается в байты от младшего к старшему
(little-endian), длина записи равна размеру команды из спецификации.
"""

from typing import Iterable

from .spec import COMMANDS
from .translator import Instruction

BYTE_ORDER = "little"
BYTE_SEPARATOR = ", "


def encode_instruction(instruction: Instruction) -> bytes:
    """Преобразовать одну команду в последовательность байтов."""
    spec = COMMANDS[instruction.command]
    value = 0
    for field in spec.fields:
        value |= instruction.fields[field.name] << field.first_bit
    return value.to_bytes(spec.size, BYTE_ORDER)


def encode(instructions: Iterable[Instruction]) -> bytes:
    """Преобразовать программу в машинный код (команды подряд)."""
    return b"".join(encode_instruction(item) for item in instructions)


def format_bytes(code: bytes) -> str:
    """Записать байты в формате тестов спецификации: 0x8C, 0xB6, ..."""
    return BYTE_SEPARATOR.join(f"0x{byte:02X}" for byte in code)
