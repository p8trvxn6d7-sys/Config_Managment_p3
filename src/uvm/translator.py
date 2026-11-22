"""Трансляция программы на языке ассемблера во внутреннее представление.

Внутреннее представление - список объектов Instruction: имя команды и
упорядоченный словарь «имя поля -> значение» (A, B, C, ...). Значение
поля - число, как оно записывается в биты команды. Знаковая константа
команды LOAD хранится в поле в дополнительном коде.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Pattern, Tuple

from .spec import COMMANDS, OPCODE_FIELD, Field

COMMENT_MARK = "#"
FIRST_LINE_NUMBER = 1
NEGATIVE_SIGN = "-"
HEX_PREFIX = "0x"
BIN_PREFIX = "0b"
HEX_BASE = 16
BIN_BASE = 2
DEC_BASE = 10

NUMBER = r"(0x[0-9a-f]+|0b[01]+|\d+)"
SIGNED_NUMBER = r"(-?(?:0x[0-9a-f]+|0b[01]+|\d+))"
REGISTER = r"r(\d+)"


class AssemblerError(Exception):
    """Ошибка трансляции; хранит номер строки исходного текста."""

    def __init__(self, message: str, line: int = None):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        return f"строка {self.line}: {self.message}"


@dataclass
class Instruction:
    """Команда во внутреннем представлении."""

    command: str
    fields: Dict[str, int]

    def describe(self) -> str:
        """Вернуть поля в формате тестов спецификации: A=140, B=54, C=374."""
        pairs = (f"{name}={value}" for name, value in self.fields.items())
        return ", ".join(pairs)


@dataclass(frozen=True)
class SyntaxRule:
    """Синтаксическая форма команды.

    operands - имена полей, которым соответствуют группы регулярного
    выражения (по порядку следования в тексте команды).
    signed - имена полей, значение которых записывается со знаком
    (в дополнительном коде).
    """

    command: str
    regex: Pattern
    operands: Tuple[str, ...]
    signed: Tuple[str, ...] = ()


RULES = (
    SyntaxRule(
        "LOAD",
        re.compile(rf"{REGISTER}\s*=\s*{SIGNED_NUMBER}"),
        ("B", "C"),
        ("C",),
    ),
    SyntaxRule(
        "READ",
        re.compile(rf"{REGISTER}\s*=\s*mem\[\s*{NUMBER}\s*\]"),
        ("B", "C"),
    ),
    SyntaxRule(
        "WRITE",
        re.compile(rf"mem\[\s*{NUMBER}\s*\]\s*=\s*{REGISTER}"),
        ("C", "B"),
    ),
    SyntaxRule(
        "ABS",
        re.compile(rf"mem\[\s*{REGISTER}\s*\]\s*=\s*abs\(\s*{REGISTER}\s*\)"),
        ("C", "B"),
    ),
)


def parse_number(text: str) -> int:
    """Разобрать целое число: десятичное, 0x... или 0b..., со знаком минус."""
    if text.startswith(NEGATIVE_SIGN):
        return -parse_number(text[len(NEGATIVE_SIGN):])
    if text.startswith(HEX_PREFIX):
        return int(text, HEX_BASE)
    if text.startswith(BIN_PREFIX):
        return int(text, BIN_BASE)
    return int(text, DEC_BASE)


def check_fits(field: Field, value: int) -> None:
    """Убедиться, что значение помещается в поле, иначе выбросить ошибку."""
    if value & field.mask != value:
        raise AssemblerError(
            f"значение {value} не помещается в поле {field.name} "
            f"({field.width} бит, максимум {field.mask})"
        )


def check_signed_fits(field: Field, value: int) -> None:
    """Убедиться, что знаковое значение помещается в поле."""
    if not field.signed_min <= value <= field.signed_max:
        raise AssemblerError(
            f"значение {value} не помещается в знаковое поле {field.name} "
            f"({field.width} бит, от {field.signed_min} "
            f"до {field.signed_max})"
        )


def to_field_value(field: Field, value: int, signed: bool) -> int:
    """Получить значение поля: беззнаковое или в дополнительном коде."""
    if not signed:
        check_fits(field, value)
        return value
    check_signed_fits(field, value)
    return value & field.mask


def build_instruction(rule: SyntaxRule, groups: Tuple[str, ...]) -> Instruction:
    """Собрать команду по найденной форме и значениям операндов."""
    spec = COMMANDS[rule.command]
    values = {OPCODE_FIELD.name: spec.opcode}
    for name, text in zip(rule.operands, groups):
        values[name] = parse_number(text)
    fields = {}
    for field in spec.fields:
        signed = field.name in rule.signed
        fields[field.name] = to_field_value(field, values[field.name], signed)
    return Instruction(rule.command, fields)


def translate_line(text: str) -> Instruction:
    """Преобразовать одну строку (без комментария, в нижнем регистре)."""
    for rule in RULES:
        match = rule.regex.fullmatch(text)
        if match:
            return build_instruction(rule, match.groups())
    raise AssemblerError(f"неизвестная команда или ошибка синтаксиса: {text!r}")


def strip_comment(line: str) -> str:
    """Убрать комментарий (от символа # до конца строки)."""
    return line.split(COMMENT_MARK, 1)[0]


def translate(source: str) -> List[Instruction]:
    """Преобразовать текст программы во внутреннее представление."""
    instructions = []
    lines = source.splitlines()
    for number, raw in enumerate(lines, start=FIRST_LINE_NUMBER):
        text = strip_comment(raw).strip().lower()
        if not text:
            continue
        try:
            instructions.append(translate_line(text))
        except AssemblerError as error:
            raise AssemblerError(error.message, number) from error
    return instructions
