from dataclasses import dataclass
from typing import Union, List

from src.constants import ACCOUNT_FORMAT


@dataclass
class Command:
    base_binary: str

    def _get_full_command(self, sub_binary: str, command: str, ledger_address: Union[str, None]) -> List[str]:
        if ledger_address:
            return "{0} {1} {2} --ledger-address {3}".format(self.base_binary, sub_binary, command,
                                                             ledger_address).split(' ')
        else:
            return "{0} {1} {2}".format(self.base_binary, sub_binary, command).split(' ')

    @staticmethod
    def _remove_prefix(text, prefix):
        return text[text.startswith(prefix) and len(prefix):]


@dataclass
class WalletCommands(Command):
    sub_binary: str = "wallet"

    def address_list(self) -> List[str]:
        return self._get_full_command(self.sub_binary, "address list", None)

    def generate_key(self, alias: str) -> List[str]:
        return self._get_full_command(self.sub_binary, "key gen --alias {0} --unsafe-dont-encrypt".format(alias), None)


@dataclass
class ClientCommands(Command):
    sub_binary: str = "client"

    def get_current_epoch(self, ledger_address: str):
        return self._get_full_command(self.sub_binary, "epoch", ledger_address)

    def get_current_validators(self, ledger_address: str):
        return self._get_full_command(self.sub_binary, "voting-power", ledger_address)

    def get_account_balance(self, owner: str, ledger_address: str):
        return self._get_full_command(self.sub_binary, "balance --owner {0}".format(owner), ledger_address)

    def get_delegations(self, ledger_address: str):
        return self._get_full_command(self.sub_binary, "bonds", ledger_address)

    def get_proposal(self, proposal_id: Union[int, None], ledger_address: str):
        if proposal_id:
            return self._get_full_command(self.sub_binary, "query-proposal --proposal-id {0}".format(proposal_id),
                                          ledger_address)
        else:
            return self._get_full_command(self.sub_binary, "query-proposal", ledger_address)

    def init_account(self, alias: str, ledger_address: str):
        return self._get_full_command(self.sub_binary,
                                      "init-account --alias {0}-{1} --public-key {1} --source {1}".format(
                                          ACCOUNT_FORMAT, alias), ledger_address)

    def faucet(self, account_alias: str, token: str, amount: int, ledger_address: str):
        signer = self._remove_prefix(account_alias, "{}-".format(ACCOUNT_FORMAT))
        return self._get_full_command(self.sub_binary,
                                      "transfer --source faucet --target {0} --signer {1} --token {2} --amount {3}".format(
                                          account_alias, signer, token, amount), ledger_address)

    def transfer(self, from_alias: str, to_alias: str, token: str, amount: int, ledger_address: str):
        signer = self._remove_prefix(from_alias, "{}-".format(ACCOUNT_FORMAT))
        return self._get_full_command(self.sub_binary,
                                      "transfer --source {0} --target {1} --signer {2} --token {3} --amount {4}".format(
                                          from_alias, to_alias, signer, token, amount), ledger_address)

    def bond(self, from_alias: str, to_validator: str, amount: int, ledger_address: str):
        return self._get_full_command(self.sub_binary,
                                      "bond --source {0} --validator {1} --amount {2}".format(from_alias, to_validator,
                                                                                              amount), ledger_address)

    def unbond(self, from_alias: str, to_validator: str, amount: int, ledger_address: str):
        return self._get_full_command(self.sub_binary,
                                      "unbond --source {0} --validator {1} --amount {2}".format(from_alias,
                                                                                                to_validator, amount),
                                      ledger_address)

    def withdraw(self, from_alias: str, to_validator: str, ledger_address: str):
        return self._get_full_command(self.sub_binary,
                                      "withdraw --source {0} --validator {1}".format(from_alias, to_validator),
                                      ledger_address)

    def init_proposal(self, proposal_path: str, ledger_address: str):
        return self._get_full_command(self.sub_binary, "init-proposal --data-path {0}".format(proposal_path),
                                      ledger_address)

    def vote_proposal(self, proposal_id: int, vote: str, signer: str, ledger_address: str):
        return self._get_full_command(self.sub_binary,
                                      "vote-proposal --proposal-id {0} --vote {1} --signer {2}".format(proposal_id,
                                                                                                       vote, signer),
                                      ledger_address)
