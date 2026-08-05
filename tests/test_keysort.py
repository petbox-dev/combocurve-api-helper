"""Tests for `APIBase._keysort`, the comparison-key builder behind every `get_*` list.

The comparison key must depend only on an item's DATA, never on the order the API
happened to serialize its JSON keys in.

`_keysort` used to assemble the key by READING the item's own key sequence
(`values[order[key]]`) instead of WRITING each value to its assigned position.
Those agree only when `order` COMPOSED WITH the item's key sequence is
self-inverse -- a property of the payload, not of `order` alone. ComboCurve does
NOT serialize keys uniformly: projects/scenarios/forecasts arrive
`createdAt, id, name, updatedAt` (self-inverse, unaffected), while econ models,
type curves and wells lead with `id` and econ runs arrive `id, runDate, status`
-- all non-self-inverse, so those really were sorted by `updatedAt` / `status`.

Most cases below are built to break that symmetry deliberately and DO fail against
the old implementation. Six do not, and say so in their own docstrings: two are
characterization tests (`test_reverse_flips_the_order`,
`test_non_string_values_sort_by_their_string_form`), two pin constants rather than
behavior, and two -- the well-comment and representative-well cases -- are regression
tests for the ORDERING CONSTANTS, not for the read-vs-write fix. Their orders have two
keys, and every 2-element permutation is self-inverse, which is exactly the masking
condition described above.
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import pytest

from combocurve_api_helper import company_models
from combocurve_api_helper.base import LIST_SORT_ORDER, WELL_LIST_SORT_ORDER, APIBase
from combocurve_api_helper.econ_runs import _ECON_RUN_SORT_ORDER
from combocurve_api_helper.forecasts import _VOLUME_SORT_ORDER
from combocurve_api_helper.production import _PRODUCTION_SORT_ORDER
from combocurve_api_helper.typecurves import _REP_WELL_SORT_ORDER
from combocurve_api_helper.wells import _WELL_COMMENT_SORT_ORDER

if TYPE_CHECKING:
    from combocurve_api_helper.base import Item, ItemList

# Imported, not re-declared: a local copy would keep passing against a stale
# mapping if the production ordering ever changed.
SORT_ORDER = LIST_SORT_ORDER


def test_sort_is_independent_of_json_key_order() -> None:
    """Two items must order by `name` even when one arrives with shuffled keys.

    `first` is in canonical key order, `second` is not. Reading rather than
    writing positions makes `second`'s key start with its `updatedAt` ('z'),
    which sorts it after `first` ('b') -- the reverse of the correct order,
    since 'a' precedes 'b' by name.
    """
    first: Item = {'name': 'b', 'id': 'X', 'createdAt': 'C', 'updatedAt': 'm'}
    second: Item = {'id': 'Y', 'name': 'a', 'createdAt': 'C', 'updatedAt': 'z'}

    ordered = APIBase._keysort([first, second], SORT_ORDER)

    assert [item['name'] for item in ordered] == ['a', 'b']


def test_identical_data_yields_identical_placement_regardless_of_key_order() -> None:
    """Serializing the same record two ways must not change where it sorts."""
    canonical: Item = {'name': 'beta', 'id': 'ID', 'createdAt': 'C', 'updatedAt': 'U'}
    shuffled: Item = {'id': 'ID', 'updatedAt': 'U', 'name': 'beta', 'createdAt': 'C'}
    neighbour: Item = {'name': 'alpha', 'id': 'ID0', 'createdAt': 'C', 'updatedAt': 'U'}

    with_canonical = [item['name'] for item in APIBase._keysort([canonical, dict(neighbour)], SORT_ORDER)]
    with_shuffled = [item['name'] for item in APIBase._keysort([shuffled, dict(neighbour)], SORT_ORDER)]

    assert with_canonical == with_shuffled == ['alpha', 'beta']


def test_non_self_inverse_order_sorts_by_the_designated_position() -> None:
    """A 3-cycle `order` must sort by the key assigned position 0.

    `{a: 1, b: 2, c: 0}` is a 3-cycle, so it is NOT self-inverse -- unlike the
    2-cycles and identities used elsewhere in the package, which mask the bug.
    Correct keys are [c, a, b]; the read-indexed version produced [b, c, a].
    """
    order = {'a': 1, 'b': 2, 'c': 0}
    first: Item = {'a': 'm', 'b': 'z', 'c': 'b'}
    second: Item = {'a': 'n', 'b': 'a', 'c': 'c'}

    ordered = APIBase._keysort([first, second], order)

    # Sorted by 'c' (position 0): 'b' precedes 'c'.
    assert [item['c'] for item in ordered] == ['b', 'c']


def test_missing_ordering_keys_are_padded_not_fatal() -> None:
    """An item lacking every ordering key sorts as empty strings rather than raising.

    The read-indexed version unpacked an empty `zip`, raising ValueError.
    """
    items: ItemList = [{'unrelated': 'x'}, {'name': 'alpha', 'id': 'ID1', 'createdAt': 'C', 'updatedAt': 'U'}]

    result = APIBase._keysort(items, SORT_ORDER)

    assert [item.get('name') for item in result] == [None, 'alpha']
    # Absent ordering keys are recorded on the item, which callers have always seen.
    assert result[0]['updatedAt'] is None


def test_reverse_flips_the_order() -> None:
    """`reverse=True` returns the same items in descending comparison-key order.

    Characterization test: unchanged by the read-vs-write fix.
    """
    items: ItemList = [{'name': 'alpha'}, {'name': 'bravo'}]

    assert [item['name'] for item in APIBase._keysort(items, SORT_ORDER, reverse=True)] == ['bravo', 'alpha']


def test_mixed_type_values_never_reach_the_comparison_raw() -> None:
    """Every key element must be a `str`, so mixed-type values cannot raise.

    The old implementation appended the RAW value in addition to its stringified
    form, so a None and an int could meet in the same key position and `sorted`
    raised `TypeError: '<' not supported between 'NoneType' and 'int'`. Both items
    share a `name` here, forcing the comparison down to the position that differs.
    """
    items: ItemList = [
        {'name': 'same', 'id': 2, 'createdAt': 'C', 'updatedAt': 'U'},
        {'name': 'same', 'id': None, 'createdAt': 'C', 'updatedAt': 'U'},
    ]

    assert [item['id'] for item in APIBase._keysort(items, SORT_ORDER)] == [None, 2]


def test_non_string_values_sort_by_their_string_form() -> None:
    """Non-str ordering values compare via `str(value)`, not numerically.

    Characterization test: `str(10) < str(2)`, so 10 sorts first.
    """
    items: ItemList = [{'name': 2, 'id': 'ID2'}, {'name': 10, 'id': 'ID1'}]

    assert [item['name'] for item in APIBase._keysort(items, SORT_ORDER)] == [10, 2]


def test_negative_order_position_is_rejected() -> None:
    """A negative position would index from the end and drop another key's value."""
    items: ItemList = [{'a': 'x', 'b': 'y'}]

    with pytest.raises(ValueError, match='non-negative'):
        APIBase._keysort(items, {'a': 0, 'b': -1})


