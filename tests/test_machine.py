"""Тесты модели УВМ: память, регистры, цикл исполнения."""

import unittest

from uvm.encoder import encode
from uvm.machine import REGISTER_COUNT, Machine, VmError
from uvm.translator import translate

DATA_SIZE = 64


def make_machine(source, data_size=DATA_SIZE):
    """Ассемблировать программу и создать машину."""
    return Machine(encode(translate(source)), data_size)


def run_source(source, data_size=DATA_SIZE):
    """Ассемблировать и выполнить программу, вернуть машину."""
    machine = make_machine(source, data_size)
    machine.run()
    return machine


class CommandsTest(unittest.TestCase):
    """Выполнение команд LOAD, READ и WRITE."""

    def test_load(self):
        """LOAD записывает константу в регистр."""
        machine = run_source("r5 = 123")
        self.assertEqual(machine.registers[5], 123)
        self.assertEqual(machine.executed, 1)

    def test_write_and_read(self):
        """WRITE кладёт регистр в память, READ возвращает значение."""
        machine = run_source("r1 = 7\nmem[3] = r1\nr2 = mem[3]")
        self.assertEqual(machine.data[3], 7)
        self.assertEqual(machine.registers[2], 7)
        self.assertEqual(machine.executed, 3)

    def test_initial_state(self):
        """Память данных и регистры изначально нулевые."""
        machine = make_machine("")
        self.assertEqual(machine.data, [0] * DATA_SIZE)
        self.assertEqual(machine.registers, [0] * REGISTER_COUNT)

    def test_empty_program(self):
        """Пустая программа ничего не выполняет."""
        machine = run_source("")
        self.assertEqual(machine.executed, 0)
        self.assertEqual(machine.pc, 0)

    def test_last_address(self):
        """Последний адрес памяти данных доступен."""
        machine = run_source(f"r1 = 9\nmem[{DATA_SIZE - 1}] = r1")
        self.assertEqual(machine.data[DATA_SIZE - 1], 9)


class MemoryModelTest(unittest.TestCase):
    """Память команд и память данных разделены."""

    def test_code_is_not_changed(self):
        """Запись в память данных не меняет память команд."""
        program = encode(translate("r1 = 5\nmem[0] = r1"))
        machine = Machine(program, DATA_SIZE)
        machine.run()
        self.assertEqual(machine.code, program)

    def test_data_size_is_independent(self):
        """Размер памяти данных не зависит от длины программы."""
        machine = make_machine("r1 = 1", data_size=8)
        self.assertEqual(len(machine.data), 8)
        self.assertEqual(len(machine.code), 6)

    def test_pc_advances_by_command_size(self):
        """Счётчик команд сдвигается на размер выполненной команды."""
        machine = make_machine("r1 = 1\nr2 = 2")
        machine.step()
        self.assertEqual(machine.pc, 6)
        machine.step()
        self.assertEqual(machine.pc, 12)


class ErrorsTest(unittest.TestCase):
    """Диагностика ошибок выполнения."""

    def test_write_out_of_memory(self):
        """Запись за пределы памяти данных."""
        with self.assertRaises(VmError) as context:
            run_source(f"mem[{DATA_SIZE}] = r0")
        self.assertIn("смещение 0", str(context.exception))

    def test_read_out_of_memory(self):
        """Чтение за пределами памяти данных."""
        with self.assertRaises(VmError):
            run_source(f"r1 = mem[{DATA_SIZE}]")

    def test_error_reports_offset(self):
        """Сообщение содержит смещение команды, вызвавшей ошибку."""
        with self.assertRaises(VmError) as context:
            run_source(f"r1 = 1\nmem[{DATA_SIZE}] = r1")
        self.assertIn("смещение 6", str(context.exception))

    def test_unknown_opcode(self):
        """Неизвестный код операции в памяти команд."""
        with self.assertRaises(VmError) as context:
            Machine(bytes([0xFF])).run()
        self.assertIn("смещение 0", str(context.exception))

    def test_truncated_command(self):
        """Обрезанная команда в конце программы."""
        with self.assertRaises(VmError):
            Machine(bytes([0x8C, 0xB6])).run()

    def test_abs_is_not_supported_yet(self):
        """Команда abs() будет реализована на этапе 4."""
        with self.assertRaises(VmError) as context:
            run_source("mem[r1] = abs(r2)")
        self.assertIn("ABS", str(context.exception))


if __name__ == "__main__":
    unittest.main()
