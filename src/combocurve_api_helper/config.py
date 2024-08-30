import json
from pathlib import Path
from typing import List, Dict, NamedTuple, Union
from typing_extensions import Self


USER_HOME = Path.home()
PACKAGE_ROOT = Path(__file__).parent.resolve()

COMBOCURVE_JSON = USER_HOME / '.combocurve' / 'combocurve.json'
CC_API_CONFIG_JSON = USER_HOME / '.combocurve' / 'cc-api.config.json'

REFERENCE_WELLHEADER: Dict[str, Union[str, int, float, bool]] = json.loads(
    (PACKAGE_ROOT / 'assets' / 'wellHeader.json').read_text())

ECON_MODELS: List[Dict[str, str]] = json.loads(
    (PACKAGE_ROOT / 'assets' / 'econModels.json').read_text())


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

# default to the configuration file bundled with the package
cfg = Configuration.from_file(CC_API_CONFIG_JSON)
