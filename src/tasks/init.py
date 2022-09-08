import string
from dataclasses import dataclass
from random import choice
from typing import Tuple, List, Dict

from src.constants import MIN_ACCOUNT_PER_RUN, TOKENS, ACCOUNT_FORMAT
from src.store import Account, Validator
from src.task import Task, TaskResult


@dataclass
class Init(Task):
    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        aliases, addresses = self._get_all_alias_and_addresses()
        validator_addresses = self._get_all_validators(ledger_address)

        self._setup_accounts(aliases, addresses, ledger_address)
        alias_balances = self._get_all_balances(aliases, ledger_address)
        self._init_storage(aliases, addresses, validator_addresses, alias_balances)

        return TaskResult(
            self.task_name,
            "",
            "",
            "",
            step_index,
            self.seed
        )

    def _get_all_alias_and_addresses(self) -> Tuple[List[str], List[str]]:
        command = self.wallet.address_list()
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't list wallet addresses.")

        aliases, addresses = self.parser.parse_wallet_address_list(stdout)
        filtered_aliases, filtered_addresses = [], []

        for account in zip(aliases, addresses):
            alias, address = account
            if ACCOUNT_FORMAT in alias and str(self.seed) in alias:
                filtered_aliases.append(alias)
                filtered_addresses.append(address)

        return filtered_aliases, filtered_addresses

    def _get_all_validators(self, ledger_address: str):
        command = self.client.get_current_validators(ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't list validators.")

        return self.parser.parse_client_validators(stdout)

    def _get_all_balances(self, aliases: List[str], ledger_address: str) -> Dict[str, Dict[str, int]]:
        balance_map = {}
        for alias in aliases:
            command = self.client.get_account_balance(alias, ledger_address)
            is_successful, stdout, stderr = self.execute_command(command)

            if not is_successful:
                raise Exception("Can't get balance of {}.".format(alias))

            owner_balances = self.parser.parse_client_balance_owner(stdout)
            balance_map[alias] = owner_balances
        return balance_map

    def _setup_accounts(self, aliases: List[str], addresses: List[str], ledger_address: str):
        i = len(aliases)
        while i < MIN_ACCOUNT_PER_RUN:
            alias, address = self._create_account(ledger_address)
            aliases.append(alias)
            addresses.append(address)
            i += 1

    def _create_account(self, ledger_address: str) -> Tuple[str, str]:
        alias = self._generate_alias(self.seed)
        command = self.wallet.generate_key(alias)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't create wallet key.")

        key_alias = self.parser.parse_wallet_gen_key(stdout)

        command = self.client.init_account(key_alias, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't init account with alias {}.".format(alias))

        account_alias, account_address = self.parser.parse_client_init_account(stdout)

        return account_alias, account_address

    @staticmethod
    def _init_storage(aliases: List[str], addresses: List[str], validator_addresses: List[str], alias_balances: Dict[str, Dict[str, int]]):
        for account in zip(aliases, addresses):
            alias, address = account
            for token in TOKENS:
                token_amount = alias_balances[alias].get(token, 0)
                Account.create_account(alias, address, token, token_amount)

        for address in validator_addresses:
            Validator.create_validator(address)

    @staticmethod
    def _generate_alias(seed: int) -> str:
        return "{0}-{1}-{2}-{3}-{4}".format(''.join(choice(string.ascii_lowercase) for x in range(3)),
                                        ''.join(choice(string.ascii_lowercase) for x in range(3)),
                                        ''.join(choice(string.ascii_lowercase) for x in range(3)),
                                        ''.join(choice(string.ascii_lowercase) for x in range(3)),
                                           seed)








