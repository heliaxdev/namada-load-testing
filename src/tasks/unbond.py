from dataclasses import dataclass

from src.store import Delegation, Account, Validator, Withdrawal
from src.task import Task, TaskResult


@dataclass
class Unbond(Task):
    UNBOND_EPOCH_WAIT: int = 4
    ACTIVE_EPOCH_WAIT: int = 2

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        epoch_command = self.client.get_current_epoch(ledger_address)
        is_successful, epoch_stdout, epoch_stderr = self.execute_command(epoch_command)

        if not is_successful:
            raise Exception("Can't query current epoch.")

        current_epoch = self.parser.parse_client_epoch(epoch_stdout)

        delegation = Delegation.get_random_valid_delegation(current_epoch)
        if not delegation:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        delegation_account = Account.get_by_id(delegation.account_id)
        validator_account = Validator.get_by_id(delegation.validator_id)

        command = self.client.unbond(delegation_account.alias, validator_account.address, delegation.amount, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        # workaround cause I can't understand how to get the correct withdrawal epoch
        bond_command = self.client.get_delegations(ledger_address)
        _, stdout_bond, stderr_bond = self.execute_command(bond_command)

        withdrawals = self.parser.parse_client_withdrawals(stdout_bond)
        Withdrawal.delete_all()
        for withdrawal in withdrawals:
            delegation_account = Account.get_by_address(withdrawal[0])
            validator_account = Validator.get_by_address(withdrawal[1])
            if delegation_account is not None and validator_account is not None:
                Withdrawal.create_withdrawal(delegation_account.get_id(), validator_account.get_id(), withdrawal[4], withdrawal[2])

        Delegation.delete_by_id(delegation.get_id())

        return TaskResult(
            self.task_name,
            ' '.join(command),
            stdout,
            stderr,
            step_index,
            self.seed
        )