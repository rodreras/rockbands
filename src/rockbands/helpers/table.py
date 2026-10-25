"""A small table type so helpers need no pandas but still render nicely in Jupyter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List


@dataclass
class Table:
    title: str
    columns: List[str]
    rows: List[List[str]]

    def to_dicts(self) -> List[Dict[str, str]]:
        return [dict(zip(self.columns, row)) for row in self.rows]

    def to_pandas(self):
        import pandas as pd  # optional dependency

        return pd.DataFrame(self.rows, columns=self.columns)

    def to_markdown(self) -> str:
        def cell(text: str) -> str:
            return str(text).replace("|", "\\|")

        lines = ["| " + " | ".join(cell(c) for c in self.columns) + " |",
                 "| " + " | ".join("---" for _ in self.columns) + " |"]
        lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in self.rows]
        return "\n".join(lines)

    def __str__(self) -> str:
        widths = [max(len(str(x)) for x in (col, *(row[i] for row in self.rows))) for i, col in enumerate(self.columns)]
        def fmt(row):
            return "  ".join(str(x).ljust(w) for x, w in zip(row, widths)).rstrip()
        out = [self.title, fmt(self.columns), fmt(["-" * w for w in widths])] if self.title else [fmt(self.columns), fmt(["-" * w for w in widths])]
        out += [fmt(row) for row in self.rows]
        return "\n".join(out)

    def _repr_markdown_(self) -> str:  # rendered by Jupyter/IPython
        return (f"**{self.title}**\n\n" if self.title else "") + self.to_markdown()

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[Dict[str, str]]:
        return iter(self.to_dicts())
