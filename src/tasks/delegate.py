from dataclasses import dataclass

from src.constants import BOND_AMOUNT
from src.store import Account, Validator, Delegation
from src.task import Task, TaskResult


@dataclass
class Delegate(Task):
    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        delegator = Account.get_random_account_with_balance_grater_than(BOND_AMOUNT * 2)
        validator = Validator.get_random_validator()
        amount = BOND_AMOUNT

        command = self.client.bond(delegator.alias, validator.address, amount, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            raise Exception("Can't bond {} from {} to {}.".format(amount, delegator.alias, validator.address))

        epoch_command = self.client.get_current_epoch(ledger_address)
        is_successful, epoch_stdout, epoch_stderr = self.execute_command(epoch_command)

        if not is_successful:
            raise Exception("Can't query current epoch.")

        current_epoch = self.parser.parse_client_epoch(epoch_stdout)
        Delegation.create_delegation(delegator.get_id(), validator.get_id(), amount, current_epoch)
        affected_rows = Account.update_account_balance(delegator.alias, 'XAN', -amount)
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(
            self.task_name,
            command,
            stdout,
            stderr,
            step_index,
            self.seed
        )
