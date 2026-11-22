"""Спецификация команд УВМ (вариант 31).

Модуль описывает только формат команд: код операции, разбивку на поля и
размер в байтах. Выполнение команд относится к интерпретатору.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Field:
    """Поле команды: имя и диапазон битов (границы включительно)."""

    name: str
    first_bit: int
    last_bit: int

    @property
    def width(self) -> int:
        """Ширина поля в битах."""
        return self.last_bit - self.first_bit + 1

    @property
    def mask(self) -> int:
        """Максимальное значение, которое помещается в поле."""
        return (1 << self.width) - 1

    @property
    def signed_min(self) -> int:
        """Наименьшее знаковое число (дополнительный код) в поле."""
        return -(1 << (self.width - 1))

    @property
    def signed_max(self) -> int:
        """Наибольшее знаковое число (дополнительный код) в поле."""
        return (1 << (self.width - 1)) - 1

    def to_signed(self, raw: int) -> int:
        """Преобразовать значение поля в знаковое число."""
        sign_bit = 1 << (self.width - 1)
        return raw - (1 << self.width) if raw & sign_bit else raw


OPCODE_FIELD = Field("A", 0, 7)
REGISTER_B = Field("B", 8, 13)
REGISTER_C = Field("C", 14, 19)
VALUE_C = Field("C", 14, 44)

LONG_SIZE = 6
SHORT_SIZE = 3


@dataclass(frozen=True)
class CommandSpec:
    """Описание команды: имя, код операции, поля-операнды и размер."""

    name: str
    opcode: int
    operands: Tuple[Field, ...]
    size: int

    @property
    def fields(self) -> Tuple[Field, ...]:
        """Все поля команды, начиная с кода операции A."""
        return (OPCODE_FIELD,) + self.operands


COMMANDS: Dict[str, CommandSpec] = {
    "LOAD": CommandSpec("LOAD", 140, (REGISTER_B, VALUE_C), LONG_SIZE),
    "READ": CommandSpec("READ", 21, (REGISTER_B, VALUE_C), LONG_SIZE),
    "WRITE": CommandSpec("WRITE", 171, (REGISTER_B, VALUE_C), LONG_SIZE),
    "ABS": CommandSpec("ABS", 146, (REGISTER_B, REGISTER_C), SHORT_SIZE),
}
