import pytest

from combocurve_api_helper.econ_models import formats as F
from combocurve_api_helper.econ_models.enums import Criteria, CRITERIA_TO_CSV, CRITERIA_FROM_CSV


def test_criteria_csv_roundtrip() -> None:
    assert CRITERIA_TO_CSV[Criteria.FPD.value] == 'fpd'
    assert CRITERIA_TO_CSV[Criteria.EconLimit.value] == 'econ limit'
    assert CRITERIA_TO_CSV[Criteria.FromHeaders.value] == 'from headers'
    assert CRITERIA_TO_CSV[Criteria.MajorSegment.value] == 'maj seg'
    assert CRITERIA_TO_CSV[Criteria.TotalFluidRate.value] == 'total fluid rate'
    for api, csv in CRITERIA_TO_CSV.items():
        assert CRITERIA_FROM_CSV[csv] == api  # invertible


def test_model_type() -> None:
    assert F.model_type(True) == 'unique'
    assert F.model_type(False) == 'project'


def test_dates() -> None:
    assert F.to_csv_date('2026-07-08') == '07/08/2026'
    assert F.to_csv_datetime('2026-05-08T14:18:05.000Z') == '05/08/2026 14:18:05'
    assert F.from_csv_date('07/08/2026') == '2026-07-08'
    assert F.to_csv_date(None) == ''


def test_bools() -> None:
    assert (F.yes_blank(True), F.yes_blank(False), F.yes_blank(None)) == ('yes', '', '')
    assert (F.yes_no(True), F.yes_no(False)) == ('yes', 'no')
    assert (F.parse_yes_blank('yes'), F.parse_yes_blank('')) == (True, False)
    assert (F.parse_yes_no('yes'), F.parse_yes_no('no')) == (True, False)


def test_escalation_title_true_none_roundtrip() -> None:
    """title=True (Capex/ProductionTaxes convention): API 'none' <-> CSV 'None'."""
    assert F.escalation_to_csv('none', title=True) == 'None'
    assert F.escalation_from_csv('None', title=True) == 'none'


def test_escalation_title_false_none_roundtrip() -> None:
    """title=False (Differentials/Expenses convention): API 'none' <-> CSV 'none'
    unchanged (lowercase, no title-casing)."""
    assert F.escalation_to_csv('none', title=False) == 'none'
    assert F.escalation_from_csv('none', title=False) == 'none'


def test_escalation_none_python_roundtrip_both_title_modes() -> None:
    """Python None (field absent/unset) always inverts with '', regardless of title."""
    assert F.escalation_to_csv(None, title=True) == ''
    assert F.escalation_to_csv(None, title=False) == ''
    assert F.escalation_from_csv('', title=True) is None
    assert F.escalation_from_csv('', title=False) is None


def test_escalation_other_model_name_passthrough_both_title_modes() -> None:
    """A non-'none' model name passes through unchanged in both title modes."""
    assert F.escalation_to_csv('flat_escalation', title=True) == 'flat_escalation'
    assert F.escalation_to_csv('flat_escalation', title=False) == 'flat_escalation'
    assert F.escalation_from_csv('flat_escalation', title=True) == 'flat_escalation'
    assert F.escalation_from_csv('flat_escalation', title=False) == 'flat_escalation'


def test_enum_to_csv_from_csv_roundtrip() -> None:
    """Underscore/space token conversion (e.g. Capex 'Category', ProductionTaxes
    'Rate Type') round-trips, and None/'' inverts like every other Optional column."""
    assert F.enum_to_csv('gross_well_head') == 'gross well head'
    assert F.enum_from_csv('gross well head') == 'gross_well_head'
    assert F.enum_to_csv(None) == ''
    assert F.enum_from_csv('') is None


def test_num_to_csv_basic() -> None:
    assert F.num_to_csv(97) == '97'
    assert F.num_to_csv(100) == '100'
    assert F.num_to_csv(100.0) == '100'
    assert F.num_to_csv(120.49) == '120.49'
    assert F.num_to_csv(0.0001167) == '0.0001167'


def test_num_to_csv_no_scientific_notation() -> None:
    """Regression: values below 1e-4 must render as decimals, not exponent form
    (str(5e-05) == '5e-05'), else the exact-forward + CSV round-trip breaks."""
    assert F.num_to_csv(5e-05) == '0.00005'
    assert F.num_to_csv(1.23e-07) == '0.000000123'
    assert F.num_to_csv_float(5e-05) == '0.00005'
    # value survives a full CSV -> API -> CSV round-trip
    assert F.num_to_csv(F.csv_to_num('0.00005')) == '0.00005'
    assert F.num_to_csv(F.csv_to_num('0.0001167')) == '0.0001167'


def test_num_to_csv_float_always_has_point() -> None:
    assert F.num_to_csv_float(100.0) == '100.0'
    assert F.num_to_csv_float(120.49) == '120.49'


def test_check_entire_well_life() -> None:
    """Both known CC flat-criteria markers pass ('Flat', 'Entire Well Life'); any other
    value fails loud rather than being silently mapped to 'flat'."""
    F.check_entire_well_life('Flat')
    F.check_entire_well_life('Entire Well Life')
    with pytest.raises(NotImplementedError):
        F.check_entire_well_life('Monthly')
    with pytest.raises(NotImplementedError):
        F.check_entire_well_life('')
