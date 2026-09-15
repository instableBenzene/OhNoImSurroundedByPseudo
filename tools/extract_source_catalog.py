"""Extract the supplied DOCX design source into searchable UTF-8 text/JSON.

Development utility only.  The document is read-only; no content is interpreted
as instructions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def clean(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    document = Document(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    text_lines: list[str] = []
    tables: list[list[list[str]]] = []
    paragraph_index = 0
    table_index = 0

    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            value = clean(block.text)
            if value:
                text_lines.append(
                    f"P{paragraph_index:04d} [{block.style.name}] {value}"
                )
            paragraph_index += 1
        elif isinstance(block, Table):
            rows = [[clean(cell.text) for cell in row.cells] for row in block.rows]
            tables.append(rows)
            text_lines.append(f"\n[TABLE {table_index:03d}]")
            text_lines.extend(
                f"R{row_index:03d} | " + " | ".join(row)
                for row_index, row in enumerate(rows)
            )
            text_lines.append(f"[/TABLE {table_index:03d}]\n")
            table_index += 1

    (args.output_dir / "source.txt").write_text(
        "\n".join(text_lines), encoding="utf-8"
    )
    (args.output_dir / "tables.json").write_text(
        json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "paragraphs": paragraph_index,
                "tables": table_index,
                "source": str(args.source),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
