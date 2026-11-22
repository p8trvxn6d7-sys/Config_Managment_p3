"""Дамп памяти данных в формате XML.

Формат файла:

    <?xml version='1.0' encoding='utf-8'?>
    <memory first="10" last="12">
      <cell address="10" value="7" />
      <cell address="11" value="0" />
      <cell address="12" value="5" />
    </memory>
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

from .machine import VmError

ROOT_TAG = "memory"
CELL_TAG = "cell"
ENCODING = "utf-8"


def check_range(first: int, last: int, size: int) -> None:
    """Убедиться, что диапазон адресов корректен и лежит в памяти."""
    if first > last:
        raise VmError(f"начало диапазона {first} больше конца {last}")
    if last >= size:
        raise VmError(
            f"диапазон до {last} выходит за память данных (размер {size})"
        )


def build_dump(data: Sequence[int], first: int, last: int) -> ET.Element:
    """Построить XML-дерево с ячейками памяти от first до last включительно."""
    root = ET.Element(ROOT_TAG, {"first": str(first), "last": str(last)})
    for address in range(first, last + 1):
        attributes = {"address": str(address), "value": str(data[address])}
        ET.SubElement(root, CELL_TAG, attributes)
    return root


def write_dump(path: str, data: Sequence[int], first: int, last: int) -> None:
    """Записать дамп диапазона адресов в XML-файл."""
    check_range(first, last, len(data))
    root = build_dump(data, first, last)
    ET.indent(root)
    try:
        ET.ElementTree(root).write(
            Path(path), encoding=ENCODING, xml_declaration=True
        )
    except OSError as error:
        raise VmError(f"не удалось записать {path}: {error.strerror}")
