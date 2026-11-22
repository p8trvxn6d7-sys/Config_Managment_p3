"""Тесты транслятора: синтаксис, границы полей, диагностика ошибок."""

import unittest

from uvm.spec import COMMANDS
from uvm.translator import RULES, AssemblerError, translate

MAX_REGISTER = (1 << 6) - 1
MAX_VALUE = (1 << 31) - 1
MAX_CONSTANT = (1 << 30) - 1
MIN_CONSTANT = -(1 << 30)


class SyntaxTest(unittest.TestCase):
    """Проверка разбора текста программы."""

    def test_empty_program(self):
        """Пустая программа даёт пустой список команд."""
        self.assertEqual(translate(""), [])
        self.assertEqual(translate("\n  \n# только комментарий\n"), [])

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки пропускаются."""
        source = "# начало\n\nr1 = 5  # константа\n\n"
        self.assertEqual(len(translate(source)), 1)

    def test_case_and_spaces(self):
        """Регистр букв и пробелы не влияют на результат."""
        variants = ("r3=7", "R3 = 7", "  r3   =   7  ")
        expected = translate("r3 = 7")[0].fields
        for source in variants:
            with self.subTest(source=source):
                self.assertEqual(translate(source)[0].fields, expected)

    def test_number_bases(self):
        """Поддерживаются десятичные, шестнадцатеричные и двоичные числа."""
        for source in ("r1 = 255", "r1 = 0xFF", "r1 = 0b11111111"):
            with self.subTest(source=source):
                self.assertEqual(translate(source)[0].fields["C"], 255)

    def test_memory_spaces(self):
        """Пробелы внутри квадратных скобок допускаются."""
        [read, write, unary] = translate(
            "r1 = mem[ 10 ]\nmem[ 20 ] = r2\nmem[ r3 ] = abs( r4 )"
        )
        self.assertEqual(read.fields["C"], 10)
        self.assertEqual(write.fields["C"], 20)
        self.assertEqual(unary.fields, {"A": 146, "B": 4, "C": 3})

    def test_program_order(self):
        """Порядок команд в результате совпадает с порядком в тексте."""
        source = "r1 = 1\nr2 = mem[2]\nmem[3] = r1"
        names = [item.command for item in translate(source)]
        self.assertEqual(names, ["LOAD", "READ", "WRITE"])


class SignedConstantTest(unittest.TestCase):
    """Константа команды LOAD - знаковая (дополнительный код, 31 бит)."""

    def test_negative_constant_field(self):
        """Отрицательная константа записывается в поле C в доп. коде."""
        cases = (
            ("r1 = -1", MAX_VALUE),
            ("r1 = -5", MAX_VALUE - 4),
            ("r1 = -0x10", MAX_VALUE - 15),
            ("r1 = -0b101", MAX_VALUE - 4),
            ("r1 = -0", 0),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(translate(source)[0].fields["C"], expected)

    def test_positive_constant_is_unchanged(self):
        """Неотрицательная константа записывается как есть."""
        self.assertEqual(translate("r1 = 374")[0].fields["C"], 374)


class LimitsTest(unittest.TestCase):
    """Проверка границ значений полей."""

    def test_register_bounds(self):
        """Номер регистра: максимум 63."""
        translate(f"r{MAX_REGISTER} = 0")
        with self.assertRaises(AssemblerError):
            translate(f"r{MAX_REGISTER + 1} = 0")

    def test_address_bounds(self):
        """Адрес памяти - беззнаковый, максимум 2^31 - 1."""
        translate(f"r0 = mem[{MAX_VALUE}]")
        translate(f"mem[{MAX_VALUE}] = r0")
        with self.assertRaises(AssemblerError):
            translate(f"r0 = mem[{MAX_VALUE + 1}]")
        with self.assertRaises(AssemblerError):
            translate(f"mem[{MAX_VALUE + 1}] = r0")

    def test_constant_bounds(self):
        """Константа LOAD: от -2^30 до 2^30 - 1."""
        translate(f"r0 = {MAX_CONSTANT}")
        translate(f"r0 = {MIN_CONSTANT}")
        with self.assertRaises(AssemblerError):
            translate(f"r0 = {MAX_CONSTANT + 1}")
        with self.assertRaises(AssemblerError):
            translate(f"r0 = {MIN_CONSTANT - 1}")

    def test_abs_register_bounds(self):
        """В команде abs оба регистра ограничены 6 битами, поле C - тоже."""
        translate(f"mem[r{MAX_REGISTER}] = abs(r{MAX_REGISTER})")
        with self.assertRaises(AssemblerError):
            translate(f"mem[r{MAX_REGISTER + 1}] = abs(r0)")
        with self.assertRaises(AssemblerError):
            translate(f"mem[r0] = abs(r{MAX_REGISTER + 1})")


class ErrorsTest(unittest.TestCase):
    """Проверка диагностики ошибок."""

    def test_unknown_command(self):
        """Неизвестная команда сообщается с номером строки."""
        with self.assertRaises(AssemblerError) as context:
            translate("r1 = 1\n\nnop\n")
        self.assertEqual(context.exception.line, 3)
        self.assertIn("строка 3", str(context.exception))

    def test_negative_address(self):
        """Отрицательные адреса не поддерживаются."""
        for source in ("r1 = mem[-5]", "mem[-5] = r1"):
            with self.subTest(source=source):
                with self.assertRaises(AssemblerError):
                    translate(source)

    def test_constant_error_reports_line(self):
        """Выход константы за границы сообщается с номером строки."""
        with self.assertRaises(AssemblerError) as context:
            translate(f"r1 = 1\nr2 = {MAX_CONSTANT + 1}")
        self.assertEqual(context.exception.line, 2)
        self.assertIn("знаков", str(context.exception))

    def test_indirect_write_is_not_supported(self):
        """Косвенная запись mem[rN] = rM в этом варианте не существует."""
        with self.assertRaises(AssemblerError):
            translate("mem[r1] = r2")


class RulesTest(unittest.TestCase):
    """Согласованность таблицы синтаксиса со спецификацией."""

    def test_rules_cover_all_commands(self):
        """Для каждой команды спецификации есть ровно одна форма записи."""
        names = sorted(rule.command for rule in RULES)
        self.assertEqual(names, sorted(COMMANDS))

    def test_rules_name_all_operands(self):
        """Операнды формы записи совпадают с полями команды (кроме A)."""
        for rule in RULES:
            with self.subTest(command=rule.command):
                spec = COMMANDS[rule.command]
                fields = sorted(field.name for field in spec.operands)
                self.assertEqual(sorted(rule.operands), fields)

    def test_only_load_has_signed_operand(self):
        """Знаковый операнд есть только у команды LOAD (поле C)."""
        signed = {rule.command: rule.signed for rule in RULES}
        self.assertEqual(signed["LOAD"], ("C",))
        for command in ("READ", "WRITE", "ABS"):
            self.assertEqual(signed[command], ())


if __name__ == "__main__":
    unittest.main()
