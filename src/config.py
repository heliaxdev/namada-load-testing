import sys
from dataclasses import dataclass
from typing import Dict, List, Union

from ruamel import yaml


@dataclass
class Config:
    data: Dict

    @staticmethod
    def read(config_path: str) -> 'Config':
        with open(config_path, "r") as stream:
            return Config(yaml.safe_load(stream))

    def get_settings(self) -> Dict[str, Union[str, int, bool]]:
        return self.data['settings']

    def get_total_transaction(self) -> int:
        total_tx = sys.maxsize if self.get_settings()['total_tx'] == -1 else self.get_settings()['total_tx']
        return total_tx

    def get_seed(self) -> int:
        return self.get_settings()['seed']

    def get_dry_run(self) -> bool:
        return self.get_settings()['dry_run']

    def get_nodes(self) -> List[str]:
        return self.data['nodes']

    def get_tasks(self) -> List[Dict[str, Union[str, int]]]:
        return self.data['tasks']
