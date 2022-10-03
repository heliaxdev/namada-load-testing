from dataclasses import dataclass
from typing import Dict, List, Tuple


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

        token = None
        for line in output.splitlines()[1:]:
            if 'No balances owned' in line:
                continue
            if 'Token' in line:
                token = line.split(' ')[1]
                continue
            tmp = line.split(':')[1].split(',')[0]
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

    @staticmethod
    def parse_client_delegations(output: str) -> List[Tuple[str, str, int, int]]:
        delegator_address = None
        validator_address = None
        bonds = []
        for line in output.splitlines()[2:]:
            if line.strip().startswith('Delegations from'):
                tmp = line.split(' ')
                delegator_address = Parser._remove_symbols(tmp[2])
                validator_address = Parser._remove_symbols(tmp[5])
            elif line.strip().startswith('Active') and (
                    delegator_address is not None and validator_address is not None):
                tmp = line.strip().split()
                epoch = Parser._remove_symbols(tmp[3])
                amount = Parser._remove_symbols(tmp[5])
                bonds.append((delegator_address, validator_address, int(epoch), int(amount)))
            elif line.strip().startswith('Self-bonds'):
                delegator_address = None
                validator_address = None

        return bonds

    @staticmethod
    def parse_client_withdrawals(output: str) -> List[Tuple[str, str, int, int, int]]:
        delegator_address = None
        validator_address = None
        withdrawals = []
        for line in output.splitlines()[2:]:
            if line.strip().startswith('Unbonded delegations'):
                tmp = line.split(' ')
                delegator_address = Parser._remove_symbols(tmp[3])
                validator_address = Parser._remove_symbols(tmp[6])
            elif line.strip().startswith('Withdrawable from') and (
                    delegator_address is not None and validator_address is not None):
                tmp = line.strip().split()
                epoch = Parser._remove_symbols(tmp[3])
                epoch_active = Parser._remove_symbols(tmp[6])
                amount = Parser._remove_symbols(tmp[8])
                withdrawals.append((
                    delegator_address, validator_address, epoch, epoch_active, amount
                ))

        return withdrawals

    @staticmethod
    def parse_client_proposals(output: str) -> List[Tuple[int, str, int, int, str]]:
        proposals = []
        output = output.splitlines()[2:]
        for index, line in enumerate(output[::5]):
            proposal_id = int(line.split(': ')[1])
            status = output[4 + index * 5].split(': ')[1].strip()
            author = output[1 + index * 5].split(': ')[1].strip()
            start_epoch = int(output[2 + index * 5].split(': ')[1].strip())
            end_epoch = int(output[3 + index * 5].split(': ')[1].strip())
            proposals.append((proposal_id, author, start_epoch, end_epoch, status))

        return proposals

    @staticmethod
    def parse_epoch_from_tx_execution(output: str) -> int:
        for line in output.splitlines():
            if line.strip().startswith('Last committed epoch'):
                return int(line.split(': ')[1])
        # very unsafe but it should never happen
        return None

    @staticmethod
    def _remove_symbols(string: str):
        return ''.join(c for c in string if c.isalnum())
