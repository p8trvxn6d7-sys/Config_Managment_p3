"""Преобразование машинного кода во внутреннее представление.

Обратная операция к encoder: по смещению в байтовой последовательности
определяется команда по коду операции (младший байт), затем из числа
(little-endian) извлекаются поля по границам битов из спецификации.
"""

from typing import Dict, Tuple

from .spec import COMMANDS, OPCODE_FIELD, CommandSpec
from .translator import Instruction

BYTE_ORDER = "little"

SPEC_BY_OPCODE: Dict[int, CommandSpec] = {
    spec.opcode: spec for spec in COMMANDS.values()
}


class DecodeError(Exception):
    """Ошибка разбора машинного кода."""


def find_spec(code: bytes, offset: int) -> CommandSpec:
    """Найти описание команды по коду операции в позиции offset."""
    if offset >= len(code):
        raise DecodeError(f"смещение {offset} за концом программы")
    opcode = code[offset] & OPCODE_FIELD.mask
    spec = SPEC_BY_OPCODE.get(opcode)
    if spec is None:
        raise DecodeError(f"неизвестный код операции {opcode}")
    return spec


def decode_instruction(
    code: bytes, offset: int = 0
) -> Tuple[Instruction, int]:
    """Разобрать команду по смещению; вернуть команду и её размер."""
    spec = find_spec(code, offset)
    chunk = code[offset : offset + spec.size]
    if len(chunk) < spec.size:
        raise DecodeError(
            f"команда {spec.name} обрезана: нужно {spec.size} байт, "
            f"осталось {len(chunk)}"
        )
    value = int.from_bytes(chunk, BYTE_ORDER)
    fields = {
        field.name: (value >> field.first_bit) & field.mask
        for field in spec.fields
    }
    return Instruction(spec.name, fields), spec.size
