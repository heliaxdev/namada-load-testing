from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.constants import ACCOUNT_FORMAT


@dataclass
class Parser:

    @staticmethod
    def parse_wallet_address_list(output: str) -> Tuple[List[str], List[str]]:
        aliases, addresses = [], []
        for line in output.splitlines()[1:]:
            tmp = line.split(':')
            alias = tmp[0][3:-1].strip()
            address = tmp[2].strip()
            aliases.append(alias)
            addresses.append(address)
        return aliases, addresses

    @staticmethod
    def parse_client_validators(output: str) -> List[str]:
        validator_addresses = []
        for line in output.splitlines()[3:-1]:
            address = line.split(':')[0].strip()
            validator_addresses.append(address)
        return validator_addresses

    @staticmethod
    def parse_client_balance_owner(output: str) -> Dict[str, int]:
        balance_map = {}
        for line in output.splitlines()[1:]:
            if 'No balance found' in line:
                continue
            tmp = line.split(':')
            token = tmp[0].strip()
            amount = int(tmp[1].strip())
            balance_map[token] = amount
        return balance_map

    @staticmethod
    def parse_wallet_gen_key(output: str) -> str:
        return output.splitlines()[1].split(':')[1].strip()[1:-1]

    @staticmethod
    def parse_client_init_account(output: str) -> Tuple[str, str]:
        tmp = output.splitlines()[-1].split(' ')
        return tmp[2].strip(), tmp[-1][:-1].strip()

    @staticmethod
    def parse_client_epoch(output: str) -> int:
        return int(output.splitlines()[1].split(': ')[1])
