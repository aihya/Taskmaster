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
    auto_restart: AutoRestart = AutoRestart.UNEXPECTED
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
        self._parse_properties(properties=properties)
        if not self.cmd:
            raise ValueError(f"Program {self._name} has no cmd attribute")

    def _parse_properties(self, properties: Dict[str, Any]):
        for k, v in properties.items():
            program_attribute = getattr(self, k, None)
            if program_attribute == None or k[0] == "_":
                continue
            value = self._validate_values(k, v)
            if isinstance(value, type(program_attribute)):
                setattr(self, k, value)
            else:
                raise TypeError(
                    f"Invalid type for attribute {k} in TestProgram. Expected {type(program_attribute)}, got {type(k)}"
                )

    def _validate_values(self, name, value):
        if name == "start_time" or name == "stop_time":
            return self._validate_date(value)
        if name == "exit_code":
            return self._validate_exit_code(value)
        if name == "auto_restart":
            return self._validate_auto_restart(value)
        if name == "stop_signal":
            return self._validate_stop_signal(value)
        return value

    def _validate_date(self, value):
        if isinstance(value, str):
            return datetime.datetime.strptime(value, "%H:%M:%S %d-%m-%Y")
        else:
            raise ValueError("Date must be a string in format HH:MM:SS DD-MM-YYYY.")

    def _validate_exit_code(self, value):
        if isinstance(value, int):
            if value >= 0 and value <= 255:
                return value
        raise ValueError("Exit code value should be an intiger between 0 and 255")

    def _validate_auto_restart(self, value):
        return AutoRestart.from_str(value)

    def _validate_stop_signal(self, value):
        return Signals.from_str(value)
