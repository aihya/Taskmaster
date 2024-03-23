import os
from typing import Dict, List, Optional, Any
from enums import Signals, AutoRestart
import subprocess

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

    _name:str = None
    count:int = 1
    auto_start:bool = True
    autorestart: AutoRestart = AutoRestart.UNEXPECTED
    exit_code = os.EX_OK
    start_time = None
    max_retry = 0
    stop_signal = Signals.TERM
    stop_time = None
    cmd = None
    working_dir = None
    stdout = None
    stderr = None
    umask = 22
    _processes: Optional[Process] = None

    def __init__(self, process_name: str, properties: Dict[str, Any]):
		
        self._name = process_name
        for k, v in properties.items():
            if k in self.__dict__.keys() and isinstance(type(k)):
                setattr(self, k, v)
        if not self.cmd:
            raise ValueError(f"Program {self._name} has no cmd attribute")
