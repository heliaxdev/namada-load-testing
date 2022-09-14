from dataclasses import dataclass
from multiprocessing.context import Process
from pathlib import Path
from typing import List

from src.config import Config
from src.manager import Manager
from src.store import connect


@dataclass
class Coordinator:

    @staticmethod
    def run(config: Config, seeds: List[str], base_directory: str, base_binary: str, fail_fast: bool):
        Path("db.db").unlink(missing_ok=True)
        connect()

        managers = [Manager('manager:{}'.format(seed), config, int(seed)) for seed in set(seeds)]
        processes = [Process(target=Coordinator._run_manager, args=(manager, base_directory, base_binary, fail_fast))
                     for manager in managers]

        for p in processes:
            p.start()

        for p in processes:
            p.join()

        print("Done load testing!")

    @staticmethod
    def _run_manager(manager: Manager, base_directory: str, base_binary: str, fail_fast: bool) -> bool:
        return manager.run(base_directory, base_binary, fail_fast)
