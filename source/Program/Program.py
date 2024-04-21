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

    def open_standard_files(self, file_name):
        if not file_name:
            return None
        try:
            return open(file_name, "a")
        except Exception as e:
            print(f"Standard file for {self.name} can't be opened because {e}.")
            return None

    def execute(self):
        if self.is_running():
            log.log(f"cannot start an already running process [pid:{self.popen.pid}]")
            return
        try:
            stdoutf = self.open_standard_files(self.stdout)
            stderrf = self.open_standard_files(self.stderr)
            print(stdoutf, stderrf)
            self.kill_by_user = False
            self.retries += 1
            self.popen = subprocess.Popen(
                self.command,
                shell=True,
                stdout=stdoutf,
                stderr=stderrf,
                umask=self.umask,
                env=self.env,
                cwd=self.cwd,
            )
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

    def check(self, auto_restart, stop_time, exit_codes, starttime, retries):
        if self.launched:
            if self.exit_status() != None and self.end_time == None:
                self.end_time = datetime.datetime.now()

        # Force kill if stop time is passed or max retries are consumed.
        self.ensure_force_kill(stop_time)
        self.ensure_restart(auto_restart, exit_codes, retries)

    def ensure_restart(self, auto_restart, exit_codes, retries):
        if (
            auto_restart == AutoRestart.NEVER
            or self.retries > retries
            or self.kill_by_user
        ):
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

    def __init__(self, name: str, properties: Dict[str, Any]):
        print(f"Creating program: {name}")
        self.name = name
        self.processes = []
        self.env = {}
        self._parse_properties(properties=properties)
        if not self.cmd:
            raise ValueError(f"Program {self.name} has no cmd attribute")
        for _ in range(self.count):
            self.processes.append(Process(self.name, self.cmd))
        print(f"Created program: {name} {len(self.processes)}")

    def _parse_properties(self, properties: Dict[str, Any]):
        for k, v in properties.items():
            program_attribute = getattr(self, k, None)
            if program_attribute is None or v is None or k[0] == "_":
                continue
            value = self._validate_values(k, v)
            if isinstance(value, type(program_attribute)):
                setattr(self, k, value)
            else:
                raise TypeError(
                    f"Invalid type for attribute {k} in {self.name}. Expected {type(program_attribute)}, got {type(k)}"
                )

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
        if name == "start_time" or name == "stop_time":
            return self._validate_time(value)
        if name == "exit_code":
            return self._validate_exit_codes(value)
        if name == "auto_restart":
            return self._validate_auto_restart(value)
        if name == "stop_signal":
            return self._validate_stop_signal(value)
        if name == "env":
            return self._validate_env(value)
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
        execute_env = self._get_expanded_env()
        print(self.name, self.env)
        for process in self.processes:
            process.set_popen_args(
                stdout=self.stdout,
                stderr=self.stderr,
                env=execute_env,
                umask=self.umask,
                workingdir=self.working_dir,
            )
            process.execute()

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
                print(
                    f"↳ {hex(id(process))}[pid:{process.popen.pid}]", end=""
                )  # Print life spane of the process
                if process.is_running():
                    print(f" \033[33mrunning\033[0m ({process.elapsed_time()})", end="")
                elif process.exit_status() == 0:
                    print(f" \033[32msuccess\033[0m ({process.elapsed_time()})", end="")
                elif process.kill_by_user:
                    print(f" \033[34mstopped\033[0m ({process.elapsed_time()})", end="")
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
                starttime=self.start_time,
                retries=self.retries,
            )

    def reload_has_substantive_change(self, nprog):
        if self.cmd != nprog.cmd or \
				self.stdout != nprog.stdout or \
				self.stderr != nprog.stderr or \
				self.env != nprog.env or \
				self.working_dir != nprog.working_dir or \
				self.umask != nprog.umask or \
                self.auto_start != nprog.auto_start or \
                self.auto_restart != nprog.auto_restart or \
                self.stop_time != nprog.stop_time or \
                self.stop_signal != nprog.stop_signal or \
                self.start_time != nprog.start_time or \
                self.retries != nprog.retries or \
                self.exit_codes != nprog.exit_codes:
            return True
        return False

    def assign_count(self, count):
        if isinstance(count, type(self.count)):
            print(f'new count for {self.name}:{count}')
            self.count = count
            print(self.count)

    def reload(self):
        newps = []
        if len(self.processes) < self.count:
            for x in range(0, (self.count - len(self.processes))):
                newp = Process(self.name, self.cmd)
                self.processes.append(newp)
                newps.append(newp)
        if self.auto_start:
            for prog in newps:
                prog.execute()
