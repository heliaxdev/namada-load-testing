import logging
import random
from dataclasses import dataclass, field
from shutil import rmtree
from typing import List, Tuple, Dict, Union

from src.config import Config
from src.constants import LOCAL_LEDGER_ADDRESS
from src.task import Task
from src.tasks.delegate import Delegate
from src.tasks.faucet import Faucet
from src.tasks.init import Init
from src.tasks.init_proposal import InitProposal
from src.tasks.transfer import Transfer
from src.tasks.unbond import Unbond
from src.tasks.vote_proposal import VoteProposal
from src.tasks.withdraw import Withdraw


@dataclass
class Manager:
    name: str
    config: Config
    seed: int
    all_tasks: Dict = field(init=False)
    stats: Dict = field(init=False)
    r: random.Random = field(init=False)

    def __post_init__(self):
        tasks = self.config.get_tasks()
        self.stats = {task_name: {'succeeded': 0, 'failed': 0} for task_name in [task['type'] for task in tasks]}

        self.r = random.Random(self.seed)
        random.seed(self.seed)

        rmtree("logs/{}".format(self.seed), ignore_errors=True)

    def run(self, base_directory: str, base_binary: str, fail_fast: bool) -> bool:
        nodes = self.config.get_nodes()
        tasks = self.config.get_tasks()

        all_tasks = self._build_all_tasks(base_directory, base_binary, self.seed)
        task_types, task_probabilities = self._build_task_with_probabilities(tasks)

        # run the init task once
        logging.info("{0}-{1} - Running {2} against {3}".format(self.name, 0, 'Init', LOCAL_LEDGER_ADDRESS))
        all_tasks['Init'].run(0, base_directory, LOCAL_LEDGER_ADDRESS, False)
        logging.info("{0}-{1} - Done {2} task".format(self.name, 0, 'Init'))

        dry_run = self.config.get_dry_run()
        total_transactions = self.config.get_total_transaction()
        for index in range(1, total_transactions + 1):
            node_address = self._get_random_node_address(nodes)
            next_task = self._get_next_task(task_types, task_probabilities, all_tasks)
            logging.info(
                "{0}-{1} - Running {2} against {3}".format(self.name, index, next_task.task_name, node_address))
            task_result = next_task.run(index, base_directory, node_address, dry_run)
            task_result.dump()

            if task_result.is_error() and fail_fast:
                logging.info("{0}-{1} - Failed {2} ({3}s)".format(self.name, index, task_result.task_name,
                                                                  task_result.time_elapsed))
                self.stats[task_result.task_name]['failed'] += 1
                self.print_stats()
                return False
            elif task_result.is_error():
                logging.info(
                    "{0}-{1} - Successfully completed {2} ({3}s)".format(self.name, index, task_result.task_name,
                                                                         task_result.time_elapsed))
                self.stats[task_result.task_name]['failed'] += 1
            else:
                logging.info(
                    "{0}-{1} - Successfully completed {2} ({3}s)".format(self.name, index, task_result.task_name,
                                                                         task_result.time_elapsed))
                self.stats[task_result.task_name]['succeeded'] += 1

        logging.info("Manager {0} completed!".format(self.name))
        self.print_stats()
        return True

    @staticmethod
    def _get_random_node_address(nodes: List[str]):
        return random.choice(nodes)

    def _get_next_task(self, task_types: List[str], task_probabilities: List[int], all_tasks: Dict[str, Task]) -> Task:
        return all_tasks[self.r.choices(task_types, task_probabilities).pop()]

    @staticmethod
    def _build_task_with_probabilities(tasks: List[Dict[str, Union[str, int]]]) -> Tuple[List[str], List[int]]:
        task_types = [task['type'] for task in tasks]
        task_probabilities = [task['probability'] for task in tasks]
        return task_types, task_probabilities

    @staticmethod
    def _build_all_tasks(base_directory: str, base_binary: str, seed: int) -> Dict[str, Task]:
        return {
            'VoteProposal': VoteProposal('VoteProposal', base_directory, base_binary, seed),
            'InitProposal': InitProposal('InitProposal', base_directory, base_binary, seed),
            'Withdraw': Withdraw('Withdraw', base_directory, base_binary, seed),
            'Unbond': Unbond('Unbond', base_directory, base_binary, seed),
            'Delegate': Delegate('Delegate', base_directory, base_binary, seed),
            'Faucet': Faucet('Faucet', base_directory, base_binary, seed),
            'Transfer': Transfer('Transfer', base_directory, base_binary, seed),
            'Init': Init('Init', base_directory, base_binary, seed)
        }

    def print_stats(self):
        for task_name in self.stats.keys():
            succeeded = self.stats[task_name]['succeeded']
            failed = self.stats[task_name]['failed']
            print("{} - {} / {}".format(task_name, succeeded, failed))
