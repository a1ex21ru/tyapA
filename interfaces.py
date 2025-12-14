from symantic import *

SIZES = {
    'int': 4,
    'float': 8,
    'bool': 1,
}

def stack_calls(operations: Operations[SimpleVar | ArrayVar]) -> str:
    calls = []
    for pos, var in enumerate(operations):
        if isinstance(var, SimpleVar):
            calls.append(f"{pos:04d}:\t{var.name}={var.value}")
    return '\n'.join(calls)


def stack_variables(operations: Operations[SimpleVar | ArrayVar]) -> str:
    variables = []
    pos = 0
    already_added = set()
    flag = False
    for var in operations:
        if var.name in already_added or (flag and var.name[0] != '$'):
           continue
        if var.name[0] == '$':
            flag = True
        already_added.add(var.name)
        if isinstance(var, SimpleVar):
            size = SIZES[var.type]
            pos += size
            variables.append(f"{pos:04d}:\t{var.name:10}\tSize:{size}")
    return '\n'.join(variables)
