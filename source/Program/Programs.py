from ast import Dict
from io import BytesIO
import yaml
import os
import sys
from Program import Program


def load_config_file():
    files = sys.argv[1:]
    full_stream = []
    if len(files) == 0:
        print("Usage: ./taskmaster conf.yaml")
        exit(os.EX_OK)

    try:
        print(files)
        for file in files:
            with open(file, "r") as stream:
                full_stream.append(stream.read())
        load_iter = yaml.safe_load_all("\n---\n".join(full_stream))
        full_load = next(load_iter)
        for itr in load_iter:
            full_load.update(itr)
        return full_load
    except FileNotFoundError as e:
        ValueError(f"{str(e)}")
    except Exception as E:
        ValueError(f"Can't parse configuration file ({files[0]}) due to:\n{E}")


class Programs:

    def __init__(self):
        self.programs_dict: Dict[str, Program] = {}
        self.names = set()

    def programs(self):
        return self.programs_dict.values()

    def load(self):
        confs = load_config_file()
        if not confs:
            exit(os.EX_OK)
        for name, properties in confs.items():
            new_program = Program(name, properties)
            self.programs_dict.update({new_program.name: new_program})

    def reload(self):
        confs = load_config_file()
        for name, config in confs.items():
            if name in self.programs_dict:
                try:
                    if self.programs_dict[name].reload_has_substantive_change(config):
                        new_program = Program(name, config)
                        del self.programs_dict[name]
                        self.programs_dict[name] = new_program
                    else:
                        self.programs_dict[name].assign_count(config["count"])
                        self.programs_dict[name].reload()
                except Exception as e:
                    print(
                        f"\033[33mWarning:\033[0m error reloading config file for {name} ({str(e)})"
                    )
                    continue
            else:
                self.programs_dict[name] = Program(name, config)

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

    def force_kill(self, program):
        program.kill()

    def force_kill_all(self):
        for _, program in self.programs_dict.items():
            program.force_kill()
