"""Запуск ассемблера: python -m uvm <source> <output> [--test]."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
