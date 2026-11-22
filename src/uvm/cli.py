"""Интерфейс командной строки ассемблера УВМ."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .translator import AssemblerError, Instruction, translate

EXIT_OK = 0
EXIT_ERROR = 1
ENCODING = "utf-8"


def build_arg_parser() -> argparse.ArgumentParser:
    """Создать разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="uvm",
        description="Ассемблер учебной виртуальной машины (вариант 31).",
    )
    parser.add_argument(
        "source", help="путь к исходному файлу с текстом программы"
    )
    parser.add_argument("output", help="путь к двоичному файлу-результату")
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="режим тестирования: вывести поля и значения команд",
    )
    return parser


def read_source(path: str) -> str:
    """Прочитать исходный файл; при неудаче выбросить AssemblerError."""
    try:
        return Path(path).read_text(encoding=ENCODING)
    except OSError as error:
        raise AssemblerError(f"не удалось прочитать {path}: {error.strerror}")


def print_internal(instructions: List[Instruction]) -> None:
    """Вывести внутреннее представление: по одной команде на строку."""
    for instruction in instructions:
        print(instruction.describe())


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Точка входа ассемблера; возвращает код завершения процесса."""
    args = build_arg_parser().parse_args(argv)
    try:
        instructions = translate(read_source(args.source))
    except AssemblerError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    if args.test:
        print_internal(instructions)
    else:
        print(
            "Этап 1: запись двоичного файла пока не реализована.",
            file=sys.stderr,
        )
    return EXIT_OK
