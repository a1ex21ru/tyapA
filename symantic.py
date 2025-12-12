from copy import deepcopy

from logic_tree import *
from tree import *
from data import *


def is_float(st):
    try:
        float(st)
        return True
    except:
        return False


def is_int(st):
    try:
        int(st)
        return True
    except:
        return False


def is_bool(st):
    try:
        bool(st)
        return True
    except:
        return False


def is_key(lst: list[Token], pos: int, key: str):
    try:
        return lst[pos].name == key
    except:
        return False


def is_keys(lst: list[Token], pos: int, keys: list[str]) -> (str | None, bool):
    for key in keys:
        if is_key(lst, pos, key):
            return key, True
    return None, False


def check_key(lst: list[Token], pos: int, key: str):
    if not is_key(lst, pos, key):
        raise Exception(f'Not found key \'{key}\', found: \'{lst[pos]}\'')


def is_id(lst: list[Token], pos: int, value: any = None):
    _is_id = lst[pos].name == 'id'
    has_value = lst[pos].value == value
    return _is_id if not value else _is_id & has_value


def check_id(lst: list[Token], pos: int, value: any = None):
    if not is_id(lst, pos, value):
        raise Exception(f'Not found id \'{value}\', found: \'{lst[pos]}\'')


def check_count_fig(lst: list[Token]):
    cnt = 0
    for pos, obj in enumerate(lst):
        if is_key(lst, pos, '{'):
            cnt += 1
        if is_key(lst, pos, '}'):
            cnt -= 1
    if cnt:
        raise Exception('Count \'{\' does not match \'}\'')


def get_num_const(lst: list[Token], pos: int):
    check_key(lst, pos, 'num')
    return int(lst[pos].value)


def parse_indexes(lst: list[Token], pos: int) -> (list[int], int):
    _, found = is_keys(lst, pos, ['[', 'num', ']'])
    indexes = []
    while found:
        check_key(lst, pos, '[')
        pos += 1
        indexes.append(get_num_const(lst, pos))
        pos += 1
        check_key(lst, pos, ']')
        pos += 1
        _, found = is_keys(lst, pos, ['[', 'num', ']'])
    return indexes, pos


def check_array(indexes: list[int], var_ass: ArrayVar):
    for order, index in enumerate(indexes):
        if index >= var_ass.sizes[order]:
            raise Exception(f'Index gte size array \'{var_ass}\'')
        if len(indexes) != len(var_ass.sizes):
            raise Exception(f'Incorrect indexes: \'{indexes}\', required: \'{var_ass.sizes}\'')


def get_var(lst: list[Token], pos: int) -> ((SimpleVar | ArrayVar), int):
    name = lst[pos - 1].value
    var_type, found = is_keys(lst, pos, TYPES)
    if found:
        check_key(lst, pos + 1, ';')
        return SimpleVar(
            name=name,
            type=var_type,
            value=None,
        ), pos + 2
    elif is_key(lst, pos, '['):
        iter_pos = pos + 1
        sizes = []
        _, found = is_keys(lst, iter_pos, TYPES)
        while not found:
            sizes.append(get_num_const(lst, iter_pos))
            iter_pos += 1
            check_key(lst, iter_pos, ']')
            iter_pos += 1
            var_type, found = is_keys(lst, iter_pos, TYPES)
            iter_pos += 1
        check_key(lst, iter_pos, ';')
        return ArrayVar(
            name=name,
            type=var_type,
            sizes=sizes,
        ), iter_pos + 1
    else:
        raise Exception(f'Not found var with type: {lst[pos]}')


