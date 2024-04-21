import os
import signal
from typing import Dict, List, Optional, Any
from enums import Signals, AutoRestart
import subprocess
import datetime
import log

# import atexit -> define function to be executed at exit point.


class Process:

    def __init__(self, name, command):
        self.command = command
        self.name = name
        self.retries = 0
        self.popen = None
        self.launched = False
        self.start_time = 0
        self.end_time = None
        self.kill_by_user = False

    def is_running(self):
        if self.popen:
            return True if self.popen.poll() == None else False
        return False

    def set_popen_args(self, stdout, stderr, env, workingdir, umask):
        self.stdout = stdout
        self.stderr = stderr
        self.env = env
        self.cwd = workingdir
        self.umask = umask

    def execute(self):
        if self.is_running():
            log.log(f"cannot start an already running process [pid:{self.popen.pid}]")
            return
        try:
            self.kill_by_user = False
            self.popen = subprocess.Popen(self.command, shell=True)
            if self.is_running():
                self.launched = True
                self.start_time = datetime.datetime.now()
                self.end_time = None
                log.log(
                    f"execute({self.command})[pid:{self.popen.pid}][status:{self.popen.poll()}]"
                )
        except Exception as E:
            self.popen = None
            log.log(f"[{self.name}] execution failed: {E}")

    def exit_status(self):
        if self.launched:
            return self.popen.poll()
        return None

    def elapsed_time(self):
        """Represents the process's time to live"""
        if self.launched:
            if self.is_running():
                return datetime.datetime.now() - self.start_time
            return self.end_time - self.start_time
        return self.end_time - self.start_time

    def check(self, auto_restart, stop_time, exit_codes):
        if self.launched:
            if self.exit_status() != None and self.end_time == None:
                self.end_time = datetime.datetime.now()

        # Force kill if stop time is passed or max retries are consumed.
        self.ensure_force_kill(stop_time)
        self.ensure_restart(auto_restart, exit_codes)

    def ensure_restart(self, auto_restart, exit_codes):
        if auto_restart == AutoRestart.NEVER or self.kill_by_user:
            return
        if auto_restart == AutoRestart.UNEXPECTED and self.exit_status() in exit_codes:
            return
        self.execute()

    def ensure_force_kill(self, stop_time):
        if self.popen == None:
            return
        if self.end_time:
            time_diff = datetime.datetime.now() - self.end_time
            if time_diff >= datetime.timedelta(seconds=stop_time):
                log.log(f"force kill process: [pid:{self.popen.pid}]")
                self.popen.kill()

    def kill(self, stop_signal):
        self.kill_by_user = True
        if self.is_running():
            log.log(f"kill process [pid:{self.popen.pid}]")
            os.kill(self.popen.pid, stop_signal)
            self.end_time = datetime.datetime.now()
            return True
        else:
            return False

    def restart(self):
        if self.kill(signal.SIGKILL) or self.launched:
            self.execute()


class Program:

    name: str = ""

    count: int = 1
    auto_start: bool = True
    auto_restart: AutoRestart = AutoRestart.UNEXPECTED
    exit_codes: int = [os.EX_OK]
    start_time: int = 0
    max_retry: int = 0
    stop_signal: Signals = Signals.TERM
    stop_time: int = 0
    cmd: str = ""
    working_dir: Optional[str] = ""
    stdout: str = ""
    stderr: str = ""
    umask: int = 22

    def __init__(self, name: str, properties: Dict[str, Any]):
        print(f"Creating program: {name}")
        self.name = name
        self._parse_properties(properties=properties)
        if not self.cmd:
            raise ValueError(f"Program {self.name} has no cmd attribute")
        self.processes = []
        for _ in range(self.count):
            self.processes.append(Process(self.name, self.cmd))
        print(f"Created program: {name} {len(self.processes)}")

    def _parse_properties(self, properties: Dict[str, Any]):
        for k, v in properties.items():
            program_attribute = getattr(self, k, None)
            if program_attribute == None or k[0] == "_":
                continue
            # setattr(self, k, v)
            value = self._validate_values(k, v)
            if isinstance(value, type(program_attribute)):
                setattr(self, k, value)
            else:
                raise TypeError(
                    f"Invalid type for attribute {k} in {self.name}. Expected {type(program_attribute)}, got {type(k)}"
                )

    def _validate_values(self, name, value):
        if name == "start_time" or name == "stop_time":
            return self._validate_time(value)
        if name == "exit_code":
            return self._validate_exit_codes(value)
        if name == "auto_restart":
            return self._validate_auto_restart(value)
        if name == "stop_signal":
            return self._validate_stop_signal(value)
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

    def execute(self):
        log.log(f"execute program: {self.name}")
        for process in self.processes:
            process.execute()

    def status(self):
        if not self.processes:
            return "No processes created."
        r, o, k, l = 0, 0, 0, 0
        for process in self.processes:
            if process.launched:
                l += 1
            if process.is_running():
                r += 1
            if process.exit_status() is not None:
                o = o + 1 if process.exit_status() == 0 else o
                k = k + 1 if process.exit_status() else k
        print(
            f"program: {self.name}\n↳ launched: {l}, running: {r}, success: {o}, failed: {k}"
        )
        return len(self.processes)

    def full_status(self):
        if not self.processes:
            return "No processes created."
        self.status()
        for process in self.processes:
            if process.launched:
                print(
                    f"↳ {hex(id(process))}[pid:{process.popen.pid}]", end=""
                )  # Print life spane of the process
                if process.is_running():
                    print(f" \033[33mrunning\033[0m ({process.elapsed_time()})", end="")
                elif process.exit_status() == 0:
                    print(f" \033[32msuccess\033[0m ({process.elapsed_time()})", end="")
                elif process.exit_status():
                    exit_status = process.exit_status()
                    string = str(signal.Signals(abs(exit_status))).split(".")[-1]
                    print(
                        f" \033[31mfailed\033[0m [code:{exit_status}({string})] ({process.elapsed_time()})",
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
            process.check(self.auto_restart, self.stop_time, self.exit_codes)
            # process.check(self.auto_restart, self.exit_code, self.max_retries, self.start_time, self.stop_time)
