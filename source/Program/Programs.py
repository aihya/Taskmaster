import yaml
import os
import sys
from Program import Program

def load_config_file():
    files = sys.argv[1:]

    if len(files) != 1:
        print("Usage: ./taskmaster conf.yaml")
        exit(os.EX_OK)

    try:
        with open(files[0], 'r') as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        ValueError(f'Configuration file ({files[0]}) not found')
    except Exception as E:
        ValueError(f'Can\'t parse configuration file ({files[0]}) due to:\n{E}')

class Programs:

    def __init__(self):
        self.programs = []
        self.names = set()

    def load(self):
        confs = self.load_conf()
        if not confs:
            exit(os.EX_OK)
        for name, properties in confs.items():
            self.programs.append(Program(name, properties))

    def load_conf(self, init=True):
        try:
            return load_config_file()
        except Exception as e:
            print(f'{str(e)}')

    def reload(self):
        confs = self.load_conf()
        print(confs)
        if not confs:
            return
        for name, properties in confs.items():
            new_program = Program(name, properties)
            for index, value in enumerate(self.programs):
                if name == value.name and value.reload_has_substantive_change(new_program):
                    print('etto 1')
                    # del self.programs[index]
                    self.programs.insert(index, new_program) 
                    self.programs[index].execute()
                elif name == value.name and isinstance(new_program.count, type(self.programs[index].count)) and new_program.count != self.programs[index].count:
                    print('etto 2')
                    value.assign_count(properties["count"])
                    value.reload()

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
