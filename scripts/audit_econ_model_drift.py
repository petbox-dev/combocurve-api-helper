"""Live-API drift audit for the econ-model CSV mappers.

CC owns the API payload shape. This tool fetches real econ models from one or more
projects and reports anything the mappers cannot account for -- payload keys outside the
committed baseline (``combocurve_api_helper.econ_models.drift._BASELINE_KEYS``), or models
the forward mapper cannot render. Run it periodically; it needs live API credentials, so
it is deliberately NOT a CI gate (the detection logic itself is unit-tested in
``test_drift.py``).

Usage:
    python scripts/audit_econ_model_drift.py --project "Sample Project A"
    python scripts/audit_econ_model_drift.py --project A --project B --cap 200
    python scripts/audit_econ_model_drift.py --project A --emit-baseline  # refreshed literal

Exit code is non-zero when any drift is found, so it can gate a scheduled job.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Sequence, Set

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.econ_models import MAPPERS, drift

# econModelType -> ComboCurveAPI getter method name.
GETTERS: Dict[str, str] = {
    'StreamProperties': 'get_stream_properties_models',
    'Differentials': 'get_differentials_models',
    'ProductionTaxes': 'get_production_taxes_models',
    'Expenses': 'get_expenses_models',
    'Capex': 'get_capex_models',
    'ReservesCategory': 'get_reserves_categories_models',
    'Pricing': 'get_pricing_models',
    'DateSettings': 'get_date_settings_models',
    'OwnershipReversion': 'get_ownership_reversions_models',
    'ActualOrForecast': 'get_actual_forecast_models',
    'Risking': 'get_riskings_models',
}


def fetch_models(
    api: ComboCurveAPI, econ_model_type: str, project_ids: Sequence[str], cap: int
) -> List[Dict[str, Any]]:
    getter = getattr(api, GETTERS[econ_model_type])
    models: List[Dict[str, Any]] = []
    for pid in project_ids:
        fetched = getter(pid)
        models.extend(fetched[:cap] if cap else fetched)
    return models


def resolve_project_ids(api: ComboCurveAPI, names: Sequence[str]) -> List[str]:
    projects = api.get_projects()
    ids: List[str] = []
    for name in names:
        pid = api.extract_id(projects, name)
        if pid is None:
            print(f'  ! project not found, skipping: {name!r}', file=sys.stderr)
            continue
        ids.append(pid)
    return ids


def run_audit(api: ComboCurveAPI, names: Sequence[str], cap: int) -> int:
    project_ids = resolve_project_ids(api, names)
    total = 0
    for econ_model_type in MAPPERS:
        models = fetch_models(api, econ_model_type, project_ids, cap)
        findings = drift.audit_models(econ_model_type, models)
        status = 'OK' if not findings else f'{len(findings)} DRIFT'
        print(f'{econ_model_type:20} {len(models):6} models  {status}')
        for finding in findings:
            if finding.unknown_keys:
                print(f'    [{finding.model_name}] unknown keys: {finding.unknown_keys}')
            if finding.map_error is not None:
                print(f'    [{finding.model_name}] cannot map: {finding.map_error}')
            if finding.roundtrip_error is not None:
                print(f'    [{finding.model_name}] round-trip: {finding.roundtrip_error}')
        total += len(findings)
    print(f'\nTotal drift findings: {total}')
    return 1 if total else 0


def emit_baseline(api: ComboCurveAPI, names: Sequence[str], cap: int) -> int:
    """Print a refreshed ``_BASELINE_KEYS`` literal from live data (paste into drift.py)."""
    project_ids = resolve_project_ids(api, names)
    print('_BASELINE_KEYS: Dict[str, FrozenSet[str]] = {')
    for econ_model_type in MAPPERS:
        keys: Set[str] = set()
        for model in fetch_models(api, econ_model_type, project_ids, cap):
            payload = {k: v for k, v in model.items() if k not in drift.ENVELOPE_KEYS}
            keys |= drift.collect_keys(payload)
        print(f'    {econ_model_type!r}: frozenset(')
        print('        {')
        for key in sorted(keys):
            print(f'            {key!r},')
        print('        }')
        print('    ),')
    print('}')
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project', action='append', dest='projects', required=True, help='project name (repeatable)')
    parser.add_argument('--cap', type=int, default=0, help='max models per type per project (0 = all)')
    parser.add_argument('--emit-baseline', action='store_true', help='print a refreshed baseline literal instead')
    args = parser.parse_args(argv)

    api = ComboCurveAPI()
    if args.emit_baseline:
        return emit_baseline(api, args.projects, args.cap)
    return run_audit(api, args.projects, args.cap)


if __name__ == '__main__':
    sys.exit(main())
