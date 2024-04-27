# from program.Programs import Programs
import os
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
        for program in programs.programs():
            program.check()
        thread_lock.release()
        time.sleep(0.1)


if __name__ == "__main__":

    lock = threading.Lock()
    try:
        programs = Programs()
        programs.load()
        programs.launch()
        interface.Interface(programs, lock).cmdloop()
    except Exception as e:
        print(f"\033[31m Error:\033[0m {str(e)}")
        exit(os.EX_OK)
    daemon = threading.Thread(target=check_programs, args=(lock, programs), daemon=True)
    daemon.start()
