import json
from pathlib import Path
from typing import NamedTuple
from typing_extensions import Self


USER_HOME = Path.home()
PACKAGE_ROOT = Path(__file__).parent.resolve()

COMBOCURVE_JSON = USER_HOME / '.combocurve' / 'combocurve.json'
CC_API_CONFIG_JSON = USER_HOME / '.combocurve' / 'cc-api.config.json'
REFRENCE_WELLS_JSON = PACKAGE_ROOT / 'assets' / 'ref_wells.json'


class Configuration(NamedTuple):
    apikey: str

    @classmethod
    def from_path(cls, path: Path) -> Self:
        """
        Parse the contents of a `ccfs.config.json` file from a path.
        """
        doc = json.loads(path.read_text())

        return cls(
            apikey=doc['apikey'],
        )

# default to the configuration file bundled with the package
cfg = Configuration.from_path(CC_API_CONFIG_JSON)
