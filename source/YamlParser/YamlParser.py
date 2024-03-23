import sys
import yaml
from enum import Enum

class YamlParser:

    __slots__ = ('_properties',)

    def __init__(self, filename):
        try:
            with open(filename) as stream:
                self._properties = yaml.safe_load(stream)
                for k, v in self.properties:
                    setattr(k, v)
                for property in self.properties:
                    if   property == 'cwd': assert type(self.properties[property]) == str
                    
        except:
            # provisionnary
            print(f'Loading yaml file {filename}', file=sys.stderr)
            exit(0)

    @property
    def properties(self):
        return self._properties

if __name__ == "__main__":
    parser = YamlParser('test.yaml')