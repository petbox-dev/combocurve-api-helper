from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS


class ReservesCategoryData(BaseModel):
    """The `reservesCategory` object on a real ReservesCategory econ model (verified live,
    project Sample Project A): `{"prmsClass": "reserves", "prmsCategory": "proved",
    "prmsSubCategory": "producing"}`.

    CC's CSV export renders these three values PASSED THROUGH UNCHANGED -- lowercase,
    including underscores (e.g. `non_producing`) -- with NO underscore-to-space transform,
    unlike the enum columns elsewhere in this package (`formats.enum_to_csv`/
    `enum_from_csv`, used by ProductionTaxes' `Rate Type`/`Rate Rows Calculation Method`).
    """

    model_config = ConfigDict(populate_by_name=True)

    prms_class: Annotated[str, Field(alias='prmsClass')]
    prms_category: Annotated[str, Field(alias='prmsCategory')]
    prms_sub_category: Annotated[str, Field(alias='prmsSubCategory')]


class ReservesCategoryMapper:
    """The v3 pilot for the 'settings' (one-row-per-model) econ-model pattern.

    Unlike the row-based mappers (ProductionTaxes, Expenses, StreamProperties, ...) that
    explode one API model into many `rows[]`-driven CSV rows, ReservesCategory has no
    `rows[]`/criteria at all -- the entire model is a single flat settings object, so
    `to_csv_rows` always emits exactly ONE row and `from_csv_rows` always consumes exactly
    ONE row.
    """

    econ_model_type = 'ReservesCategory'
    columns = COLUMNS['ReservesCategory']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        data = ReservesCategoryData.model_validate(model.get('reservesCategory') or {})

        row = dict(common)
        row.update(
            {
                'PRMS Class': data.prms_class,
                'PRMS Category': data.prms_category,
                'PRMS Sub Category': data.prms_sub_category,
            }
        )
        return [{c: row.get(c, '') for c in self.columns}]

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        if len(rows) != 1:
            raise NotImplementedError(
                f'ReservesCategory is one-row-per-model; expected exactly 1 CSV row, got {len(rows)}'
            )
        row = rows[0]

        data = ReservesCategoryData(
            prms_class=row['PRMS Class'],
            prms_category=row['PRMS Category'],
            prms_sub_category=row['PRMS Sub Category'],
        )

        name, unique = model_identity(rows)
        return {
            'name': name,
            'unique': unique,
            'reservesCategory': data.model_dump(by_alias=True),
        }
