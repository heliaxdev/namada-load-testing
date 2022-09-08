import random
from dataclasses import dataclass

from src.store import Account
from src.task import Task, TaskResult


@dataclass
class Transfer(Task):
    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        from_account = Account.get_random_account_with_positive_balance()
        to_account = Account.get_random_account()
        token = from_account.token
        amount = random.randint(0, from_account.amount)

        command = self.client.transfer(from_account.alias, to_account.alias, token, amount, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)
        if not is_successful:
            raise Exception("Can't transfer {} from {} to {}.".format(amount, from_account.alias, to_account.alias))

        changed_rows = Account.update_account_balance(from_account.alias, token, -amount)
        self.assert_row_affected(1, changed_rows)
        changed_rows = Account.update_account_balance(to_account.alias, token, amount)
        self.assert_row_affected(1, changed_rows)

        return TaskResult(
            self.task_name,
            command,
            stdout,
            stderr,
            step_index,
            self.seed
        )
