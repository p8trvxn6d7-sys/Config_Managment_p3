"""Тесты интерпретатора: командная строка и программа копирования массива."""

import argparse
import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uvm.encoder import encode
from uvm.interpreter import EXIT_ERROR, EXIT_OK, main, parse_range
from uvm.translator import translate

EXAMPLE_FILE = (
    Path(__file__).resolve().parent.parent / "examples" / "copy_array.asm"
)

SOURCE_ARRAY = [7, 42, 13, 5, 99]
FIRST_SOURCE = 10
FIRST_COPY = 20
DUMP_RANGE = "10:24"
EXECUTED_LINE = "Выполнено команд: 20"


def run_cli(*args):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


def read_dump(path):
    """Прочитать XML-дамп и вернуть словарь «адрес -> значение»."""
    root = ET.parse(path).getroot()
    return {
        int(cell.get("address")): int(cell.get("value"))
        for cell in root.findall("cell")
    }


class ParseRangeTest(unittest.TestCase):
    """Разбор аргумента с диапазоном адресов."""

    def test_valid(self):
        """Диапазон вида FIRST:LAST."""
        self.assertEqual(parse_range("10:24"), (10, 24))
        self.assertEqual(parse_range("0:0"), (0, 0))

    def test_invalid(self):
        """Некорректные записи диапазона отклоняются."""
        for text in ("5", "a:b", "-1:3", "1:2:3", "1-2", ""):
            with self.subTest(text=text):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_range(text)


class CopyArrayTest(unittest.TestCase):
    """Тестовая программа: копирование массива с одного адреса на другой."""

    def setUp(self):
        """Ассемблировать программу копирования во временную папку."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.program = Path(self.folder.name) / "copy.bin"
        self.dump = Path(self.folder.name) / "dump.xml"
        source = EXAMPLE_FILE.read_text(encoding="utf-8")
        self.program.write_bytes(encode(translate(source)))

    def test_array_is_copied(self):
        """Копия совпадает с исходным массивом, остальное не тронуто."""
        code, out, _ = run_cli(str(self.program), str(self.dump), DUMP_RANGE)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines(), [EXECUTED_LINE])
        cells = read_dump(self.dump)
        expected = dict.fromkeys(range(10, 25), 0)
        for index, value in enumerate(SOURCE_ARRAY):
            expected[FIRST_SOURCE + index] = value
            expected[FIRST_COPY + index] = value
        self.assertEqual(cells, expected)

    def test_copy_equals_source(self):
        """Прямое сравнение двух массивов в дампе."""
        run_cli(str(self.program), str(self.dump), DUMP_RANGE)
        cells = read_dump(self.dump)
        count = len(SOURCE_ARRAY)
        source = [cells[FIRST_SOURCE + i] for i in range(count)]
        copy = [cells[FIRST_COPY + i] for i in range(count)]
        self.assertEqual(source, SOURCE_ARRAY)
        self.assertEqual(copy, source)

    def test_range_narrower_than_memory(self):
        """В дамп попадает только запрошенный диапазон."""
        run_cli(str(self.program), str(self.dump), "20:22")
        self.assertEqual(read_dump(self.dump), {20: 7, 21: 42, 22: 13})


class CliErrorsTest(unittest.TestCase):
    """Обработка ошибок в командной строке."""

    def setUp(self):
        """Создать временную папку."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.dump = Path(self.folder.name) / "dump.xml"

    def test_missing_program(self):
        """Отсутствующий бинарный файл."""
        code, out, err = run_cli("no_such.bin", str(self.dump), "0:1")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)
        self.assertFalse(self.dump.exists())

    def test_range_out_of_memory(self):
        """Диапазон за пределами памяти данных."""
        program = Path(self.folder.name) / "empty.bin"
        program.write_bytes(b"")
        code, _, err = run_cli(str(program), str(self.dump), "0:70000")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("диапазон", err)

    def test_broken_program(self):
        """Повреждённая программа сообщается со смещением команды."""
        program = Path(self.folder.name) / "broken.bin"
        program.write_bytes(bytes([0xFF]))
        code, _, err = run_cli(str(program), str(self.dump), "0:1")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("смещение 0", err)


if __name__ == "__main__":
    unittest.main()
