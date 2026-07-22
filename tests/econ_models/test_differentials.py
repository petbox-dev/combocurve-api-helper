from combocurve_api_helper.econ_models.differentials import DifferentialsMapper

API = {
    'id': 'd1',
    'name': 'Sample Differentials',
    'unique': False,
    'createdAt': '2026-05-10T03:11:41.000Z',
    'updatedAt': '2026-05-10T03:11:41.000Z',
    'econModelType': 'Differentials',
    'differentials': {
        'firstDifferential': {
            'oil': {'escalationModel': 'none', 'rows': [{'dates': '2027-01-01', 'dollarPerBbl': -2.54}]},
            'gas': {'escalationModel': 'none', 'rows': [{'dates': '2027-01-01', 'dollarPerMmbtu': -0.17}]},
            'ngl': {'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'pctOfBasePrice': 32}]},
            'dripCondensate': {'escalationModel': 'none', 'rows': [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}]},
        },
        'secondDifferential': {},
        'thirdDifferential': {},
    },
}


def test_to_row_dicts_values() -> None:
    rows = DifferentialsMapper().to_row_dicts(API)
    assert len(rows) == 4
    oil = next(r for r in rows if r['Phase'] == 'oil')
    assert oil['Key'] == 'differentials_1'
    assert (oil['Criteria'], oil['Period'], oil['Value'], oil['Unit']) == ('dates', '01/01/2027', '-2.54', '$/bbl')
    gas = next(r for r in rows if r['Phase'] == 'gas')
    assert gas['Unit'] == '$/mmbtu'
    ngl = next(r for r in rows if r['Phase'] == 'ngl')
    assert (ngl['Criteria'], ngl['Period'], ngl['Unit']) == ('flat', '', '% base price rem')


def test_roundtrip() -> None:
    m = DifferentialsMapper()
    rebuilt = m.from_row_dicts(m.to_row_dicts(API))
    assert rebuilt['differentials'] == API['differentials']
    assert rebuilt['name'] == 'Sample Differentials' and rebuilt['unique'] is False


def test_escalation_none_roundtrip() -> None:
    """Test that escalationModel=None round-trips to None, not the string 'none'."""
    m = DifferentialsMapper()
    api_model = {
        'id': 'd2',
        'name': 'NoneEscalation',
        'unique': False,
        'createdAt': '2026-05-10T03:11:41.000Z',
        'updatedAt': '2026-05-10T03:11:41.000Z',
        'econModelType': 'Differentials',
        'differentials': {
            'firstDifferential': {
                'oil': {
                    'escalationModel': None,
                    'rows': [{'entireWellLife': 'Flat', 'dollarPerBbl': 0}],
                },
            },
            'secondDifferential': {},
            'thirdDifferential': {},
        },
    }
    rebuilt = m.from_row_dicts(m.to_row_dicts(api_model))
    assert rebuilt['differentials']['firstDifferential']['oil']['escalationModel'] is None, (
        "escalationModel=None should roundtrip to None, not 'none'"
    )


def test_escalation_string_roundtrip() -> None:
    """Test that escalationModel='none' (string) round-trips to 'none'."""
    m = DifferentialsMapper()
    api_model = {
        'id': 'd3',
        'name': 'StringEscalation',
        'unique': False,
        'createdAt': '2026-05-10T03:11:41.000Z',
        'updatedAt': '2026-05-10T03:11:41.000Z',
        'econModelType': 'Differentials',
        'differentials': {
            'firstDifferential': {
                'gas': {
                    'escalationModel': 'none',
                    'rows': [{'entireWellLife': 'Flat', 'dollarPerMmbtu': 0}],
                },
            },
            'secondDifferential': {},
            'thirdDifferential': {},
        },
    }
    rebuilt = m.from_row_dicts(m.to_row_dicts(api_model))
    assert rebuilt['differentials']['firstDifferential']['gas']['escalationModel'] == 'none', (
        "escalationModel='none' (string) should roundtrip to 'none'"
    )
