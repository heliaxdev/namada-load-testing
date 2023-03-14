from dataclasses import dataclass

from src.store import Delegation, Account, Validator, Withdrawal
from src.task import Task, TaskResult


@dataclass
class Unbond(Task):
    WITHDRAWAL_EPOCH_WAIT: int = 7

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        epoch_command = self.client.get_current_epoch(ledger_address)
        is_successful, epoch_stdout, epoch_stderr = self.execute_command(epoch_command)

        if not is_successful:
            raise Exception("Can't query current epoch.")

        current_epoch = self.parser.parse_client_epoch(epoch_stdout)

        delegation = Delegation.get_random_valid_delegation(current_epoch, self.seed)
        if not delegation:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        delegation_account = Account.get_by_id(delegation.account_id)
        validator_account = Validator.get_by_id(delegation.validator_id)

        command = self.client.unbond(delegation_account.alias, validator_account.address, delegation.amount,
                                     ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, command, stdout, stderr, step_index, self.seed)

        withdrawals = self.parser.parse_withdrawal_from_unbond_tx(stdout)
        for withdrawal in withdrawals:
            Withdrawal.create_withdrawal(delegation_account.get_id(), validator_account.get_id(), withdrawal[1],
                                         withdrawal[0], self.seed)

        affected_rows = Delegation.delete_by_id(delegation.get_id())
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)
