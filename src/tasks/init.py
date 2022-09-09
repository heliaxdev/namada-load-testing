import string
from dataclasses import dataclass
from random import choice
from typing import Tuple, List, Dict

from src.constants import TOKENS, ACCOUNT_FORMAT
from src.store import Account, Validator, Delegation, Withdrawal
from src.task import Task, TaskResult


@dataclass
class Init(Task):
    MIN_ACCOUNT_PER_RUN = 10

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        aliases, addresses = self._get_all_alias_and_addresses()
        validator_addresses = self._get_all_validators(ledger_address)
        delegations = self._get_delegations(addresses, validator_addresses, ledger_address)
        withdrawals = self._get_withdrawals(addresses, validator_addresses, ledger_address)

        self._setup_accounts(aliases, addresses, ledger_address)
        alias_balances = self._get_all_balances(aliases, ledger_address)
        self._init_storage(aliases, addresses, validator_addresses, alias_balances, delegations, withdrawals)

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
        while i < self.MIN_ACCOUNT_PER_RUN:
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

    def _get_delegations(self, account_addresses: List[str], validator_addresses: List[str], ledger_address: str) -> List[Tuple[str, str, int, int]]:
        command = self.client.get_delegations(ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't read bonds.")

        delegations = self.parser.parse_client_delegations(stdout)

        filtered_delegations = []
        for delegation in delegations:
            if not delegation[0] in account_addresses:
                continue
            if not delegation[1] in validator_addresses:
                continue
            filtered_delegations.append(delegation)

        return filtered_delegations

    def _get_withdrawals(self, account_addresses: List[str], validator_addresses: List[str], ledger_address: str) -> List[Tuple[str, str, int, int, int]]:
        command = self.client.get_delegations(ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't read bonds.")

        withdrawals = self.parser.parse_client_withdrawals(stdout)

        filtered_withdrawals = []
        for withdrawal in withdrawals:
            if not withdrawal[0] in account_addresses:
                continue
            if not withdrawal[1] in validator_addresses:
                continue
            filtered_withdrawals.append(withdrawal)

        return filtered_withdrawals

    @staticmethod
    def _init_storage(aliases: List[str], addresses: List[str], validator_addresses: List[str], alias_balances: Dict[str, Dict[str, int]], delegations: List[Tuple[str, str, int, int]], withdrawals: List[Tuple[str, str, int, int, int]]):
        for account in zip(aliases, addresses):
            alias, address = account
            for token in TOKENS:
                token_amount = alias_balances[alias].get(token, 0)
                Account.create_account(alias, address, token, token_amount)

        for address in validator_addresses:
            Validator.create_validator(address)

        for delegation in delegations:
            delegator_address = delegation[0]
            validator_address = delegation[1]
            epoch = delegation[2]
            amount = delegation[3]

            delegator_account = Account.get_by_address(delegator_address)
            validator_account = Validator.get_by_address(validator_address)

            Delegation.create_delegation(delegator_account.get_id(), validator_account.get_id(), amount, epoch)

        for withdrawal in withdrawals:
            delegator_address = withdrawal[0]
            validator_address = withdrawal[1]
            epoch = withdrawal[2]
            amount = withdrawal[4]
            active_epoch = withdrawal[3]

            delegator_account = Account.get_by_address(delegator_address)
            validator_account = Validator.get_by_address(validator_address)

            Withdrawal.create_withdrawal(delegator_account.get_id(), validator_account.get_id(), amount, epoch)

    @staticmethod
    def _generate_alias(seed: int) -> str:
        return "{0}-{1}-{2}-{3}-{4}".format(''.join(choice(string.ascii_lowercase) for x in range(3)),
                                        ''.join(choice(string.ascii_lowercase) for x in range(3)),
                                        ''.join(choice(string.ascii_lowercase) for x in range(3)),
                                        ''.join(choice(string.ascii_lowercase) for x in range(3)),
                                           seed)








