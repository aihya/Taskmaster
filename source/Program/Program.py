import os
from typing import Dict, List, Optional, Any
from source.enums import Signals, AutoRestart
import subprocess
import datetime


class Process:
    _retry_count: int = 0
    _process_name: str
    _processes: list = []

    def __init__(self, process_name, retry_count):
        self._retry_count = retry_count
        self._process_name = process_name

    def open(self, command, copies):
        for _ in range(0, copies):
            process = subprocess.Popen(command)
            self._processes.append(process)

    def close(self):
        for process in self._processes:
            if process.poll() is None:
                process.terminate()


class Program:

    _name: str = ""
    _processes: Optional[Process] = None

    count: int = 1
    auto_start: bool = True
    autorestart: AutoRestart = AutoRestart.UNEXPECTED
    exit_code: int = os.EX_OK
    start_time: datetime.datetime = datetime.datetime.now()
    max_retry: int = 0
    stop_signal: Signals = Signals.TERM
    stop_time: datetime.datetime = datetime.datetime.now()
    cmd: str = ""
    working_dir: Optional[str] = ""
    stdout: str = ""
    stderr: str = ""
    umask: int = 22

    def __init__(self, process_name: str, properties: Dict[str, Any]):
        self._name = process_name
        for k, v in properties.items():
            program_attribute = getattr(self, k, None)
            if program_attribute == None or k[0] == "_":
                continue
            if isinstance(v, type(program_attribute)):
                setattr(self, k, v)
            else:
                raise TypeError(
                    f"Invalid type for attribute {k} in TestProgram. Expected {type(program_attribute)}, got {type(k)}"
                )
        if not self.cmd:
            raise ValueError(f"Program {self._name} has no cmd attribute")


if __name__ == "__init__":
    Program("hehe", {"cmd": "hehe"})
