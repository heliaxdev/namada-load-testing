import random
from dataclasses import dataclass

from src.store import Account
from src.task import Task, TaskResult


@dataclass
class Transfer(Task):
    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        from_account = Account.get_random_account_with_positive_balance(self.seed)
        if not from_account:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        to_account = Account.get_random_account(self.seed)
        token = from_account.token
        amount = random.randint(0, from_account.amount)

        command = self.client.transfer(from_account.alias, to_account.alias, token, amount, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)
        if not is_successful:
            return TaskResult(self.task_name, command, stdout, stderr, step_index, self.seed)

        changed_rows = Account.update_account_balance(from_account.alias, token, -amount, self.seed)
        self.assert_row_affected(1, changed_rows)
        changed_rows = Account.update_account_balance(to_account.alias, token, amount, self.seed)
        self.assert_row_affected(1, changed_rows)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)
