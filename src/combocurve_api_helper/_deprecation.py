import os
import sys
import warnings
from pathlib import Path

_PACKAGE_DIRECTORY = os.path.normcase(str(Path(__file__).parent.resolve()))


def _is_package_frame(filename: str) -> bool:
    """True when `filename` is a module of this package."""
    return os.path.normcase(os.path.realpath(filename)).startswith(_PACKAGE_DIRECTORY + os.sep)


def warn_deprecated(message: str) -> None:
    """Emit a `DeprecationWarning` attributed to the first caller outside this package.

    The depth from a public entry point to here differs per path (`ComboCurveAPI()`,
    `from_credentials_directory`, `from_alternate_config`), so a fixed `stacklevel` would point at a
    frame inside the package. Python's default filter hides a `DeprecationWarning` unless it is
    attributed to `__main__`, and pytest shows it for the test that triggered it; both need the
    caller's frame.
    """
    frame = sys._getframe(1)
    stacklevel = 2
    while frame.f_back is not None and _is_package_frame(frame.f_code.co_filename):
        frame = frame.f_back
        stacklevel += 1
    warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
