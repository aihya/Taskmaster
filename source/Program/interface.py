import cmd
import log


class Interface(cmd.Cmd):

    prompt = "\033[1;32mTaskmaster > \033[0m"

    def __init__(self, programs, lock):
        self.lock = lock
        self.programs = programs
        super().__init__()

    def do_EOF(self, args):
        return True

    def do_exit(self, args):
        return True

    def do_start(self, args):
        """
        Start a program from the collection of programs
        loaded using the configuration file.

        Example: start nginx
        """
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
                log.log(f"stop {program.name}")
                program.kill()
        self.lock.release()

    def do_status(self, args):
        self.lock.acquire(True)
        log.log(f"status {args}")

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
                print()
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
                    log.log(f"full_status: [program:{args[1]}]")
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
            print(f"full_restart don't take any arguments")
        else:
            for program in self.programs.programs():
                program.kill()
                program.execute()
        self.lock.release()

    def do_reload(self, args):
        try:
            self.lock.acquire(True)
            self.programs.reload()
            self.lock.release()
        except Exception as e:
            print(f"\033[33mWarning:\033[0m error reloading ({str(e)})")

    def do_log(self, args):
        self.lock.acquire(True)
        try:
            with open("./log.txt", "r") as log_file:
                line = log_file.readline()
                while line:
                    print(line, end="")
                    line = log_file.readline()
        except FileNotFoundError:
            raise (f"Warning: Log file not found.")
        self.lock.release()

    def emptyline(self):
        pass
