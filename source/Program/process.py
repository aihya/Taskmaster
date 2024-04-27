from enums import AutoRestart
import log
import subprocess
import datetime
import signal
import os

class Process:

    def __init__(self, name, command):
        self.command = command
        self.name = name
        self.retries = 0
        self.popen = None
        self.launched = False
        self.start = 0
        self.end = None
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
            self.kill_by_user = False
            self.start = self.end = datetime.datetime.now()
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
                self.end = None
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
        if self.launched and self.is_running():
            return datetime.datetime.now() - self.start
        return self.end - self.start

    def check(self, auto_restart, stop_time, exit_codes, start_time, retries):
        if self.launched:
            if self.exit_status() != None and self.end == None:
                self.end = datetime.datetime.now()
        if self.exit_status() is not None:
            self.ensure_restart(auto_restart, exit_codes, retries, start_time)
        else:
            self.ensure_force_kill(stop_time)

    def lived_enough(self, start_time):
        if not self.start or not self.end or not start_time:
            return True
        td = datetime.timedelta(seconds = start_time)
        if self.end - self.start <= td:
            return False
        return True

    def ensure_restart(self, auto_restart, exit_codes, retries, start_time):
        if (
            auto_restart == AutoRestart.NEVER
            or self.retries > retries
            or self.kill_by_user
        ):
            return
        if auto_restart == AutoRestart.UNEXPECTED and self.exit_status() in exit_codes and self.lived_enough(start_time):
            return
        if self.exit_status() not in exit_codes:
            self.retries += 1
        self.execute()

    def ensure_force_kill(self, stop_time):
        if self.popen == None:
            return
        if self.end:
            time_diff = datetime.datetime.now() - self.end
            if time_diff >= datetime.timedelta(seconds=stop_time):
                log.log(f"force kill process: [pid:{self.popen.pid}]")
                self.popen.kill()

    def kill(self, stop_signal, killed_by_user=True):
        self.kill_by_user = killed_by_user
        if self.is_running():
            log.log(f"kill process [pid:{self.popen.pid}]")
            os.kill(self.popen.pid, stop_signal)
            self.end = datetime.datetime.now()

    def restart(self):
        self.kill(signal.SIGKILL, False)
        self.retries = 0
        self.execute()
