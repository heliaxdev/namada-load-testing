import json
import logging
from dataclasses import dataclass, field
from multiprocessing import Queue
from pathlib import Path
from threading import Thread
from time import sleep
from typing import List

import requests

from src.config import Config
from src.constants import STATUS_ENDPOINT
from src.manager import Manager, ManagerResult
from src.store import connect


@dataclass
class Coordinator:

    @staticmethod
    def run(config: Config, seeds: List[str], nodes: List[str], base_directory: str, base_binary: str, fail_fast: bool, json_output: bool):
        Path("db.db").unlink(missing_ok=True)
        connect()

        q = Queue()
        managers = [Manager('manager:{}'.format(seed), config, int(seed)) for seed in set(seeds)]
        threads = [Thread(target=Coordinator._run_manager, args=(manager, base_directory, nodes, fail_fast, q))
                     for manager in managers]

        # waiting for node to be synched
        waiting_sync_node = [True for _ in nodes]
        while any(waiting_sync_node):
            for index, node in enumerate(nodes):
                node_status = requests.get("http://{}/{}".format(node, STATUS_ENDPOINT), timeout=5)
                body = node_status.json()
                if 'result' in body:
                    is_synched = node_status.json()['result']['sync_info']['catching_up']
                else:
                    is_synched = node_status.json()['sync_info']['catching_up']
                logging.info("Node {} is caught up: {}".format(node, not is_synched))
                waiting_sync_node[index] = is_synched
            sleep(3)

        for manager in managers:
            manager.run_init_task(base_directory, base_binary, nodes)

        logging.info("coordinator - Starting load testing with {}...".format(', '.join(seeds)))

        for p in threads:
            p.start()

        for p in threads:
            p.join()

        logging.info("coordinator - Done load testing!")

        Coordinator._dump_stats(q, json_output)

    @staticmethod
    def _run_manager(manager: Manager, base_directory: str, nodes: List[str], fail_fast: bool, queue: Queue):
        result = manager.run(base_directory, nodes, fail_fast)
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

