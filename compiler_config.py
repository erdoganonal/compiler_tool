"Config file parser"
import os
import json

CONFIG_FILE = os.path.join(
    os.path.expanduser("~"),
    ".compiler_config"
)


class _Configurations:
    def __init__(self):
        try:
            with open(CONFIG_FILE) as config_file:
                self._config = json.loads(config_file.read())["general_config"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self._config = {}

    def __getattr__(self, key):
        try:
            return self._config[key]
        except KeyError as error:
            raise AttributeError(error)

    def get(self, key, default):
        "returns the given key"
        return getattr(self, key, default)

    def get_all(self):
        "return entire configurations"
        return self._config


CONFIGURATIONS = _Configurations()
