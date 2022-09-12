from dataclasses import dataclass
import random

from src.constants import TOKENS, TOKEN_PROBABILITIES
from src.store import Account
from src.task import Task, TaskResult


@dataclass
class Faucet(Task):
    FAUCET_AMOUNT_LIMIT: int = 1000

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        account = Account.get_random_account()
        amount = random.randint(0, self.FAUCET_AMOUNT_LIMIT)
        token = random.choices(TOKENS, TOKEN_PROBABILITIES).pop()

        command = self.client.faucet(account.alias, token, amount, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        changed_rows = Account.update_account_balance(account.alias, token, amount)
        self.assert_row_affected(1, changed_rows)

        return TaskResult(
            self.task_name,
            ' '.join(command),
            stdout,
            stderr,
            step_index,
            self.seed
        )
