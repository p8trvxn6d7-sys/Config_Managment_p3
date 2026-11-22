"""Тесты дампа памяти в формате XML."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from uvm.dump import build_dump, check_range, write_dump
from uvm.machine import VmError

DATA = [0, 10, 20, 30, 40, 50]


def read_cells(path):
    """Прочитать XML-дамп; вернуть корень и список (адрес, значение)."""
    root = ET.parse(path).getroot()
    cells = [
        (int(cell.get("address")), int(cell.get("value")))
        for cell in root.findall("cell")
    ]
    return root, cells


class BuildDumpTest(unittest.TestCase):
    """Построение XML-дерева."""

    def test_structure(self):
        """Корень memory содержит ячейки cell с адресом и значением."""
        root = build_dump(DATA, 1, 3)
        self.assertEqual(root.tag, "memory")
        self.assertEqual(root.attrib, {"first": "1", "last": "3"})
        cells = [(cell.get("address"), cell.get("value")) for cell in root]
        self.assertEqual(cells, [("1", "10"), ("2", "20"), ("3", "30")])

    def test_single_cell(self):
        """Диапазон из одной ячейки."""
        root = build_dump(DATA, 4, 4)
        self.assertEqual(len(root), 1)


class CheckRangeTest(unittest.TestCase):
    """Проверка диапазона адресов."""

    def test_valid(self):
        """Корректные диапазоны принимаются."""
        check_range(0, 0, len(DATA))
        check_range(0, len(DATA) - 1, len(DATA))

    def test_reversed(self):
        """Начало больше конца."""
        with self.assertRaises(VmError):
            check_range(3, 2, len(DATA))

    def test_out_of_memory(self):
        """Конец диапазона за пределами памяти."""
        with self.assertRaises(VmError):
            check_range(0, len(DATA), len(DATA))


class WriteDumpTest(unittest.TestCase):
    """Запись дампа в файл."""

    def setUp(self):
        """Создать временную папку."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def test_file_content(self):
        """Файл содержит XML с запрошенными ячейками."""
        path = Path(self.folder.name) / "dump.xml"
        write_dump(str(path), DATA, 2, 5)
        root, cells = read_cells(path)
        self.assertEqual(root.attrib, {"first": "2", "last": "5"})
        self.assertEqual(cells, [(2, 20), (3, 30), (4, 40), (5, 50)])

    def test_xml_declaration(self):
        """Файл начинается с XML-декларации."""
        path = Path(self.folder.name) / "dump.xml"
        write_dump(str(path), DATA, 0, 1)
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("<?xml"))

    def test_unwritable_path(self):
        """Недоступный путь даёт VmError."""
        path = Path(self.folder.name) / "no_dir" / "dump.xml"
        with self.assertRaises(VmError):
            write_dump(str(path), DATA, 0, 1)


if __name__ == "__main__":
    unittest.main()
