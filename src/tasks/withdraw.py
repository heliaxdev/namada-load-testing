from dataclasses import dataclass

from src.store import Account, Validator, Withdrawal
from src.task import Task, TaskResult


@dataclass
class Withdraw(Task):

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        epoch_command = self.client.get_current_epoch(ledger_address)
        is_successful, epoch_stdout, epoch_stderr = self.execute_command(epoch_command)

        if not is_successful:
            raise Exception("Can't query current epoch.")

        current_epoch = self.parser.parse_client_epoch(epoch_stdout)

        withdraw = Withdrawal.get_random_withdrawable_withdraw(current_epoch, self.seed)
        if not withdraw:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        delegation_account = Account.get_by_id(withdraw.account_id)
        validator_account = Validator.get_by_id(withdraw.validator_id)

        if delegation_account is None or validator_account is None:
            Withdrawal.delete_by_id(withdraw.get_id())
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        compatible_withdraws = Withdrawal.get_compatible_withdrawals(delegation_account.get_id(),
                                                                     validator_account.get_id(), current_epoch,
                                                                     self.seed)
        withdrawable_sum = sum([withdraw.amount for withdraw in compatible_withdraws])

        command = self.client.withdraw(delegation_account.alias, validator_account.address, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, command, stdout, stderr, step_index, self.seed)

        for withdraw in compatible_withdraws:
            Withdrawal.delete_by_id(withdraw.get_id())

        affected_rows = Account.update_account_balance(delegation_account.alias, 'NAM', withdrawable_sum, self.seed)
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)
