"""Shared setup of the live dev tests: where the dev credentials are, whether the live tests run, and the
name prefix of every object a live test creates.

The `dev_api` fixture (`tests/conftest.py`) builds one client from `DEV_CREDENTIALS_DIRECTORY` for the
whole session, so a pytest run fetches at most one OAuth token for the dev tests: the token endpoint
allows 10 fetches per client per 15 minutes. `test_type_curves_v2_live.py` does not use it: it needs the
production credentials (the dev tenant is not enrolled in Type Curve 2.0).

Each live module keeps its own `pytestmark` skip condition, built from `live_tests_enabled()` plus the
environment variables it needs. Nothing here touches the network, so every live module collects offline.
"""

import os
from pathlib import Path

from combocurve_api_helper.config import find_native_credentials_directory

# An unzipped ComboCurve credential download for the dev tenant. Never `~/.combocurve` itself: that is
# production.
DEV_CREDENTIALS_DIRECTORY = Path.home() / '.combocurve' / 'dev'

# Every object a live test writes carries this prefix, so a leaked one is recognisable and safe to delete.
FIXTURE_PREFIX = 'API Helper Fixture'

LIVE_TEST_SKIP_REASON = 'requires CC_LIVE_TEST=1 and ~/.combocurve/dev credentials'


def live_tests_enabled() -> bool:
    """True when `CC_LIVE_TEST` is set to a non-empty value and the dev credential download is in place.
    The credential check uses the loader's own lookup, so the skip cannot disagree with the loader."""
    return (
        bool(os.environ.get('CC_LIVE_TEST'))
        and find_native_credentials_directory(DEV_CREDENTIALS_DIRECTORY) is not None
    )
