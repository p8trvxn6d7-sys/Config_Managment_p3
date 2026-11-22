"""Спецификация команд УВМ (вариант 31).

Модуль описывает только формат команд: код операции и разбивку на поля.
Выполнение команд относится к интерпретатору (этапы 3-4).
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


OPCODE_FIELD = Field("A", 0, 7)
REGISTER_B = Field("B", 8, 13)
REGISTER_C = Field("C", 14, 19)
VALUE_C = Field("C", 14, 44)


@dataclass(frozen=True)
class CommandSpec:
    """Описание команды: имя, код операции и поля-операнды."""

    name: str
    opcode: int
    operands: Tuple[Field, ...]

    @property
    def fields(self) -> Tuple[Field, ...]:
        """Все поля команды, начиная с кода операции A."""
        return (OPCODE_FIELD,) + self.operands


COMMANDS: Dict[str, CommandSpec] = {
    "LOAD": CommandSpec("LOAD", 140, (REGISTER_B, VALUE_C)),
    "READ": CommandSpec("READ", 21, (REGISTER_B, VALUE_C)),
    "WRITE": CommandSpec("WRITE", 171, (REGISTER_B, VALUE_C)),
    "ABS": CommandSpec("ABS", 146, (REGISTER_B, REGISTER_C)),
}
