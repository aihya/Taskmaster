import yaml
import os
import sys
from Program import Program

def load_config_file():
    files = sys.argv[1:]

    if len(files) != 1:
        print("Usage: ./taskmaster conf.yaml")
        exit(os.EX_OK)

    programs = []
    try:
        with open(files[0], 'r') as stream:
            programs.append(yaml.safe_load(stream))
    except FileNotFoundError:
        print(f'Configuration file ({files[0]}) not found')
        exit(os.EX_OK)
    except Exception as E:
        print(f'Can\'t parse configuration file ({files[0]}) due to:\n{E}')
        exit(os.EX_OK)

    return programs

class Programs:

    def __init__(self):
        self.programs = []
        self.names = set()

    def load(self):
        configs = load_config_file()
        print(configs)
        for config in configs:
            for name, properties in config.items():
                self.programs.append(Program(name, properties))
                self.names.add(name)

    def reload(self):
        pass

    def status(self):
        for program in self.programs:
            program.status()

    def full_status(self):
        for program in self.programs:
            program.full_status()

    def launch(self):
        for program in self.programs:
            if program.auto_start:
                program.execute()

    def force_kill(self, program):
        program.kill()

    def force_kill_all(self):   
        for program in self.programs:
            program.force_kill()
