from typing import Dict, List, Optional, Any
from enums import Signals, AutoRestart
from process import Process
from log import logger as log
import os


class Program:

    name: str = ""
    count: int = 1
    auto_start: bool = True
    auto_restart: AutoRestart = AutoRestart.UNEXPECTED
    exit_codes: int = [os.EX_OK]
    start_time: int = 0
    retries: int = 0
    stop_signal: Signals = Signals.TERM
    stop_time: int = 0
    cmd: str = ""
    working_dir: Optional[str] = ""
    stdout: str = ""
    stderr: str = ""
    umask: int = 22
    processes: List[Process] = []
    env: Dict[str, str] = {}
    config: Dict[str, any] = {}

    def __init__(self, name: str, properties: Dict[str, Any]):
        self.name = name
        self.processes = []
        self.env = {}
        self.config = properties
        self._parse_properties(properties=properties)
        self.env = self._get_expanded_env()
        if not self.cmd:
            raise ValueError(f"Program {self.name} has no cmd attribute")
        self._create_processes(self.count)

    def _create_processes(self, count):
        procces_list = []
        for _ in range(0, count):
            procces_list.append(Process(self.name, self.cmd))
        self.processes = procces_list

    def _validate_type(self, value, attribute_name, attribute_type):
        if isinstance(value, attribute_type):
            setattr(self, attribute_name, value)
        else:
            raise TypeError(
                f"Invalid type for attribute {attribute_name} in {self.name}. Expected {attribute_type}, got {type(value)}"
            )

    def _parse_properties(self, properties: Dict[str, Any]):
        for k, v in properties.items():
            program_attribute = getattr(self, k, None)
            if program_attribute is None or v is None or k[0] == "_":
                continue
            value = self._validate_values(k, v)
            self._validate_type(value, k, type(program_attribute))

    def _get_expanded_env(self):
        new_env = os.environ
        for k, v in self.env.items():
            new_env.update({k: str(v)})
        return new_env

    def _validate_env(self, value: Dict[str, Any]):
        if not isinstance(value, dict):
            raise ValueError(f"Env variable should be a dictionary, got {type(value)}")
        for k, v in value.items():
            try:
                self.env[k] = str(v)
            except:
                raise ValueError(f"Invalid type for env variable {k}.")
        return self.env

    def _validate_values(self, name, value):
        if name == "exit_code":
            return self._validate_exit_codes(value)
        if name == "auto_restart":
            return self._validate_auto_restart(value)
        if name == "stop_signal":
            return self._validate_stop_signal(value)
        if name == "env":
            return self._validate_env(value)
        if name == "umask":
            value = self._validate_umask(value)
        if isinstance(value, int):
            if value < 0:
                raise ValueError(f"The {name} cannot be negative.")
        return value

    def _validate_umask(self, value):
        if value > 0o777:
            raise ValueError("The umask cannot be greater than 0777.")
        return value

    def _validate_time(self, value):
        try:
            return int(value)
        except:
            raise ValueError(f"Invalid time format, expected int.")

    def _validate_exit_codes(self, values):
        value_list = []
        if not isinstance(values, list):
            raise ValueError("Exit code should be a valid list")
        for value in values:
            if isinstance(value, int):
                if value >= 0 and value <= 255:
                    value_list.append(value)
                    continue
            raise ValueError("Exit code value should be an intiger between 0 and 255")

    def _validate_auto_restart(self, value):
        return AutoRestart.from_str(value)

    def _validate_stop_signal(self, value):
        return Signals.from_str(value)

    def execute_processes(self, processes):
        for process in processes:
            process.set_popen_args(
                stdout=self.stdout,
                stderr=self.stderr,
                env=self.env,
                umask=self.umask,
                workingdir=self.working_dir,
            )
            process.execute()

    def execute(self):
        self.execute_processes(self.processes)

    def status(self):
        if not self.processes:
            return "No processes created."
        r, o, k, l, s = 0, 0, 0, 0, 0
        for process in self.processes:
            if process.launched:
                l += 1
            if process.is_running():
                r += 1
            if process.kill_by_user:
                s += 1
            elif process.exit_status() is not None:
                o = o + 1 if process.exit_status() == 0 else o
                k = k + 1 if process.exit_status() else k
        print(
            f"program: {self.name}\n↳ launched: {l}, running: {r}, success: {o}, failed: {k}, stopped: {s}"
        )
        return len(self.processes)

    def full_status(self):
        if not self.processes:
            return "No processes created."
        self.status()
        for process in self.processes:
            if process.launched:
                print(f"↳ {hex(id(process))} [pid:{process.popen.pid}]", end="")
                if process.is_running():
                    print(f" \033[33mrunning\033[0m ({process.elapsed_time()})", end="")
                elif process.kill_by_user:
                    print(f" \033[34mstopped\033[0m ({process.elapsed_time()})", end="")
                elif process.exit_status() == 0:
                    print(f" \033[32msuccess\033[0m ({process.elapsed_time()})", end="")
                elif process.exit_status():
                    exit_status = process.exit_status()
                    print(
                        f" \033[31mfailed\033[0m [code:{exit_status}] ({process.elapsed_time()})",
                        end="",
                    )
                print()

    def restart(self):
        log.log(f"restart program [{self.name}]")
        for process in self.processes:
            process.restart()

    def kill(self):
        log.log(f"kill program [{self.name}]")
        for process in self.processes:
            process.kill(self.stop_signal)

    def check(self):
        for process in self.processes:
            process.check(
                auto_restart=self.auto_restart,
                stop_time=self.stop_time,
                exit_codes=self.exit_codes,
                start_time=self.start_time,
                retries=self.retries,
            )

    def reload_has_substantive_change(self, new_config):
        return any(
            [
                getattr(self, k, None) is not None
                and (k not in self.config.keys() or self.config[k] != new_config[k])
                for k, _ in new_config.items()
                if k != "count"
            ]
        )

    def assign_count(self, count):
        self._validate_values("count", count)

    def reload(self):
        newps = []
        if len(self.processes) == self.count:
            return
        if len(self.processes) < self.count:
            for _ in range(0, (self.count - len(self.processes))):
                newp = Process(self.name, self.cmd)
                self.processes.append(newp)
                newps.append(newp)
        else:
            del self.processes
            self._create_processes(self.count)
            self.execute()
            return

        if self.auto_start:
            self.execute_processes(newps)
