import time
from enums import AutoRestart
from log import logger as log
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

    def demote(self, user_uid, user_gid):
        def result():
            os.setgid(user_gid)
            os.setuid(user_uid)

        return result

    def set_popen_args(self, stdout, stderr, env, workingdir, umask, uid, gid):
        self.stdout = stdout
        self.stderr = stderr
        self.env = env
        self.cwd = workingdir
        self.umask = umask
        self.uid = uid
        self.gid = gid

    def open_standard_files(self, file_name):
        if not file_name:
            return None
        try:
            return open(file_name, "a")
        except Exception as e:
            print(
                f"\033[33mWarning:\033[0m Standard file for {self.name} can't be opened because {e}."
            )
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
                stdin=open("/dev/null", 'w'),
                umask=self.umask,
                env=self.env,
                cwd=self.cwd,
                preexec_fn=self.demote(self.uid, self.gid),
            )
            if self.is_running():
                self.launched = True
                self.end = None
                log.log(f"execute({self.command})[pid:{self.popen.pid}]")
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
                if self.exit_status() not in exit_codes:
                    log.log(
                        f"process[pid:{self.popen.pid}] stopped unexpectedly [code:{self.exit_status()}]"
                    )
        if self.exit_status() is not None:
            self.ensure_restart(auto_restart, exit_codes, retries, start_time)
        else:
            self.ensure_force_kill(stop_time)

    def lived_enough(self, start_time):
        if not self.start or not self.end or not start_time:
            return True
        td = datetime.timedelta(seconds=start_time)
        if self.end - self.start <= td:
            return False
        return True

    def ensure_restart(self, auto_restart, exit_codes, retries, start_time):
        if (
            auto_restart == AutoRestart.NEVER
            or self.kill_by_user
            or self.retries > retries
        ):
            return
        if (
            auto_restart == AutoRestart.UNEXPECTED
            and self.exit_status() in exit_codes
            and self.lived_enough(start_time)
        ):
            return
        es = self.exit_status()
        if (es is not None and es not in exit_codes) or not self.lived_enough(start_time):
            self.retries += 1
            if self.retries > retries:
                log.log(f"max retries reached [pid:{self.popen.pid}]")
                return
        self.execute()

    def ensure_force_kill(self, stop_time):
        if self.popen == None:
            return
        if self.end:
            time_diff = datetime.datetime.now() - self.end
            if time_diff >= datetime.timedelta(seconds=stop_time):
                self.popen.kill()

    def kill(self, stop_signal, killed_by_user=True):
        self.kill_by_user = killed_by_user
        if self.is_running():
            os.kill(self.popen.pid, stop_signal)
            while self.popen.poll() == None:
                time.sleep(0.01)
            self.end = datetime.datetime.now()

    def restart(self):
        log.log(f"restart process [{self.name}]")
        self.kill(signal.SIGKILL, False)
        self.retries = 0
        self.execute()
