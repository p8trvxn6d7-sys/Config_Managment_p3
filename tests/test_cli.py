"""Тесты интерфейса командной строки."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from uvm.cli import EXIT_ERROR, EXIT_OK, main

EXAMPLE_FILE = (
    Path(__file__).resolve().parent.parent / "examples" / "spec_tests.asm"
)

EXPECTED_LINES = [
    "0x8C, 0xB6, 0x5D, 0x00, 0x00, 0x00",
    "0x15, 0x89, 0x80, 0x00, 0x00, 0x00",
    "0xAB, 0x76, 0xB8, 0x00, 0x00, 0x00",
    "0x92, 0x89, 0x0D",
]
EXPECTED_BINARY = bytes(
    [0x8C, 0xB6, 0x5D, 0x00, 0x00, 0x00]
    + [0x15, 0x89, 0x80, 0x00, 0x00, 0x00]
    + [0xAB, 0x76, 0xB8, 0x00, 0x00, 0x00]
    + [0x92, 0x89, 0x0D]
)
COUNT_LINE = "Ассемблировано команд: 4"


def run_cli(*args):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Проверка режима тестирования, записи файла и ошибок."""

    def setUp(self):
        """Создать временную папку для результатов."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.output = Path(self.folder.name) / "out.bin"

    def test_test_mode_output(self):
        """В режиме --test выводятся байты команд и число команд."""
        code, out, _ = run_cli(str(EXAMPLE_FILE), str(self.output), "--test")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines(), EXPECTED_LINES + [COUNT_LINE])

    def test_binary_file(self):
        """Двоичный файл содержит все команды подряд."""
        run_cli(str(EXAMPLE_FILE), str(self.output))
        self.assertEqual(self.output.read_bytes(), EXPECTED_BINARY)

    def test_count_without_test_mode(self):
        """Без --test выводится только число команд."""
        code, out, _ = run_cli(str(EXAMPLE_FILE), str(self.output))
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines(), [COUNT_LINE])

    def test_missing_source(self):
        """Отсутствующий исходный файл даёт код ошибки и сообщение."""
        code, out, err = run_cli("no_such_file.asm", str(self.output))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)
        self.assertFalse(self.output.exists())

    def test_syntax_error_reports_line(self):
        """Синтаксическая ошибка сообщается с номером строки."""
        source = Path(self.folder.name) / "bad.asm"
        source.write_text("r1 = 1\nbad line\n", encoding="utf-8")
        code, _, err = run_cli(str(source), str(self.output), "--test")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("строка 2", err)
        self.assertFalse(self.output.exists())

    def test_unwritable_output(self):
        """Недоступный путь результата даёт код ошибки и сообщение."""
        bad_output = Path(self.folder.name) / "no_dir" / "out.bin"
        code, out, err = run_cli(str(EXAMPLE_FILE), str(bad_output))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("не удалось записать", err)


if __name__ == "__main__":
    unittest.main()
