"""Интерфейс командной строки ассемблера УВМ."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .encoder import encode, encode_instruction, format_bytes
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
        help="режим тестирования: вывести байты команд на экран",
    )
    return parser


def read_source(path: str) -> str:
    """Прочитать исходный файл; при неудаче выбросить AssemblerError."""
    try:
        return Path(path).read_text(encoding=ENCODING)
    except OSError as error:
        raise AssemblerError(f"не удалось прочитать {path}: {error.strerror}")


def write_binary(path: str, code: bytes) -> None:
    """Записать машинный код в файл; при неудаче выбросить AssemblerError."""
    try:
        Path(path).write_bytes(code)
    except OSError as error:
        raise AssemblerError(f"не удалось записать {path}: {error.strerror}")


def print_machine_code(instructions: Sequence[Instruction]) -> None:
    """Вывести машинный код: байты одной команды на каждой строке."""
    for instruction in instructions:
        print(format_bytes(encode_instruction(instruction)))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Точка входа ассемблера; возвращает код завершения процесса."""
    args = build_arg_parser().parse_args(argv)
    try:
        instructions = translate(read_source(args.source))
        write_binary(args.output, encode(instructions))
    except AssemblerError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    if args.test:
        print_machine_code(instructions)
    print(f"Ассемблировано команд: {len(instructions)}")
    return EXIT_OK