def test_duplicate_order_positions_are_rejected() -> None:
    """Two keys sharing a position would silently discard one of them."""
    items: ItemList = [{'a': 'x', 'b': 'y'}]

    with pytest.raises(ValueError, match='distinct'):
        APIBase._keysort(items, {'a': 0, 'b': 0})


def test_gaps_in_order_positions_are_allowed() -> None:
    """A non-contiguous `order` pads the gap and still sorts by position 0."""
    items: ItemList = [{'name': 'b', 'id': 'X'}, {'name': 'a', 'id': 'Y'}]

    assert [item['name'] for item in APIBase._keysort(items, {'name': 0, 'id': 3})] == ['a', 'b']


def test_shared_order_constants_match_the_documented_positions() -> None:
    """Pin the single-sourced orderings; `sort_by_key`'s argument depends on them."""
    assert dict(LIST_SORT_ORDER) == {'name': 0, 'id': 3, 'createdAt': 2, 'updatedAt': 1}
    assert dict(WELL_LIST_SORT_ORDER) == {'wellName': 0, 'id': 3, 'createdAt': 2, 'updatedAt': 1}
    # company_models re-exports the same object, not a copy.
    assert company_models.SORT_ORDER is LIST_SORT_ORDER


def test_wells_sort_by_well_name_on_the_live_payload_key_order() -> None:
    """Wells must sort by `wellName`, not `updatedAt`, for the real arrival order.

    Live payloads arrive `id, wellName, createdAt, updatedAt`. Composed with
    `WELL_LIST_SORT_ORDER` that is p=(3,0,2,1) -- a 3-cycle plus a fixed point, not
    self-inverse -- so the read-indexed version ordered wells by `updatedAt`. Note the
    `name` ordering yields the SAME permutation under its live arrival order (see the
    next test): the two do not differ, so neither can be reasoned about from the other's
    alphabetical position.
    """
    wells: ItemList = [
        {'id': 'w3', 'wellName': 'Zulu 9H', 'createdAt': 'C', 'updatedAt': '2026-01-01'},
        {'id': 'w1', 'wellName': 'Alpha 1H', 'createdAt': 'C', 'updatedAt': '2026-04-01'},
        {'id': 'w2', 'wellName': 'Mike 5H', 'createdAt': 'C', 'updatedAt': '2026-02-01'},
    ]

    ordered = APIBase._keysort(wells, WELL_LIST_SORT_ORDER)

    assert [item['wellName'] for item in ordered] == ['Alpha 1H', 'Mike 5H', 'Zulu 9H']


