"""Print selected extracted DOCX tables with duplicate Word cells collapsed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def collapse(row: list[str]) -> list[str]:
    result: list[str] = []
    for cell in row:
        if not result or cell != result[-1]:
            result.append(cell)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("tables", nargs="+", type=int)
    args = parser.parse_args()
    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    for index in args.tables:
        print(f"\n=== TABLE {index:03d} ===")
        for row_index, row in enumerate(data[index]):
            print(f"R{row_index:03d}: " + " || ".join(collapse(row)))


if __name__ == "__main__":
    main()
