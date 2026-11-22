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


def run_cli(*args):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Проверка режима тестирования и обработки ошибок."""

    def test_test_mode_output(self):
        """В режиме --test выводятся поля и значения команд."""
        code, out, _ = run_cli(str(EXAMPLE_FILE), "out.bin", "--test")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            out.splitlines(),
            [
                "A=140, B=54, C=374",
                "A=21, B=9, C=514",
                "A=171, B=54, C=737",
                "A=146, B=9, C=54",
            ],
        )

    def test_missing_source(self):
        """Отсутствующий исходный файл даёт код ошибки и сообщение."""
        code, out, err = run_cli("no_such_file.asm", "out.bin", "--test")
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_syntax_error_reports_line(self):
        """Синтаксическая ошибка сообщается с номером строки."""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.asm"
            source.write_text("r1 = 1\nbad line\n", encoding="utf-8")
            code, _, err = run_cli(str(source), "out.bin", "--test")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("строка 2", err)


if __name__ == "__main__":
    unittest.main()
