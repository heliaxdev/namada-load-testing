import logging
import os
from dataclasses import dataclass, field
import random
from pathlib import Path
from shutil import rmtree
from typing import List, Tuple, Dict, Union

from src.config import Config
from src.constants import LOCAL_LEDGER_ADDRESS
from src.store import connect
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
    config: Config
    all_tasks: Dict = field(init=False)
    stats: Dict = field(init=False)
    random: random.Random = field(init=False)

    def __post_init__(self):
        tasks = self.config.get_tasks()
        self.stats = {task_name: {'succeeded': 0, 'failed': 0} for task_name in [task['type'] for task in tasks]}

        seed = self.config.get_seed()
        self.random = random.Random(seed)
        random.seed(seed)

        rmtree("logs/{}".format(seed), ignore_errors=True)

        Path("db.db").unlink(missing_ok=True)
        connect()

    def run(self, base_directory: str, base_binary: str, fail_fast: bool):
        nodes = self.config.get_nodes()
        tasks = self.config.get_tasks()
        seed = self.config.get_seed()

        all_tasks = self._build_all_tasks(base_directory, base_binary, seed)
        task_types, task_probabilities = self._build_task_with_probabilities(tasks)

        # run the init task once
        all_tasks['Init'].run(0, base_directory, LOCAL_LEDGER_ADDRESS, False)

        dry_run = self.config.get_dry_run()
        total_transactions = self.config.get_total_transaction()
        for index in range(1, total_transactions + 1):
            node_address = self._get_random_node_address(nodes)
            next_task = self._get_next_task(task_types, task_probabilities, all_tasks)
            logging.info("{} - Running {} against {}".format(index, next_task.task_name, node_address))
            task_result = next_task.run(index, base_directory, node_address, dry_run)
            task_result.dump()

            if task_result.is_error() and fail_fast:
                logging.info("{0} - Failed {1} ({2}s)".format(index, task_result.task_name, task_result.time_elapsed))
                self.stats[task_result.task_name]['failed'] += 1
                self.print_stats()
                exit(1)
            elif task_result.is_error():
                logging.info("{0} - Successfully completed {1} ({2}s)".format(index, task_result.task_name, task_result.time_elapsed))
                self.stats[task_result.task_name]['failed'] += 1
            else:
                logging.info("{0} - Successfully completed {1} ({2}s)".format(index, task_result.task_name, task_result.time_elapsed))
                self.stats[task_result.task_name]['succeeded'] += 1

        logging.info("Load testing completed!")
        self.print_stats()

    @staticmethod
    def _get_random_node_address(nodes: List[str]):
        return random.choice(nodes)

    def _get_next_task(self, task_types: List[str], task_probabilities: List[int], all_tasks: Dict[str, Task]) -> Task:
        return all_tasks[self.random.choices(task_types, task_probabilities).pop()]

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




