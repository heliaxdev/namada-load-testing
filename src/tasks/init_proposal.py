import datetime
import json
import os
import random
import string
from dataclasses import dataclass

from src.store import Account, Proposal
from src.task import Task, TaskResult


@dataclass
class InitProposal(Task):
    PROPOSAL_PATH: str = os.path.abspath(os.path.join(os.path.curdir, "proposal.json"))
    END_EPOCH_FACTOR: int = 3
    GRACE_EPOCH_FACTOR: int = 6
    PROPOSAL_MIN_FUNDS: int = 500
    PROPOSAL_DISCUSSION_URL_FORMAT: str = "www.github.com/namada/nip/{}"
    PROPOSAL_CONTENT = {
        "content": {
            "title": "Proposal title",
            "authors": "test@namada.com",
            "discussions-to": "",
            "created": "-1",
            "license": "MIT",
            "abstract": "Ut convallis eleifend orci vel venenatis. Duis vulputate metus in lacus sollicitudin vestibulum. Suspendisse vel velit ac est consectetur feugiat nec ac urna. Ut faucibus ex nec dictum fermentum. Morbi aliquet purus at sollicitudin ultrices. Quisque viverra varius cursus. Praesent sed mauris gravida, pharetra turpis non, gravida eros. Nullam sed ex justo. Ut at placerat ipsum, sit amet rhoncus libero. Sed blandit non purus non suscipit. Phasellus sed quam nec augue bibendum bibendum ut vitae urna. Sed odio diam, ornare nec sapien eget, congue viverra enim.",
            "motivation": "Ut convallis eleifend orci vel venenatis. Duis vulputate metus in lacus sollicitudin vestibulum. Suspendisse vel velit ac est consectetur feugiat nec ac urna. Ut faucibus ex nec dictum fermentum. Morbi aliquet purus at sollicitudin ultrices.",
            "details": "Ut convallis eleifend orci vel venenatis. Duis vulputate metus in lacus sollicitudin vestibulum. Suspendisse vel velit ac est consectetur feugiat nec ac urna. Ut faucibus ex nec dictum fermentum. Morbi aliquet purus at sollicitudin ultrices. Quisque viverra varius cursus. Praesent sed mauris gravida, pharetra turpis non, gravida eros.",
            "requires": "-1",
        },
        "author": "",
        "voting_start_epoch": -1,
        "voting_end_epoch": -1,
        "grace_epoch": -1,
    }

    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        epoch_command = self.client.get_current_epoch(ledger_address)
        is_successful, epoch_stdout, epoch_stderr = self.execute_command(epoch_command)

        if not is_successful:
            raise Exception("Can't query current epoch.")

        current_epoch = self.parser.parse_client_epoch(epoch_stdout)

        proposer_account = Account.get_random_account_with_balance_grater_than(self.PROPOSAL_MIN_FUNDS, self.seed,
                                                                               ['XAN'])
        if proposer_account is None:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        voting_start_epoch = current_epoch + random.randint(2, 45)
        voting_end_epoch = voting_start_epoch + random.randint(self.END_EPOCH_FACTOR, 45)
        grace_epoch = voting_end_epoch + random.randint(self.GRACE_EPOCH_FACTOR, 20)
        discussion_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        self.PROPOSAL_CONTENT["voting_start_epoch"] = voting_start_epoch - voting_start_epoch % self.END_EPOCH_FACTOR
        self.PROPOSAL_CONTENT["voting_end_epoch"] = voting_end_epoch - voting_end_epoch % self.END_EPOCH_FACTOR
        self.PROPOSAL_CONTENT["grace_epoch"] = grace_epoch
        self.PROPOSAL_CONTENT["author"] = proposer_account.address
        self.PROPOSAL_CONTENT['content']['discussion-to'] = self.PROPOSAL_DISCUSSION_URL_FORMAT.format(discussion_id)
        self.PROPOSAL_CONTENT['content']['created'] = str(datetime.datetime.now().replace(microsecond=0).isoformat())

        with open(self.PROPOSAL_PATH, "w") as f:
            json.dump(self.PROPOSAL_CONTENT, f)

        command = self.client.init_proposal(self.PROPOSAL_PATH, ledger_address)
        is_successful, stdout, stderr = self.execute_command(command)

        if not is_successful:
            return TaskResult(self.task_name, "", "", "", step_index, self.seed)

        proposal_id = Proposal.get_last_proposal_id(self.seed)
        proposal_id = 0 if not proposal_id and proposal_id != 0 else proposal_id + 1

        Proposal.create_proposal(proposal_id, proposer_account.get_id(), voting_start_epoch, voting_end_epoch,
                                 self.seed)
        affected_rows = Account.update_account_balance(proposer_account.alias, 'XAN', -self.PROPOSAL_MIN_FUNDS,
                                                       self.seed)
        self.assert_row_affected(affected_rows, 1)

        return TaskResult(self.task_name, ' '.join(command), stdout, stderr, step_index, self.seed)
