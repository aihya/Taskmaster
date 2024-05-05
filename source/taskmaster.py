import os
import threading
import interface
import time
from programsManager import ProgramsManager


def check_programs(thread_lock, programs):
    while True:
        thread_lock.acquire(True)
        for program in programs.programs():
            program.check()
        thread_lock.release()
        time.sleep(0.1)


if __name__ == "__main__":

    lock = threading.Lock()
    try:
        programs = ProgramsManager()
        programs.load()
        programs.launch()
        daemon = threading.Thread(target=check_programs, args=(lock, programs), daemon=True)
        daemon.start()
        interface.Interface(programs, lock).cmdloop()
    except Exception as e:
        print(f"\033[31m Error:\033[0m {str(e)}")
        exit(os.EX_OK)
