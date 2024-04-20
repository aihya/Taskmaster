import sys
import yaml
from enum import Enum

assert_type = lambda pt, t: assert pt == t, TypeError(f'Illegal type {pt}')

types = {'cmd': str,
        'auto_start': bool,
        'auto_restart': str,
        'exit_code': int,
        'start_time': int,
        'max_retry': int,
        'stop_signal': str,
        'stop_time': int,
        'working_dir': str,
        'stdout': str,
        'stderr': str,
        'umask': int
}

class YamlParser:

    __slots__ = ('_props',)

    def __init__(self, filename):
        try:
            with open(filename) as stream:
                self._props = yaml.safe_load(stream)
                for prop in self.props:
                    prop_type = type(self.props[prop])
                    if 
        except:
            # provisionnary
            print(f'Loading yaml file {filename}', file=sys.stderr)
            exit(0)

    @property
    def properties(self):
        return self._properties

if __name__ == "__main__":
    parser = YamlParser('test.yaml')
