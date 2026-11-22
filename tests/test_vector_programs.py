"""Тесты этапа 5: поэлементный abs() над вектором длины 5."""

import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uvm.encoder import encode
from uvm.interpreter import EXIT_OK, main
from uvm.translator import translate

PROGRAMS_DIR = (
    Path(__file__).resolve().parent.parent / "examples" / "stage5"
)

VECTOR_LENGTH = 5
ZERO = 0
SOURCE_BASE = 0
RESULT_BASE = 5
DUMP_RANGE = "0:9"
EXECUTED_LINE = "Выполнено команд: 25"
PROGRAM_SIZE = VECTOR_LENGTH * (6 + 6) + VECTOR_LENGTH * (6 + 6 + 3)

CASES = (
    ("vector_abs.asm", [-3, 8, -15, 0, 42]),
    ("example_mixed.asm", [-100, 250, -7, 3, -1]),
    ("example_negative.asm", [-1, -20, -300, -4000, -50000]),
    ("example_boundaries.asm", [-1073741824, 1073741823, 0, -1, 1]),
)


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


def vector_at(cells, base):
    """Вернуть вектор из пяти ячеек дампа, начиная с адреса base."""
    return [cells[base + index] for index in range(VECTOR_LENGTH)]


class VectorProgramsTest(unittest.TestCase):
    """Программы из examples/stage5: ассемблер -> интерпретатор -> дамп."""

    def setUp(self):
        """Создать временную папку для результатов."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.program = Path(self.folder.name) / "program.bin"
        self.dump = Path(self.folder.name) / "dump.xml"

    def run_case(self, name):
        """Ассемблировать и выполнить программу; вернуть вывод и дамп."""
        source = (PROGRAMS_DIR / name).read_text(encoding="utf-8")
        self.program.write_bytes(encode(translate(source)))
        code, out, _ = run_cli(str(self.program), str(self.dump), DUMP_RANGE)
        return code, out, read_dump(self.dump)

    def test_run_is_successful(self):
        """Все 25 команд выполняются без ошибок."""
        for name, _ in CASES:
            with self.subTest(program=name):
                code, out, _ = self.run_case(name)
                self.assertEqual(code, EXIT_OK)
                self.assertEqual(out.splitlines(), [EXECUTED_LINE])

    def test_program_size(self):
        """Размер двоичного файла одинаков для всех программ."""
        for name, _ in CASES:
            with self.subTest(program=name):
                self.run_case(name)
                self.assertEqual(self.program.stat().st_size, PROGRAM_SIZE)

    def test_source_vector_is_stored(self):
        """Исходный вектор записан по адресам 0..4 и не изменился."""
        for name, values in CASES:
            with self.subTest(program=name):
                _, _, cells = self.run_case(name)
                self.assertEqual(vector_at(cells, SOURCE_BASE), values)

    def test_result_vector(self):
        """Новый вектор по адресам 5..9 содержит модули элементов."""
        for name, values in CASES:
            with self.subTest(program=name):
                _, _, cells = self.run_case(name)
                expected = [abs(value) for value in values]
                self.assertEqual(vector_at(cells, RESULT_BASE), expected)

    def test_result_is_not_negative(self):
        """В результате нет отрицательных чисел."""
        for name, _ in CASES:
            with self.subTest(program=name):
                _, _, cells = self.run_case(name)
                result = vector_at(cells, RESULT_BASE)
                self.assertTrue(all(value >= ZERO for value in result))

    def test_dump_has_only_two_vectors(self):
        """Дамп 0:9 состоит из исходного и результирующего векторов."""
        _, _, cells = self.run_case(CASES[0][0])
        self.assertEqual(sorted(cells), list(range(10)))

    def test_all_programs_are_covered(self):
        """Каждая программа из examples/stage5 проверяется этим тестом."""
        found = sorted(path.name for path in PROGRAMS_DIR.glob("*.asm"))
        self.assertEqual(found, sorted(name for name, _ in CASES))


if __name__ == "__main__":
    unittest.main()
