"""ComboCurve has no company route for the Emission and FluidModel econ models: `GET`/`HEAD`
`/v1/econ-models/emissions` and `/fluid-models` answer 400 (verified live 2026-09-30). The shared company
url builder refuses those types before any request. On 2.x the eight hand-written company methods for them
stay (removing them is a breaking change, done in 3.0.0); each raises `ValueError` through the builder."""

from collections.abc import Callable
from typing import Any

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from tests.http_fakes import make_offline_api

V1 = 'https://api.combocurve.com/v1'

KEPT_COMPANY_METHODS: dict[str, Callable[[ComboCurveAPI], object]] = {
    'get_company_emissions_models_url': lambda api: api.get_company_emissions_models_url(),
    'get_company_emissions_model_by_id_url': lambda api: api.get_company_emissions_model_by_id_url('M'),
    'get_company_fluid_models_url': lambda api: api.get_company_fluid_models_url(),
    'get_company_fluid_models_by_id_url': lambda api: api.get_company_fluid_models_by_id_url('M'),
    'get_company_emission_models': lambda api: api.get_company_emission_models(),
    'get_company_emissions_model_by_id': lambda api: api.get_company_emissions_model_by_id('M'),
    'get_company_fluid_models': lambda api: api.get_company_fluid_models(),
    'get_company_fluid_model_by_id': lambda api: api.get_company_fluid_model_by_id('M'),
}


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


@pytest.mark.parametrize('method_name', sorted(KEPT_COMPANY_METHODS))
def test_each_kept_company_method_raises_before_any_request(monkeypatch: MonkeyPatch, method_name: str) -> None:
    def fail_if_called(*arguments: Any, **keywords: Any) -> None:
        pytest.fail('a request was sent for a type with no company route')

    monkeypatch.setattr(requests, 'request', fail_if_called)
    with pytest.raises(ValueError, match='no company route'):
        KEPT_COMPANY_METHODS[method_name](make_offline_api())


def test_company_list_by_type_raises_before_any_request(monkeypatch: MonkeyPatch) -> None:
    def fail_if_called(*arguments: Any, **keywords: Any) -> None:
        pytest.fail('a request was sent for a type with no company route')

    monkeypatch.setattr(requests, 'request', fail_if_called)
    with pytest.raises(ValueError, match='FluidModel'):
        make_offline_api().get_company_econ_models_by_type('FluidModel')
