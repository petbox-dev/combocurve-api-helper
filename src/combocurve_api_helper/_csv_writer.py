import csv
import io
import os
from collections.abc import Sequence
from typing import Union


class RowWriter:
    """File-level CSV writing from already-built row dicts, given a `columns` header.

    Split out of `EconModelMapper` (`econ_models/base.py`) so a ONE-WAY exporter -- the
    forecast-parameters converter, and the other async export kinds to come -- can reuse
    the row-list -> CSV plumbing without also declaring the round-trip `from_row_dicts`
    the econ mappers need.

    It constrains only the OUTPUT (`columns` -> CSV text/file); it says nothing about how a
    subclass PRODUCES its rows. That is deliberate: the econ mappers build rows from one
    model dict (`to_row_dicts(model, context)`) while the forecast converter builds them
    from a collection plus a join (`to_row_dicts(export_rows, wells)`), so the two keep
    their own, different, row-building signatures and share only the writer.
    """

    # The exact CSV header, in order. Every subclass sets this (a list on the econ mappers, a
    # tuple on the forecast converter -- `Sequence` accepts both, and an immutable tuple is
    # preferred for a re-exported header). A row carrying a key NOT in `columns` raises
    # (csv.DictWriter's default `extrasaction='raise'`); a column absent from a row is written
    # blank -- so build every row with the full `columns` key set.
    columns: Sequence[str]

    def rows_to_csv(self, rows: list[dict[str, str]]) -> str:
        """Serialize already-built row dicts to a CSV string.

        The header (from `self.columns`) is always written, so `rows_to_csv([])` returns a
        header-only string. Lines use the csv module's default CRLF terminator; write the
        result through `write_rows_csv` (which opens with `newline=''`) to avoid doubled
        newlines on Windows.
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.columns)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()

    def write_rows_csv(self, path: Union[str, os.PathLike[str]], rows: list[dict[str, str]]) -> None:
        """Write already-built row dicts to a CSV file (UTF-8, `newline=''`)."""
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            handle.write(self.rows_to_csv(rows))
