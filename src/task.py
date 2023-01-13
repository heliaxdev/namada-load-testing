import json
import os
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Tuple, List

from src.commands import WalletCommands, ClientCommands
from src.constants import (
    VALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_OUTPUT, 
    INVALID_TRANSACTION_EXECUTION_OUTPUT, NOT_ENOUGH_BALANCE, SKIPPING_KEY
)
from src.output_parser import Parser
import logging


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
        if len(self.stderr) > 0:
            #Shows up as an error but isnt a failed tx
            if NOT_ENOUGH_BALANCE in self.stderr:
                return False
            #Temporary bug
            elif SKIPPING_KEY in self.stderr:
                return False
            else:
                return True

    def serialize(self):
        return {
            'command': self.command,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'task_name': self.task_name,
            'index': self.index,
            'seed': self.seed,
        }

    def set_time_elapsed(self, start_time: float):
        self.time_elapsed = round(time.time() - start_time, 2)
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
        return self.handler(step_index, base_directory, ledger_address, dry_run).set_time_elapsed(start_time)

    @abstractmethod
    def handler(self, step_index: int, base_directory: str, ledger_address: str, dry_run: bool) -> TaskResult:
        raise Exception("Handler must be implemented!")

    def execute_command(self, command: List[str], timeout: int = 130) -> Tuple[bool, str, str]:
        # If a command fails due to a timeout error, it may be because the ledger is prompting it to replace already existing keys
        # To resolve this, try a different set of seeds, or clear the wallet
        process_result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                        cwd=self.base_diretory, timeout=timeout)
        if not self._is_tx_valid(process_result):
            return False, process_result.stdout, process_result.stderr
        return True, process_result.stdout, process_result.stderr

    @staticmethod
    def _is_tx_valid(process_result: subprocess.CompletedProcess) -> bool:
        if len(process_result.stderr) > 0:
            if NOT_ENOUGH_BALANCE in process_result.stderr:
                pass
            #Temporary bug
            elif SKIPPING_KEY in process_result.stderr:
                pass
            else:
                logging.debug('failed because stderr is present that isnt not enough gas')
                return False

        if not any(output in process_result.stdout for output in [VALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_OUTPUT,
                                                                  INVALID_TRANSACTION_EXECUTION_OUTPUT]) and not any(
                output in process_result.stderr for output in
                [VALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_OUTPUT, INVALID_TRANSACTION_EXECUTION_OUTPUT]):
            return True

        if VALID_TRANSACTION_OUTPUT in process_result.stdout:
            return True
        elif INVALID_TRANSACTION_OUTPUT in process_result.stdout or INVALID_TRANSACTION_OUTPUT in process_result.stderr:
            logging.debug('failed bacuase of 96')
            return False
        elif INVALID_TRANSACTION_EXECUTION_OUTPUT in process_result.stdout or INVALID_TRANSACTION_EXECUTION_OUTPUT in process_result.stderr:
            logging.debug('failed because of 98')
            return False
        else:
            return True

    @staticmethod
    def assert_row_affected(affected_rows: int, expected_affected_rows: int):
        assert (affected_rows == expected_affected_rows)
