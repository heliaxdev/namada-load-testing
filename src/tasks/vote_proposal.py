import random
from dataclasses import dataclass
from typing import Tuple

from src.store import Account, Proposal, Delegation
from src.task import Task, TaskResult


@dataclass
class VoteProposal(Task):
    votes: Tuple[str, str] = ('yay', 'nay')

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        epoch_command = self.client.get_current_epoch(ledger_address)
        is_successful, epoch_stdout, epoch_stderr = self.execute_command(epoch_command)

        if not is_successful:
            raise Exception("Can't query current epoch.")

        current_epoch = self.parser.parse_client_epoch(epoch_stdout)

        proposal = Proposal.get_random_votable_proposal(current_epoch)
        if proposal is None:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        delegation = Delegation.get_random_valid_delegation(current_epoch)
        if delegation is None:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        delegation_account = Account.get_by_id(delegation.account_id)
        vote = random.choice(self.votes)

        command = self.client.vote_proposal(proposal.proposal_id, vote, delegation_account.alias, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)
