import random
from dataclasses import dataclass

from src.store import Account, Validator, Delegation
from src.task import Task, TaskResult


@dataclass
class Delegate(Task):
    BOND_AMOUNT_MAX: int = 10
    BOND_AMOUNT_MIN: int = 1
    ACTIVE_EPOCH_WAIT: int = 2

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        amount = random.randint(self.BOND_AMOUNT_MIN, self.BOND_AMOUNT_MAX)
        delegator = Account.get_random_account_with_balance_greater_than(amount, self.seed, tokens=['NAM'])
        if not delegator:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        validator = Validator.get_random_validator(self.seed)

        command = self.client.bond(delegator.alias, validator.address, amount, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, command, stdout, stderr, step_index, self.seed)

        tx_epoch_execution = self.parser.parse_epoch_from_tx_execution(stdout)

        Delegation.create_delegation(delegator.get_id(), validator.get_id(), amount,
                                     tx_epoch_execution + self.ACTIVE_EPOCH_WAIT, self.seed)
        affected_rows = Account.update_account_balance(delegator.alias, 'NAM', -amount, self.seed)
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)
