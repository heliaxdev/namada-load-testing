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

        withdraw = Withdrawal.get_random_withdrawable_withdraw(current_epoch)
        if not withdraw:
            return TaskResult(
                self.task_name,
                "",
                "",
                "",
                step_index,
                self.seed
            )

        delegation_account = Account.get_by_id(withdraw.account_id)
        validator_account = Validator.get_by_id(withdraw.validator_id)

        compatible_withdraws = Withdrawal.get_compatible_withdrawals(delegation_account.get_id(), validator_account.get_id(),current_epoch)
        withdrawable_sum = sum([withdraw.amount for withdraw in compatible_withdraws])
        withdrawals_id = [withdraw.id for withdraw in compatible_withdraws]

        command = self.client.withdraw(delegation_account.alias, validator_account.address, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            TaskResult(
                self.task_name,
                ' '.join(command),
                stdout,
                stderr,
                step_index,
                self.seed
            )

        # affected_rows = Withdrawal.delete_withdraws(delegation_account.get_id(), validator_account.get_id(), current_epoch)
        affected_rows = sum([Withdrawal.delete_by_id(id) for id in withdrawals_id])
        self.assert_row_affected(affected_rows, len(compatible_withdraws))
        affected_rows = Account.update_account_balance(delegation_account.alias, 'XAN', withdrawable_sum)
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(
            self.task_name,
            ' '.join(command),
            stdout,
            stderr,
            step_index,
            self.seed
        )