def parse_ass(
        lst: list[Token],
        pos: int,
        variables: dict[str, SimpleVar | ArrayVar],
        operations: list[SimpleVar | ArrayVar],
) -> int:
    name = lst[pos].value
    var_ass = variables.get(name)
    if not var_ass:
        raise Exception(f'Not found var in all variables: \'{lst[pos]}\'')
    iter_pos = pos + 1

    if isinstance(var_ass, ArrayVar):
        indexes, iter_pos = parse_indexes(lst, iter_pos)
        check_array(indexes, var_ass)
        check_key(lst, iter_pos, 'ass')
        iter_pos += 1

        tree, iter_pos = build_expression_tree(lst, iter_pos)
        val, var = evaluate(tree, variables, var_ass.type, operations)
        var_ass.set_value(indexes, val)
        operations.append(
            SimpleVar(
                name=var_ass.name,
                type=var_ass.type,
                value=var.name,
            )
        )
    elif isinstance(var_ass, SimpleVar):
        check_key(lst, iter_pos, 'ass')
        iter_pos += 1
        if var_ass.type == 'bool':
            tree, iter_pos = build_expression_tree_logic(lst, iter_pos)
            val, var = evaluate_logic(tree, variables, var_ass.type, operations)
            var_ass.set_value(val)
            operations.append(
                SimpleVar(
                    name=var_ass.name,
                    type=var_ass.type,
                    value=var.name,
                )
            )
        else:
            tree, iter_pos = build_expression_tree(lst, iter_pos)
            val, var = evaluate(tree, variables, var_ass.type, operations)
            var_ass.set_value(val)
            operations.append(
                SimpleVar(
                    name=var_ass.name,
                    type=var_ass.type,
                    value=var.name,
                )
            )
    else:
        raise Exception(f'Unexpected type of var \'{var_ass}\'')

    return iter_pos + 1


def parse_while(
        lst: list[Token],
        pos: int,
        variables: dict[str, SimpleVar | ArrayVar],
        operations: list[SimpleVar | ArrayVar],
) -> int:
    iter_pos = pos + 1
    logic_tree, iter_pos = build_expression_tree_logic(lst, iter_pos)
    val = evaluate_logic(logic_tree, variables, 'bool', operations)[0]
    if val:
        while evaluate_logic(logic_tree, variables, 'bool', operations)[0]:
            parse_main(lst, iter_pos + 1, variables, operations)
            iter_pos = pos + 1
            logic_tree, iter_pos = build_expression_tree_logic(lst, iter_pos)
    while not is_key(lst, iter_pos, '}'):  # заканчиваем цикл
        iter_pos += 1
    return iter_pos + 1


def parse_main(
        lst: list[Token],
        pos: int,
        variables: dict[str, SimpleVar | ArrayVar],
        operations: list[SimpleVar | ArrayVar],
) -> int:
    while not is_key(lst, pos, '}'):
        if is_key(lst, pos, 'id'):
            pos = parse_ass(lst, pos, variables, operations)
        elif is_key(lst, pos, 'while'):
            pos = parse_while(lst, pos, variables, operations)
        else:
            raise Exception('Expected id or while')
    return pos


class Operations(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_index = 0

    @property
    def last_index(self):
        self._last_index += 1
        return self._last_index


def symantic(tokens):
    lst = [Token(name=k, value=v) for data in tokens for k, v in data.items() if k != 'com']
    process_tokens = deepcopy(lst)

    check_key(process_tokens, 0, 'program')
    check_id(process_tokens, 1)
    check_key(process_tokens, 2, ';')
    check_count_fig(process_tokens)

    pos = 3
    variables: dict[str, SimpleVar | ArrayVar] = {}
    # Сегмент данных
    while not is_key(lst, pos, 'main'):
        check_key(process_tokens, pos, 'var')
        pos += 1
        check_id(process_tokens, pos)
        pos += 1
        var, pos = get_var(process_tokens, pos)
        variables[var.name] = var

    operations: Operations[SimpleVar | ArrayVar] = deepcopy(Operations(variables.values()))

    # Основная функция
    check_key(lst, pos, 'main')
    pos += 1
    check_key(lst, pos, '{')
    pos += 1
    pos = parse_main(lst, pos, variables, operations)
    check_key(lst, pos, '}')

    return operations

