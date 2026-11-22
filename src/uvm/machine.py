"""Модель УВМ: память команд, память данных, регистры и цикл исполнения.

Память команд (code) и память данных (data) разделены: программа не может
ни прочитать, ни изменить собственный код. Регистры и ячейки данных хранят
целые числа; разрядность в спецификации не задана.
"""

from typing import Callable, Dict, List

from .decoder import DecodeError, decode_instruction
from .translator import Instruction

REGISTER_COUNT = 64
DATA_MEMORY_SIZE = 1 << 16


class VmError(Exception):
    """Ошибка выполнения программы на УВМ."""


class Machine:
    """Виртуальная машина: исполняет программу из памяти команд."""

    def __init__(self, program: bytes, data_size: int = DATA_MEMORY_SIZE):
        self.code = bytes(program)
        self.data: List[int] = [0] * data_size
        self.registers: List[int] = [0] * REGISTER_COUNT
        self.pc = 0
        self.executed = 0
        self.handlers: Dict[str, Callable[[Instruction], None]] = {
            "LOAD": self.execute_load,
            "READ": self.execute_read,
            "WRITE": self.execute_write,
        }

    def check_address(self, address: int) -> None:
        """Убедиться, что адрес лежит в памяти данных."""
        if address >= len(self.data):
            raise VmError(
                f"адрес {address} вне памяти данных "
                f"(размер {len(self.data)})"
            )

    def execute_load(self, instruction: Instruction) -> None:
        """LOAD: записать константу C в регистр B."""
        fields = instruction.fields
        self.registers[fields["B"]] = fields["C"]

    def execute_read(self, instruction: Instruction) -> None:
        """READ: записать в регистр B значение из памяти по адресу C."""
        fields = instruction.fields
        self.check_address(fields["C"])
        self.registers[fields["B"]] = self.data[fields["C"]]

    def execute_write(self, instruction: Instruction) -> None:
        """WRITE: записать значение регистра B в память по адресу C."""
        fields = instruction.fields
        self.check_address(fields["C"])
        self.data[fields["C"]] = self.registers[fields["B"]]

    def fetch(self) -> Instruction:
        """Прочитать команду по счётчику команд и сдвинуть его."""
        try:
            instruction, size = decode_instruction(self.code, self.pc)
        except DecodeError as error:
            raise VmError(str(error)) from error
        self.pc += size
        return instruction

    def execute(self, instruction: Instruction) -> None:
        """Выполнить команду во внутреннем представлении."""
        handler = self.handlers.get(instruction.command)
        if handler is None:
            raise VmError(f"команда {instruction.command} не поддерживается")
        handler(instruction)
        self.executed += 1

    def step(self) -> None:
        """Выполнить одну команду; ошибки дополняются смещением команды."""
        offset = self.pc
        try:
            self.execute(self.fetch())
        except VmError as error:
            raise VmError(f"смещение {offset}: {error}") from error

    def run(self) -> None:
        """Выполнять команды, пока не закончится память команд."""
        while self.pc < len(self.code):
            self.step()
