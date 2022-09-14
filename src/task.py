import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Tuple, List, Union

from src.commands import WalletCommands, ClientCommands
from src.constants import VALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_EXECUTION_OUTPUT
from src.parser import Parser


@dataclass
class TaskResult:
    task_name: str
    command: str
    stdout: str
    stderr: str
    index: int
    seed: int
    time_elapsed: float = field(init=False)

    def is_error(self):
        return len(self.stderr) > 0

    def serialize(self):
        return {
            'command': self.command,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'task_name': self.task_name,
            'index': self.index,
            'seed': self.seed,
        }

    def set_time_elapsed(self, start_time: float, end_time: Union[float, None]):
        if end_time is None:
            self.time_elapsed = time.time() - start_time
        else:
            self.time_elapsed = end_time - start_time
        return self

    def dump(self):
        folder = 'success' if not self.is_error() else 'failed'
        file_path = 'logs/{}/{}/{}-{}.log'.format(self.seed, folder, self.index, self.task_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        log = self.serialize()
        with open(file_path, "w") as f:
            f.write(json.dumps(log, sort_keys=True, indent=4))


@dataclass
class Task(ABC):
    task_name: str
    base_diretory: str
    base_binary: str
    seed: int
    wallet: WalletCommands = field(init=False)
    client: ClientCommands = field(init=False)
    parser: Parser = field(init=False)

    def __post_init__(self):
        self.wallet = WalletCommands(self.base_binary)
        self.client = ClientCommands(self.base_binary)
        self.parser = Parser()

    def run(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        start_time = time.time()
        return self.handler(step_index, base_directory, ledger_address, dry_run).set_time_elapsed(start_time, None)

    @abstractmethod
    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        raise Exception("Handler must be implemented!")

    def execute_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        process_result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.base_diretory, timeout=timeout)
        if not self._is_tx_valid(process_result):
            return False, process_result.stdout, process_result.stderr
        return True, process_result.stdout, process_result.stderr

    @staticmethod
    def _is_tx_valid(process_result: subprocess.CompletedProcess) -> bool:
        if len(process_result.stderr) > 0:
            return False

        if not any(output in process_result.stdout for output in [VALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_EXECUTION_OUTPUT]) and not any(output in process_result.stderr for output in [VALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_EXECUTION_OUTPUT]):
            return True

        if VALID_TRANSACTION_OUTPUT in process_result.stdout:
            return True
        elif INVALID_TRANSACTION_OUTPUT in process_result.stdout or INVALID_TRANSACTION_OUTPUT in process_result.stderr:
            return False
        elif INVALID_TRANSACTION_EXECUTION_OUTPUT in process_result.stdout or INVALID_TRANSACTION_EXECUTION_OUTPUT in process_result.stderr:
            return False
        else:
            return True

    @staticmethod
    def assert_row_affected(affected_rows: int, expected_affected_rows: int):
        assert(affected_rows == expected_affected_rows)

