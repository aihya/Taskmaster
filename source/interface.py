import cmd
import signal
from log import logger as log
import subprocess


class Interface(cmd.Cmd):

    prompt = "\033[1;32mTaskmaster > \033[0m"

    def __init__(self, programs, lock):
        self.lock = lock
        self.programs = programs
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGHUP, self.sighup_handler)
        super().__init__()

    def sigint_handler(self, signal, frame):
        log.log("stopping taskmaster")
        exit(0)

    def sighup_handler(self, signal, frame):
        self.do_reload(None)

    def do_shell(self, args):
        try:
            completed_process = subprocess.run(args, shell=True, check=True, stdin=subprocess.DEVNULL)
            output = completed_process.stdout.decode().strip()
            print(output)
        except Exception as e:
            pass

    def do_EOF(self, args):
        return True

    def do_exit(self, args):
        return True

    def do_start(self, args):
        self.lock.acquire(True)
        for arg in args.split():
            if arg in self.programs.programs_dict:
                program = self.programs.programs_dict[arg]
                log.log(f"start {program.name}")
                program.execute()
        self.lock.release()

    def do_stop(self, args):
        self.lock.acquire(True)
        for arg in args.split():
            if arg in self.programs.programs_dict:
                program = self.programs.programs_dict[arg]
                program.kill()
                log.log(f"stop {program.name}")
        self.lock.release()

    def do_status(self, args):
        self.lock.acquire(True)

        if args:
            found = {}
            extra = []
            for arg in args.split():
                for program in self.programs.programs():
                    if program.name == arg and arg not in found.keys():
                        found[program.name] = program
                        break
                if arg not in found.keys():
                    extra.append(arg)
            if found:
                for name in found:
                    found[name].status()
            if extra:
                print(f'\033[33mprograms not found: {" ".join(set(extra))}\033[0m')
        else:
            self.programs.status()

        self.lock.release()

    def do_full_status(self, args):
        self.lock.acquire(True)
        if args:
            for arg in args.split():
                if arg in self.programs.programs_dict:
                    program = self.programs.programs_dict[arg]
                    program.full_status()
        else:
            self.programs.full_status()
        self.lock.release()

    def do_restart(self, args):
        if not args:
            return
        self.lock.acquire(True)
        for arg in args.split():
            if arg in self.programs.programs_dict:
                program = self.programs.programs_dict[arg]
                program.restart()
                log.log(f"restart: [{program.name}]")
        self.lock.release()

    def do_full_restart(self, args):
        self.lock.acquire(True)
        if args:
            print(f"\033[33mWarning:\033[0m full_restart don't take any arguments")
        else:
            for program in self.programs.programs():
                program.kill()
                program.execute()
        self.lock.release()

    def do_reload(self, args):
        try:
            self.lock.acquire(True)
            self.programs.reload()
        except Exception as e:
            print(f"\033[33mWarning:\033[0m error reloading ({str(e)})")
        self.lock.release()

    def emptyline(self):
        pass
