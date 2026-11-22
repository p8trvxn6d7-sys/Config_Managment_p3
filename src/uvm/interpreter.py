"""Интерфейс командной строки интерпретатора УВМ.

Запуск: python -m uvm.interpreter <program> <dump> <first:last>
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from .dump import write_dump
from .machine import Machine, VmError

EXIT_OK = 0
EXIT_ERROR = 1
RANGE_PATTERN = re.compile(r"(\d+):(\d+)")


def parse_range(text: str) -> Tuple[int, int]:
    """Разобрать диапазон адресов вида FIRST:LAST (границы включены)."""
    match = RANGE_PATTERN.fullmatch(text)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"ожидается диапазон вида FIRST:LAST, получено {text!r}"
        )
    return int(match.group(1)), int(match.group(2))


def build_arg_parser() -> argparse.ArgumentParser:
    """Создать разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="uvm.interpreter",
        description="Интерпретатор учебной виртуальной машины (вариант 31).",
    )
    parser.add_argument(
        "program", help="путь к бинарному файлу с ассемблированной программой"
    )
    parser.add_argument(
        "dump", help="путь к XML-файлу, куда будет сохранён дамп памяти"
    )
    parser.add_argument(
        "range",
        type=parse_range,
        metavar="FIRST:LAST",
        help="диапазон адресов памяти данных для дампа (границы включены)",
    )
    return parser


def read_program(path: str) -> bytes:
    """Прочитать бинарный файл программы; при неудаче выбросить VmError."""
    try:
        return Path(path).read_bytes()
    except OSError as error:
        raise VmError(f"не удалось прочитать {path}: {error.strerror}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Точка входа интерпретатора; возвращает код завершения процесса."""
    args = build_arg_parser().parse_args(argv)
    first, last = args.range
    try:
        machine = Machine(read_program(args.program))
        machine.run()
        write_dump(args.dump, machine.data, first, last)
    except VmError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(f"Выполнено команд: {machine.executed}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
