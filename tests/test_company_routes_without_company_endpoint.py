"""ComboCurve has no company route for the Emission and FluidModel econ models: `GET`/`HEAD`
`/v1/econ-models/emissions` and `/fluid-models` answer 400 (verified live 2026-09-30). The shared company
url builder refuses those types before any request, and the hand-written methods for them are gone."""

from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from tests.http_fakes import make_offline_api

V1 = 'https://api.combocurve.com/v1'

REMOVED_METHOD_NAMES = [
    'get_company_emissions_models_url',
    'get_company_emissions_model_by_id_url',
    'get_company_fluid_models_url',
    'get_company_fluid_models_by_id_url',
    'get_company_emission_models',
    'get_company_emissions_model_by_id',
    'get_company_fluid_models',
    'get_company_fluid_model_by_id',
]


@pytest.mark.parametrize('econ_model_type', ['Emission', 'emission', 'EMISSION', 'FluidModel', 'fluidmodel'])
def test_url_builder_refuses_a_type_with_no_company_route(econ_model_type: str) -> None:
    with pytest.raises(ValueError, match=econ_model_type):
        make_offline_api().get_company_econ_models_by_type_url(econ_model_type)


@pytest.mark.parametrize('econ_model_type', ['Emission', 'FluidModel'])
def test_by_id_url_builder_refuses_a_type_with_no_company_route(econ_model_type: str) -> None:
    with pytest.raises(ValueError, match=econ_model_type):
        make_offline_api().get_company_econ_model_by_type_by_id_url(econ_model_type, 'M')


def test_url_builder_still_builds_a_type_with_a_company_route() -> None:
    assert make_offline_api().get_company_econ_models_by_type_url('Capex') == f'{V1}/econ-models/capex'


def test_url_builder_keeps_the_assertion_for_an_unknown_type() -> None:
    with pytest.raises(AssertionError, match='Invalid econ model type'):
        make_offline_api().get_company_econ_models_by_type_url('NoSuchType')


@pytest.mark.parametrize('method_name', REMOVED_METHOD_NAMES)
def test_removed_company_methods_are_gone(method_name: str) -> None:
    assert not hasattr(ComboCurveAPI, method_name)


def test_company_list_by_type_raises_before_any_request(monkeypatch: MonkeyPatch) -> None:
    def fail_if_called(*args: Any, **kwargs: Any) -> None:
        pytest.fail('a request was sent for a type with no company route')

    monkeypatch.setattr(requests, 'request', fail_if_called)
    with pytest.raises(ValueError, match='FluidModel'):
        make_offline_api().get_company_econ_models_by_type('FluidModel')
