"""Tests for the file-level econ-model CSV layer (EconModelMapper.to_csv/from_csv/
read_csv/write_csv) against the real trimmed CC-export fixtures."""

import csv
import io
import os
import pathlib

import pytest

from combocurve_api_helper.econ_models import get_mapper
from combocurve_api_helper.econ_models.base import group_rows_by_model_name
from tests.econ_models.csv_fixture_io import (
    FIXTURE_FILES,
    FIXTURES_DIR,
    group_by_model_name,
    project_columns,
    read_csv_rows,
)


@pytest.mark.parametrize('econ_model_type', sorted(FIXTURE_FILES))
def test_from_csv_equals_per_model_from_csv_rows(econ_model_type: str) -> None:
    mapper = get_mapper(econ_model_type)
    for filename in FIXTURE_FILES[econ_model_type]:
        path = os.path.join(FIXTURES_DIR, filename)
        text = pathlib.Path(path).read_text(encoding='utf-8')
        rows = read_csv_rows(path)
        expected = [mapper.from_csv_rows(g) for g in group_by_model_name(rows).values()]
        assert mapper.from_csv(text) == expected, f'{econ_model_type} / {filename}'


@pytest.mark.parametrize('econ_model_type', sorted(FIXTURE_FILES))
def test_to_csv_reemits_model_parameter_columns(econ_model_type: str) -> None:
    mapper = get_mapper(econ_model_type)
    compare_columns = mapper.columns[3:-1]  # exclude Model Id/Created At/Project Name + Last Update
    for filename in FIXTURE_FILES[econ_model_type]:
        path = os.path.join(FIXTURES_DIR, filename)
        rows = read_csv_rows(path)
        models = [mapper.from_csv_rows(g) for g in group_by_model_name(rows).values()]
        reparsed = list(csv.DictReader(io.StringIO(mapper.to_csv(models))))
        expected = [project_columns(r, compare_columns) for r in rows]
        actual = [project_columns(r, compare_columns) for r in reparsed]
        assert actual == expected, f'{econ_model_type} / {filename}'


def test_to_csv_empty_is_header_only() -> None:
    mapper = get_mapper('Expenses')
    text = mapper.to_csv([])
    lines = text.splitlines()
    assert len(lines) == 1
    assert list(csv.reader([lines[0]]))[0] == mapper.columns
    assert mapper.from_csv(text) == []


def test_from_csv_accepts_string_and_file_like() -> None:
    mapper = get_mapper('Expenses')
    path = os.path.join(FIXTURES_DIR, FIXTURE_FILES['Expenses'][0])
    text = pathlib.Path(path).read_text(encoding='utf-8')
    from_string = mapper.from_csv(text)
    from_buffer = mapper.from_csv(io.StringIO(text))
    assert from_string == from_buffer


def test_from_csv_without_model_name_column_raises() -> None:
    mapper = get_mapper('Expenses')
    with pytest.raises(ValueError, match='Model Name'):
        mapper.from_csv('Key,Category\nfoo,bar\n')


def test_read_write_round_trip(tmp_path: pathlib.Path) -> None:
    mapper = get_mapper('Expenses')
    src = os.path.join(FIXTURES_DIR, FIXTURE_FILES['Expenses'][0])
    models = mapper.read_csv(src)
    out = tmp_path / 'out.csv'
    mapper.write_csv(out, models)
    assert mapper.read_csv(out) == models


def test_group_rows_by_model_name_preserves_first_seen_order() -> None:
    rows = [
        {'Model Name': 'b', 'x': '1'},
        {'Model Name': 'a', 'x': '2'},
        {'Model Name': 'b', 'x': '3'},
    ]
    groups = group_rows_by_model_name(rows)
    assert [g[0]['Model Name'] for g in groups] == ['b', 'a']
    assert [len(g) for g in groups] == [2, 1]
