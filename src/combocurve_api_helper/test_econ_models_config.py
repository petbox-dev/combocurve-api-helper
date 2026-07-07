from combocurve_api_helper import config


def test_every_entry_has_capability_fields() -> None:
    for m in config.ECON_MODELS:
        assert set(m) >= {"qualifier", "econModelType", "route", "methodBase", "hasCrud", "assignable"}
        assert m["hasCrud"] == (m["route"] is not None)
        if m["route"] is None:
            assert m["methodBase"] is None
            assert m["assignable"] is False
        else:
            assert isinstance(m["methodBase"], str) and m["methodBase"]


def test_fluid_model_base_is_fluid() -> None:
    fluid = next(m for m in config.ECON_MODELS if m["econModelType"] == "FluidModel")
    assert fluid["methodBase"] == "fluid"


def test_assignable_set() -> None:
    assignable = {m["econModelType"] for m in config.ECON_MODELS if m["assignable"]}
    assert assignable == {
        "ActualOrForecast", "Capex", "Dates", "Depreciation", "Differentials",
        "Emission", "Escalation", "Expenses", "FluidModel", "Operations",
        "OwnershipReversion", "Pricing", "ProductionTaxes", "ReservesCategory",
        "Risking", "StreamProperties",
    }
    assert "GeneralOptions" not in assignable