def test_econ_models_sort_by_name_on_the_live_payload_key_order() -> None:
    """Econ models and type curves arrive `id, name, createdAt, updatedAt`.

    Same p=(3,0,2,1) as the well ordering above -- a 3-cycle plus a fixed point.
    """
    models: ItemList = [
        {'id': 'm3', 'name': 'Zulu', 'createdAt': 'C', 'updatedAt': '2026-01-01'},
        {'id': 'm1', 'name': 'Alpha', 'createdAt': 'C', 'updatedAt': '2026-04-01'},
        {'id': 'm2', 'name': 'Mike', 'createdAt': 'C', 'updatedAt': '2026-02-01'},
    ]

    ordered = APIBase._keysort(models, LIST_SORT_ORDER)

    assert [item['name'] for item in ordered] == ['Alpha', 'Mike', 'Zulu']


def test_well_comment_ordering_matches_the_well_comment_payload() -> None:
    """The well-comment ordering must use keys the payload actually has.

    Regression test for the CONSTANT, not for the read-vs-write fix: a 2-key order is
    self-inverse, so this passes under either implementation. The well-list ordering has
    none of these keys, which raised ValueError before 2.1.0 and would otherwise have
    no-sorted while injecting four null keys.
    """
    assert set(_WELL_COMMENT_SORT_ORDER) <= {'commentedAt', 'commentedBy', 'forecast', 'project', 'text', 'well'}

    comments: ItemList = [
        {'commentedAt': '2026-01-02', 'commentedBy': 'u1', 'well': 'w2', 'text': 'b'},
        {'commentedAt': '2026-01-01', 'commentedBy': 'u2', 'well': 'w1', 'text': 'a'},
    ]

    ordered = APIBase._keysort(comments, _WELL_COMMENT_SORT_ORDER, reverse=True)

    # Newest first, matching how get_well_comments calls it.
    assert [item['commentedAt'] for item in ordered] == ['2026-01-02', '2026-01-01']
    # No key outside the documented comment shape was padded in.
    assert not set(ordered[0]) - {'commentedAt', 'commentedBy', 'forecast', 'project', 'text', 'well'}


def test_ordering_constants_are_immutable() -> None:
    """They are shared by every list endpoint, so one stray write would corrupt all of them."""
    shared = [
        LIST_SORT_ORDER,
        WELL_LIST_SORT_ORDER,
        company_models.SORT_ORDER,
        _ECON_RUN_SORT_ORDER,
        _PRODUCTION_SORT_ORDER,
        _VOLUME_SORT_ORDER,
        _REP_WELL_SORT_ORDER,
        _WELL_COMMENT_SORT_ORDER,
    ]
    for order in shared:
        with pytest.raises(TypeError):
            order[next(iter(order))] = 99  # type: ignore[index]


def test_bool_order_positions_are_rejected() -> None:
    """`bool` is an `int` subclass, so `True` would tie with position 1 undetected."""
    items: ItemList = [{'a': 'x', 'b': 'y'}]

    with pytest.raises(ValueError, match='non-bool ints'):
        APIBase._keysort(items, {'a': True, 'b': 2})


def test_int_enum_order_positions_are_accepted() -> None:
    """`IntEnum` is a genuine `int` and satisfies `Mapping[str, int]`, so it must work.

    An earlier `type(position) is not int` guard rejected it -- code that passed
    `mypy --strict` then failed at runtime.
    """

    class Position(IntEnum):
        FIRST = 0
        SECOND = 1

    items: ItemList = [{'a': 'y', 'b': '2'}, {'a': 'x', 'b': '1'}]

    ordered = APIBase._keysort(items, {'a': Position.FIRST, 'b': Position.SECOND})

    assert [item['a'] for item in ordered] == ['x', 'y']


def test_representative_well_ordering_matches_its_payload() -> None:
    """Representative wells key their id as `wellId`, not `id`.

    Naming `id` meant the tiebreaker never fired and every returned well was padded
    with a spurious `id: null` -- the same defect class as get_well_comments, but
    silent because `wellName` alone still decided the order. Regression test for the
    CONSTANT: a 2-key order is self-inverse, so it passes under either implementation.
    """
    documented = {'api14', 'wellName', 'wellId', 'chosenID', 'wellNumber', 'water', 'oil', 'gas'}
    assert set(_REP_WELL_SORT_ORDER) <= documented

    # Same name, so the comparison falls through to the id tiebreaker.
    rep_wells: ItemList = [
        {'api14': 'a2', 'wellName': 'Shared', 'wellId': 'w2', 'chosenID': 'c2'},
        {'api14': 'a1', 'wellName': 'Shared', 'wellId': 'w1', 'chosenID': 'c1'},
    ]

    ordered = APIBase._keysort(rep_wells, _REP_WELL_SORT_ORDER)

    assert [item['wellId'] for item in ordered] == ['w1', 'w2']
    assert not set(ordered[0]) - documented
