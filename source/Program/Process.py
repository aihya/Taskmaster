import os
import subprocess
import datetime


class Process:
    def __init__(self, name, cmd, start_date, end_date):
        self.name = name
        self.cmd = cmd
        self.nb_start_retries = 0
        self.popen = None
        self.kill_by_user = False
        self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        self.starttime = None
        self.closetime = None

    def open_standard_files(self, file_name):
        if file_name is None:
            return None
        try:
            return open(file_name, "a")
        except Exception as e:
            print(f"Standard file for {self.name} can't be opened because {e}.")
            return None

    def execute(self):
        self.nb_start_retries += 1
        try:
            stdoutf = self.open_standard_files(self.stdout)
            stderrf = self.open_standard_files(self.stderr)
            self.cmd = self.umask + self.cmd
            self.popen = subprocess.Popen(
                self.cmd,
                stdout=stdoutf,
                stderr=stderrf,
                env=self.env,
                shell=True,
                cwd=self.workingdir,
            )
            self.starttime = datetime.datetime.now()
            self.closetime = None
        except Exception as e:
            print(f"Can't launch process {self.name} because {e}.")

    def return_code_is_allowed(self, rc, exitcodes):
        if not isinstance(exitcodes, list):
            return rc == exitcodes
        return rc in exitcodes

    def lived_enough(self, starttime):
        if not starttime or not self.starttime or not self.closetime:
            return True
        td = datetime.timedelta(seconds=starttime)
        return (self.closetime - self.starttime) <= td

    def restart_if_needed(self, autorestart, exitcodes, startretries):
        if self.nb_start_retries > startretries or self.kill_by_user:
            return False
        if autorestart == AutoRestartEnum.never or startretries < 1:
            return
        if (
            autorestart == AutoRestartEnum.unexpected
            and self.return_code_is_allowed(self.popen.poll(), exitcodes)
            and self.lived_enough(starttime)
        ):
            return False
        self.execute()

    def force_kill_if_needed(self, stoptime):
        if (
            not self.popen
            or not self.closetime
            or not Process.check_pid_is_alive(self.popen.pid)
            or not stoptime
        ):
            return
        diff = datetime.datetime.now() - self.closetime
        if diff > datetime.timedelta(seconds=stoptime):
            print(f"Forced kill of process for program {self.name}")
            os.kill(self.popen.pid, 9)

    def check(self, autorestart, exitcodes, startretries, starttime, stoptime):
        if not self.popen:
            return False
        rv = self.popen.poll()
        self.force_kill_if_needed(stoptime)
        if rv is not None:
            if not self.closetime:
                self.closetime = datetime.datetime.now()
                print(f"Process in program {self.name} has stopped, return code: {rv}")
            self.restart_if_needed(autorestart, exitcodes, startretries)

    @staticmethod
    def check_pid_is_alive(pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def kill(self, stopsignal):
        self.kill_by_user = True
        if self.popen and not self.popen.poll():
            if Process.check_pid_is_alive(self.popen.pid):
                os.kill(self.popen.pid, stopsignal)
                print(f"Process in program {self.name} has been killed")
                self.closetime = datetime.datetime.now()

    def update_status(self, exitcodes):
        if not self.popen:
            return ProcessStatus.NOT_LAUNCH
        if self.popen.poll() is None:
            return ProcessStatus.RUNNING
        if self.return_code_is_allowed(self.popen.poll(), exitcodes):
            return ProcessStatus.STOP_OK
        else:
            return ProcessStatus.STOP_KO
