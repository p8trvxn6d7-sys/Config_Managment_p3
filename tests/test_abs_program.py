"""Тестовая программа этапа 4: abs() с сохранением результата в память."""

import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uvm.encoder import encode
from uvm.interpreter import EXIT_OK, main
from uvm.translator import translate

EXAMPLE_FILE = (
    Path(__file__).resolve().parent.parent / "examples" / "abs_demo.asm"
)

ORIGINALS = [-17, 25, 0, -1073741824, 1073741823]
FIRST_ORIGINAL = 30
FIRST_RESULT = 40
DUMP_RANGE = "30:44"
EXECUTED_LINE = "Выполнено команд: 20"
PROGRAM_SIZE = 5 * (6 + 6 + 6 + 3)


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


class AbsProgramTest(unittest.TestCase):
    """Программа examples/abs_demo.asm: ассемблер -> интерпретатор -> дамп."""

    def setUp(self):
        """Ассемблировать программу и выполнить её."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.program = Path(self.folder.name) / "abs.bin"
        self.dump = Path(self.folder.name) / "dump.xml"
        source = EXAMPLE_FILE.read_text(encoding="utf-8")
        self.program.write_bytes(encode(translate(source)))
        self.code, self.out, _ = run_cli(
            str(self.program), str(self.dump), DUMP_RANGE
        )
        self.cells = read_dump(self.dump)

    def test_program_size(self):
        """Четыре команды на значение: три по 6 байт и abs в 3 байта."""
        self.assertEqual(self.program.stat().st_size, PROGRAM_SIZE)

    def test_run_is_successful(self):
        """Все 20 команд выполнены без ошибок."""
        self.assertEqual(self.code, EXIT_OK)
        self.assertEqual(self.out.splitlines(), [EXECUTED_LINE])

    def test_originals_are_stored(self):
        """Исходные значения сохранены по адресам 30..34."""
        stored = [self.cells[FIRST_ORIGINAL + i] for i in range(5)]
        self.assertEqual(stored, ORIGINALS)

    def test_results(self):
        """Результаты abs() лежат по адресам 40..44."""
        results = [self.cells[FIRST_RESULT + i] for i in range(5)]
        self.assertEqual(results, [17, 25, 0, 1073741824, 1073741823])

    def test_results_equal_python_abs(self):
        """Результаты совпадают с abs() языка Python."""
        results = [self.cells[FIRST_RESULT + i] for i in range(5)]
        self.assertEqual(results, [abs(value) for value in ORIGINALS])

    def test_gap_is_untouched(self):
        """Ячейки между исходными значениями и результатами не тронуты."""
        gap = [self.cells[address] for address in range(35, 40)]
        self.assertEqual(gap, [0] * 5)


if __name__ == "__main__":
    unittest.main()
