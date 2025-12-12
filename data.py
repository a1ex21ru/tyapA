import dataclasses
import typing
from enum import StrEnum
from collections import defaultdict

nested_dict = lambda: defaultdict(nested_dict)

TYPES = [
    'int',
    'float32',
    'bool',
]

key_words = [
    'program',
    'main',
    '&&',
    '||',
    '!',
    'type',
    'var',
    'True',
    'False',
    'while',
    *TYPES,
]


class Type:
    pass


def parse_value(var_type, value):
    match var_type:
        case 'int':
            return int(value), 'int'
        case 'float32':
            return float(value), 'float32'
        case 'bool':
            return True if (isinstance(value, str) and value == 'True') or isinstance(value,
                                                                                      bool) and value else False, 'bool'
        case _:
            raise Exception(f'Cannot parse value \'{value}\' in type \'{var_type}\'')


@dataclasses.dataclass
class SimpleVar:
    name: str
    type: str
    value: any

    def set_value(self, value):
        self.value, _ = parse_value(self.type, value)


@dataclasses.dataclass
class ArrayVar:
    name: str
    type: str
    sizes: list[int]
    values: defaultdict = dataclasses.field(default_factory=nested_dict)

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def set_value(self, indexes, value):
        values = self.values
        for index in indexes[:-1]:
            values = values[index]
        values[indexes[-1]], _ = parse_value(self.type, value)

    def get_value(self, indexes):
        values = self.values
        for index in indexes[:-1]:
            values = values[index]
        return values[indexes[-1]]


@dataclasses.dataclass
class Token:
    name: str
    value: any

    def __str__(self):
        return f'("{self.name}": {self.value})'

    def __repr__(self):
        return f'("{self.name}": {self.value})'
