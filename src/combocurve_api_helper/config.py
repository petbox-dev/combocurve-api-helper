import json
from pathlib import Path
from typing import NamedTuple, Optional, TypedDict, Union

from typing_extensions import Self

USER_HOME = Path.home()
PACKAGE_ROOT = Path(__file__).parent.resolve()

COMBOCURVE_DIRECTORY = USER_HOME / '.combocurve'

# The files of an unzipped ComboCurve credential download (the "native" layout). OAuth (v2)
# downloads hold `api-credentials.json`; legacy (v1) downloads hold `api-service-account-key.json`.
# The ZIP puts them in a `combocurve/` folder, so a directory is searched at its top and in that folder.
API_CREDENTIALS_JSON = 'api-credentials.json'
SERVICE_ACCOUNT_KEY_JSON = 'api-service-account-key.json'
API_KEY_TXT = 'api-key.txt'
CREDENTIALS_ZIP_FOLDER = 'combocurve'

# The older layout: the credential JSON renamed to `combocurve.json`, the key wrapped in JSON.
# Deprecated in 2.5.0, removed in 3.0.0.
COMBOCURVE_JSON = COMBOCURVE_DIRECTORY / 'combocurve.json'
CC_API_CONFIG_JSON = COMBOCURVE_DIRECTORY / 'cc-api.config.json'

REFERENCE_WELLHEADER: dict[str, Union[str, int, float, bool]] = json.loads(
    (PACKAGE_ROOT / 'assets' / 'wellHeader.json').read_text()
)


class EconModelEntry(TypedDict):
    """Shape of each entry in `assets/econModels.json`."""

    qualifier: str
    econModelType: str
    route: Optional[str]  # API path segment; None when hasCrud and assignable are both False
    methodBase: Optional[str]  # generated method-name stem; None when hasCrud and assignable are both False
    hasCrud: bool
    assignable: bool


ECON_MODELS: list[EconModelEntry] = json.loads((PACKAGE_ROOT / 'assets' / 'econModels.json').read_text())


class Configuration(NamedTuple):
    apikey: str

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> Self:
        """
        Parse the contents of a `cc-api.config.json` file from a path.
        """
        if isinstance(path, str):
            path = Path(path)

        doc = json.loads(path.read_text())

        return cls(
            apikey=doc['apikey'],
        )


def find_native_credentials_directory(directory: Union[str, Path]) -> Optional[Path]:
    """
    Return the directory that holds `api-key.txt`: `directory` itself, or its `combocurve/`
    folder from the ZIP. None when neither holds it.
    """
    directory = Path(directory)
    for candidate in (directory, directory / CREDENTIALS_ZIP_FOLDER):
        if (candidate / API_KEY_TXT).is_file():
            return candidate
    return None


def read_api_key(directory: Path) -> str:
    """
    Read the API key from `api-key.txt` in `directory`, without surrounding whitespace.
    """
    return (directory / API_KEY_TXT).read_text().strip()


def _load_default_configuration() -> Configuration:
    """
    The API key from `~/.combocurve`: the native `api-key.txt` first, so that it matches the
    credentials `ComboCurveAPI()` picks, then the older `cc-api.config.json`. Raises
    `FileNotFoundError` when neither exists.
    """
    native_directory = find_native_credentials_directory(COMBOCURVE_DIRECTORY)
    if native_directory is not None:
        return Configuration(apikey=read_api_key(native_directory))
    return Configuration.from_file(CC_API_CONFIG_JSON)


cfg = _load_default_configuration()
