#from program.Programs import Programs
import threading
import interface
import time
import log
from Programs import Programs

def check_programs(thread_lock, programs):
    """
    This function is responsible for checking
    and updating the status of every program
    and their processes.
    The thread lock is required to control printing
    """
    while True:
        thread_lock.acquire(True)
        for program in programs.programs:
            program.check()
        thread_lock.release()
        time.sleep(0.1)


if __name__ == "__main__":

    lock = threading.Lock()


    # Creates Programs instance for parsing the YAML file and reading the programs.
    programs = Programs()
    programs.load()
    programs.launch()

    # Thread responsible for checking the state of the programs
    daemon = threading.Thread(target=check_programs, args=(lock, programs), daemon=True)
    daemon.start()

    interface.Interface(programs, lock).cmdloop()
