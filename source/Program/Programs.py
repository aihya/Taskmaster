from ast import Dict
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
        with open(files[0], "r") as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        ValueError(f"Configuration file ({files[0]}) not found")
    except Exception as E:
        ValueError(f"Can't parse configuration file ({files[0]}) due to:\n{E}")


class Programs:

    def __init__(self):
        self.programs_dict: Dict[str, Program] = {}
        self.names = set()

    def programs(self):
        return self.programs_dict.values()

    def load(self):
        try:
            confs = load_config_file()
            if not confs:
                exit(os.EX_OK)
            for name, properties in confs.items():
                try:
                    new_program = Program(name, properties)
                    self.programs_dict.update({new_program.name: new_program})
                except Exception as e:
                    print(str(e))
                    continue
        except Exception as e:
            print(str(e))
        print(self.programs_dict)

    def reload(self):
        try:
            confs = load_config_file()
            for name, config in confs.items():
                if name in self.programs_dict:
                    if self.programs_dict[name].reload_has_substantive_change(config):
                        new_program = Program(name, config)
                        del self.programs_dict[name]
                        self.programs_dict[name] = new_program
                    else:
                        self.programs_dict[name].assign_count(config["count"])
                        self.programs_dict[name].reload()
                else:
                    self.programs_dict[name] = Program(name, config)
        except Exception as e:
            print(str(e))

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
