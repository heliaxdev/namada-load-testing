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
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        delegation_account = Account.get_by_id(withdraw.account_id)
        validator_account = Validator.get_by_id(withdraw.validator_id)

        compatible_withdraws = Withdrawal.get_compatible_withdrawals(delegation_account.get_id(), validator_account.get_id(),current_epoch)
        withdrawable_sum = sum([withdraw.amount for withdraw in compatible_withdraws])

        command = self.client.withdraw(delegation_account.alias, validator_account.address, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        # workaround cause I can't understand how to get the correct withdrawal epoch
        bond_command = self.client.get_delegations(ledger_address)
        _, stdout_bond, _ = self.execute_command(bond_command)

        Withdrawal.delete_all()
        withdrawals = self.parser.parse_client_withdrawals(stdout_bond)
        for withdrawal in withdrawals:
            delegation_account = Account.get_by_address(withdrawal[0])
            validator_account = Validator.get_by_address(withdrawal[1])
            if delegation_account is not None and validator_account is not None:
                Withdrawal.create_withdrawal(delegation_account.get_id(), validator_account.get_id(), withdrawal[4], withdrawal[2])

        affected_rows = Account.update_account_balance(delegation_account.alias, 'XAN', withdrawable_sum)
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)