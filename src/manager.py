import os
from dataclasses import dataclass, field
import random
from pathlib import Path
from typing import List, Tuple, Dict, Union

from src.config import Config
from src.constants import LOCAL_LEDGER_ADDRESS
from src.store import connect
from src.task import Task
from src.tasks.faucet import Faucet
from src.tasks.init import Init
from src.tasks.transfer import Transfer


@dataclass
class Manager:
    config: Config
    all_tasks: Dict = field(init=False)

    def __post_init__(self):
        seed = self.config.get_seed()
        random.seed(seed)
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
        for index in range(1, total_transactions):
            node_address = self._get_random_node_address(nodes)
            next_task = self._get_next_task(task_types, task_probabilities, all_tasks)
            task_result = next_task.run(index, base_directory, node_address, dry_run)
            task_result.dump()
            if task_result.is_error() and fail_fast:
                raise Exception("Task {} failed at step {}!".format(next_task.task_name, index))

    @staticmethod
    def _get_random_node_address(nodes: List[str]):
        return random.choice(nodes)

    @staticmethod
    def _get_next_task(task_types: List[str], task_probabilities: List[int], all_tasks: Dict[str, Task]) -> Task:
        return all_tasks[random.choices(task_types, task_probabilities).pop()]

    @staticmethod
    def _build_task_with_probabilities(tasks: List[Dict[str, Union[str, int]]]) -> Tuple[List[str], List[int]]:
        task_types = [task['type'] for task in tasks]
        task_probabilities = [task['probability'] for task in tasks]
        return task_types, task_probabilities

    @staticmethod
    def _build_all_tasks(base_diretory: str, base_binary: str, seed: int) -> Dict[str, Task]:
        return {
            'Faucet': Faucet('Faucet', base_diretory, base_binary, seed),
            'Transfer': Transfer('Transfer', base_diretory, base_binary, seed),
            'Init': Init('Init', base_diretory, base_binary, seed)
        }




