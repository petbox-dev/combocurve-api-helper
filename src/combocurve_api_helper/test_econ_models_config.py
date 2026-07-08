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


def test_method_base_matches_route_derivation() -> None:
    """methodBase must equal route.replace('-','_') (except FluidModel='fluid').

    Independent cross-check against the REST route: the generator names public
    methods from methodBase, and every other test derives its expectations from
    the same econModels.json -- so a typo'd methodBase would silently rename a
    public method with all other tests still green. This pins methodBase to the
    route, which nothing else does.
    """
    for m in config.ECON_MODELS:
        route = m["route"]
        base = m["methodBase"]
        if route is None:
            assert base is None
        elif m["econModelType"] == "FluidModel":
            assert base == "fluid"
        else:
            assert base == route.replace("-", "_")
