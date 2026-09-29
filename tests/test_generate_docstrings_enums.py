"""Offline unit tests for the enum handling in `scripts/generate_docstrings.py`.

The Postman collection picks a random member of each enum on every publish. These
tests pin that a change of pick alone neither makes a block stale nor defeats the
collapse of duplicated array elements, and that a real change still does.
"""

import importlib.util
import pathlib
from types import ModuleType

GEN = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'generate_docstrings.py'


def _load_generator() -> ModuleType:
    specification = importlib.util.spec_from_file_location('generate_docstrings', GEN)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


generator = _load_generator()

SOURCE_TEMPLATE = '''class Sample:
    def post_sample(self) -> None:
        """Post a sample.

        https://docs.api.combocurve.com/api/post-sample

        Example data:
{block}
        """
'''


def _source_with_block(body: object) -> str:
    return SOURCE_TEMPLATE.format(block='\n'.join(generator.render_block(body, '        ')))


def _examples(request: object) -> dict[str, object]:
    return {'post-sample': generator.CollectionExample(response=None, request=request)}


def test_literal_strings_are_marked_and_placeholders_spoofed() -> None:
    filled = generator.fill({'exportType': 'econMonthlyExport', 'expirationHours': '<integer>'})
    assert isinstance(filled['exportType'], generator.EnumLiteral)
    assert filled == {'exportType': 'econMonthlyExport', 'expirationHours': 123}


def test_array_elements_differing_only_in_enum_picks_collapse() -> None:
    filled = generator.fill(
        [{'series': 'P50', 'eur': '<number>'}, {'series': 'P90', 'eur': '<number>'}],
    )
    assert filled == [{'series': 'P50', 'eur': 123.45}]


def test_array_elements_differing_in_placeholders_do_not_collapse() -> None:
    filled = generator.fill([{'value': '<number>'}, {'value': '<string>'}])
    assert filled == [{'value': 123.45}, {'value': 'string'}]


def test_changed_enum_pick_keeps_the_committed_block() -> None:
    source = _source_with_block({'exportType': 'monthlyProductionVolumeExport', 'expirationHours': 24})
    request = generator.fill({'exportType': 'monthlyCombinedVolumeExport', 'expirationHours': '<integer>'})
    request['expirationHours'] = 24
    lines = source.split('\n')
    replacements, unsourced = generator.plan_replacements(source, _examples(request))
    assert unsourced == []
    assert len(replacements) == 1
    replacement = replacements[0]
    assert replacement.lines == lines[replacement.start : replacement.end + 1]


def test_changed_placeholder_value_rewrites_the_block() -> None:
    source = _source_with_block({'exportType': 'econMonthlyExport', 'expirationHours': 24})
    request = generator.fill({'exportType': 'econMonthlyExport', 'expirationHours': '<integer>'})
    lines = source.split('\n')
    replacements, _ = generator.plan_replacements(source, _examples(request))
    replacement = replacements[0]
    assert replacement.lines != lines[replacement.start : replacement.end + 1]
    assert '"expirationHours": 123' in '\n'.join(replacement.lines)


def test_added_key_rewrites_the_block() -> None:
    source = _source_with_block({'exportType': 'econMonthlyExport'})
    request = generator.fill({'exportType': 'econMonthlyExport', 'expirationHours': '<integer>'})
    lines = source.split('\n')
    replacements, _ = generator.plan_replacements(source, _examples(request))
    replacement = replacements[0]
    assert replacement.lines != lines[replacement.start : replacement.end + 1]


def test_enum_position_holding_a_non_string_rewrites_the_block() -> None:
    assert not generator.matches_ignoring_enums({'kind': 1}, generator.fill({'kind': 'rate'}))
    assert not generator.matches_ignoring_enums({'flag': 1}, generator.fill({'flag': '<boolean>'}))
