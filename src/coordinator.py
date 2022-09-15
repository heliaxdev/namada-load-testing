import json
import logging
from dataclasses import dataclass, field
from multiprocessing.context import Process
from multiprocessing import Queue
from pathlib import Path
from typing import List, Dict

from src.config import Config
from src.manager import Manager, ManagerResult
from src.store import connect


@dataclass
class Coordinator:

    @staticmethod
    def run(config: Config, seeds: List[str], base_directory: str, base_binary: str, fail_fast: bool, json_output: bool):
        Path("db.db").unlink(missing_ok=True)
        connect()

        q = Queue()
        managers = [Manager('manager:{}'.format(seed), config, int(seed)) for seed in set(seeds)]
        processes = [Process(target=Coordinator._run_manager, args=(manager, base_directory, fail_fast, q))
                     for manager in managers]

        for manager in managers:
            manager.run_init_task(base_directory, base_binary)

        logging.info("coordinator - Starting load testing with {}".format(', '.join(seeds)))

        for p in processes:
            p.start()

        for p in processes:
            p.join()

        logging.info("coordinator - Done load testing!")

        Coordinator._dump_stats(q, json_output)

    @staticmethod
    def _run_manager(manager: Manager, base_directory: str, fail_fast: bool, queue: Queue):
        result = manager.run(base_directory, fail_fast)
        queue.put(result)

    @staticmethod
    def _dump_stats(queue: Queue, json_output):
        while not queue.empty():
            result: ManagerResult = queue.get()
            if json_output:
                json_result = result.to_json()
                with open('result_{}.json'.format(json_result['seed']), "w") as f:
                    f.write(json.dumps(json_result, sort_keys=True, indent=4))
            else:
                result.print()
                print("---------------------------")

