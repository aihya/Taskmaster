from ast import Dict
import yaml
import os
import sys
from program import Program


def load_config_file():
    files = sys.argv[1:]
    full_stream = []
    if len(files) == 0:
        print("Usage: ./taskmaster conf.yaml")
        exit(os.EX_OK)
    try:
        for file in files:
            with open(file, "r") as stream:
                full_stream.append(stream.read())
        if not full_stream:
            return {}  
        load_iter = yaml.safe_load_all("\n---\n".join(full_stream))
        full_load = next(load_iter)
        for itr in load_iter:
            full_load.update(itr)
        return full_load
    except Exception as E:
        raise ValueError(f"Can't parse configuration file ({files[0]})")


class ProgramsManager:

    def __init__(self):
        self.programs_dict: Dict[str, Program] = {}
        self.names = set()

    def programs(self):
        return self.programs_dict.values()

    def load(self):
        confs = load_config_file()
        if not confs:
            print("\033[31m Error:\033[0m empty config")
            exit(os.EX_OK)
        for name, properties in confs.items():
            new_program = Program(name, properties)
            self.programs_dict.update({new_program.name: new_program})

    def reload(self):
        confs = load_config_file()
        for prog_name in list(self.programs_dict.keys()):
            if prog_name in confs:
                config = confs[prog_name]
                try:
                    if self.programs_dict[prog_name].reload_has_substantive_change(config):
                        new_program = Program(prog_name, config)
                        self.programs_dict[prog_name].kill()
                        del self.programs_dict[prog_name]
                        self.programs_dict[prog_name] = new_program
                        if self.programs_dict[prog_name].auto_start:
                            self.programs_dict[prog_name].execute()
                    else:
                        self.programs_dict[prog_name].assign_count(config["count"])
                        self.programs_dict[prog_name].reload()
                except Exception as e:
                    print(
                        f"\033[33mWarning:\033[0m error reloading config file for {prog_name} ({str(e)})"
                    )
                finally:
                    del confs[prog_name]
            else:
                self.programs_dict[prog_name].kill()
                del self.programs_dict[prog_name]
        for prog_name, config in confs.items():
            self.programs_dict[prog_name] = Program(prog_name, config)
            if self.programs_dict[prog_name].auto_start:
                self.programs_dict[prog_name].execute()

    def status(self):
        for _, program in self.programs_dict.items():
            program.status()

    def full_status(self):
        for _, program in self.programs_dict.items():
            program.full_status()

    def launch(self):
        for _, program in self.programs_dict.items():
            if program.auto_start:
                program.execute()
