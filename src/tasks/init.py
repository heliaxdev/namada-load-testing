import logging
import string
from dataclasses import dataclass
from random import choice
from time import sleep
from typing import Tuple, List, Dict

from src.constants import TOKENS, ACCOUNT_FORMAT
from src.store import Account, Validator, Delegation, Withdrawal, Proposal
from src.task import Task, TaskResult
import logging


@dataclass
class Init(Task):
    MIN_ACCOUNT_PER_RUN = 5

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        logging.info("Parsing aliases and addresses...")
        aliases, addresses = self._get_all_alias_and_addresses()
        logging.info("Parsed {} aliases and {} addresses!".format(len(aliases), len(addresses)))
        logging.info("Parsing validators...")
        validator_addresses = self._get_all_validators(ledger_address)
        logging.info("Parsed {} validators!".format(len(validator_addresses)))
        logging.info("Parsing delegations...")
        delegations = self._get_delegations(addresses, validator_addresses, ledger_address)
        logging.info("Parsed {} delegations!".format(len(delegations)))
        logging.info("Parsing withdrawals...")
        withdrawals = self._get_withdrawals(addresses, validator_addresses, ledger_address)
        logging.info("Parsed {} withdrawals!".format(len(withdrawals)))
        logging.info("Parsing proposals...")
        proposals = self._get_all_proposals(ledger_address)
        logging.info("Parsed {} proposals!".format(len(proposals)))

        logging.info("Setup accounts...")
        self._setup_accounts(aliases, addresses, ledger_address)
        logging.info("Setup balances...")
        alias_balances = self._get_all_balances(aliases, ledger_address)
        logging.info("Init storage...")
        self._init_storage(aliases, addresses, validator_addresses, alias_balances, delegations, withdrawals, proposals)
        logging.info("Done!")

        return TaskResult(self.task_name, "", "", "", step_index, self.seed)

    def _get_all_alias_and_addresses(self) -> Tuple[List[str], List[str]]:
        command = self.wallet.address_list()
        is_successful, stdout, _stderr = self.execute_command(command)

        print(_stderr)

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

        print(stdout)

        if not is_successful:
            logging.debug(stdout)
            logging.debug(stderr)
            raise Exception("Can't list validators.")

        return self.parser.parse_client_validators(stdout)

    def _get_all_balances(self, aliases: List[str], ledger_address: str) -> Dict[str, Dict[str, int]]:
        balance_map = {}
        for alias in aliases:
            command = self.client.get_account_balance(alias, ledger_address)
            is_successful, stdout, stderr = self.execute_command(command)

            if not is_successful:
                logging.debug(stderr)
                raise Exception("Can't get balance of {}.".format(alias))

            owner_balances = self.parser.parse_client_balance_owner(stdout)
            balance_map[alias] = owner_balances
        return balance_map

    def _get_all_proposals(self, ledger_address: str) -> List[Tuple[int, str, int, int, str]]:
        command = self.client.get_proposal(None, ledger_address)
        is_successful, stdout, _stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't get proposals")

        return self.parser.parse_client_proposals(stdout)

    def _setup_accounts(self, aliases: List[str], addresses: List[str], ledger_address: str):
        i = len(aliases)
        while i < self.MIN_ACCOUNT_PER_RUN:
            alias, address = self._create_account(ledger_address)
            aliases.append(alias)
            addresses.append(address)
            logging.info("Created new account {} with alias {}...".format(address, alias))
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
            logging.debug(stdout)
            logging.debug('stderr is:')
            logging.debug(stderr)
            raise Exception("Can't init account with alias {}.".format(alias))

        account_alias, account_address = self.parser.parse_client_init_account(stdout)

        return account_alias, account_address

    def _get_delegations(self, account_addresses: List[str], validator_addresses: List[str], ledger_address: str) -> \
            List[Tuple[str, str, int, int]]:
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

    def _get_withdrawals(self, account_addresses: List[str], validator_addresses: List[str], ledger_address: str) -> \
            List[Tuple[str, str, int, int, int]]:

        all_withdrawals = []

        print(validator_addresses)

        for validator_address in validator_addresses:
            for account_address in account_addresses:
                command = self.client.get_delegations_by_owner_and_validator(account_address, validator_address, ledger_address)
                print(command)
                is_successful, stdout, stderr = self.execute_command(command)

                if not is_successful:
                    print(stderr)
                    raise Exception("Can't read bonds.")

                withdrawals = self.parser.parse_client_withdrawals(stdout, validator_address)
                all_withdrawals.extend(withdrawals)

        return all_withdrawals

    def _init_storage(self, aliases: List[str], addresses: List[str], validator_addresses: List[str],
                      alias_balances: Dict[str, Dict[str, int]], delegations: List[Tuple[str, str, int, int]],
                      withdrawals: List[Tuple[str, str, int, int, int]],
                      proposals: List[Tuple[int, str, int, int, str]]):
        for account in zip(aliases, addresses):
            alias, address = account
            for token in TOKENS:
                token_amount = alias_balances[alias].get(token, 0)
                Account.create_account(alias, address, token, token_amount, self.seed)

        for address in validator_addresses:
            Validator.create_validator(address, self.seed)

        for delegation in delegations:
            delegator_address = delegation[0]
            validator_address = delegation[1]
            epoch = delegation[2]
            amount = delegation[3]

            delegator_account = Account.get_by_address(delegator_address, self.seed)
            validator_account = Validator.get_by_address(validator_address, self.seed)

            if validator_account is None or delegator_account is None:
                continue

            Delegation.create_delegation(delegator_account.get_id(), validator_account.get_id(), amount, epoch,
                                         self.seed)

        for withdrawal in withdrawals:
            delegator_address = withdrawal[0]
            validator_address = withdrawal[1]
            epoch = withdrawal[2]
            amount = withdrawal[4]

            delegator_account = Account.get_by_address(delegator_address, self.seed)
            validator_account = Validator.get_by_address(validator_address, self.seed)

            if validator_account is None or delegator_account is None:
                continue

            Withdrawal.create_withdrawal(delegator_account.get_id(), validator_account.get_id(), amount, epoch,
                                         self.seed)

        for proposal in proposals:
            proposal_id = proposal[0]
            proposal_author = proposal[1]
            proposal_start_epoch = proposal[2]
            proposal_end_epoch = proposal[3]
            proposal_status = proposal[4]

            if proposal_status != 'pending' and proposal_status != 'on-going':
                continue

            proposer_account = Account.get_by_address(proposal_author, self.seed)
            if proposer_account is None:
                continue

            Proposal.create_proposal(proposal_id, proposer_account.get_id(), proposal_start_epoch, proposal_end_epoch,
                                     self.seed)

    @staticmethod
    def _generate_alias(seed: int) -> str:
        return "{0}-{1}-{2}-{3}-{4}".format(''.join(choice(string.ascii_lowercase) for _ in range(3)),
                                            ''.join(choice(string.ascii_lowercase) for _ in range(3)),
                                            ''.join(choice(string.ascii_lowercase) for _ in range(3)),
                                            ''.join(choice(string.ascii_lowercase) for _ in range(3)),
                                            seed)
