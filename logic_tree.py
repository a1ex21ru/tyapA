from copy import deepcopy

from data import *


class Node:
    def __init__(self, token: Token, left=None, right=None):
        self.token = token
        self.indexes = []
        self.left = left
        self.right = right

    def __repr__(self):
        if self.left and self.right:
            return f"({self.left} {self.token} {self.right})"
        elif self.left:
            return f"({self.token} {self.left})"
        else:
            return str(self.token)


def precedence(op):
    """Приоритет операций"""
    if op.name == 'and' or op.name == 'or':
        return 1
    if op.name == 'rel':
        return 2
    return 0


def apply_op(ops, values):
    """Создаёт узел дерева и помещает его обратно в стек значений"""
    try:
        op = ops.pop()
        if op.name == 'not':
            operand = values.pop()
            node = Node(op, left=operand)
        else:
            right = values.pop()
            left = values.pop()
            node = Node(op, left, right)
        values.append(node)
    except Exception as e:
        raise Exception(f'Invalid operation, {e}')


def build_expression_tree_logic(lst: list[Token], pos: int):
    """Строит дерево выражения из строки"""
    from symantic import is_key, is_keys, parse_indexes
    values = []  # стек для чисел (или узлов)
    ops = []  # стек для операторов

    while not is_keys(lst, pos, ['{', ';'])[1]:
        token = lst[pos]

        if is_keys(lst, pos, ['num', 'id', 'True', 'False'])[1]:
            values.append(Node(token))
            if ops and ops[-1].name == 'not':
                apply_op(ops, values)

        elif is_key(lst, pos, '('):
            ops.append(token)

        elif is_key(lst, pos, ')'):
            while ops and ops[-1].name != '(':
                apply_op(ops, values)
            try:
                ops.pop()  # убираем '('
            except Exception as e:
                raise Exception(f'Invalid operation, {e}')

        elif is_keys(lst, pos, ['and', 'or', 'rel'])[1]:
            while (
                    ops
                    and ops[-1].name != '('
                    and precedence(ops[-1]) >= precedence(token)
            ):
                apply_op(ops, values)
            ops.append(token)
        elif is_key(lst, pos, 'not'):
            ops.append(token)
        elif is_key(lst, pos, '['):
            node = values[-1]
            node.indexes, pos = parse_indexes(lst, pos)
            pos -= 1
        else:
            raise Exception(f'Unexpected token: \'{lst[pos]}\'')

        pos += 1

    # Обрабатываем оставшиеся операторы
    while ops:
        apply_op(ops, values)

    return values[0] if values else None, pos


def evaluate_logic(tree: Node, variables: dict[str, SimpleVar | ArrayVar], var_type: str,
                   operations: list[SimpleVar | ArrayVar]) -> (bool | int | float, SimpleVar | ArrayVar):
    from symantic import check_array

    if not tree:
        return None, None
    token = tree.token

    if tree.left is None and tree.right is None:
        value = token.value
        if token.name == 'num':
            value = parse_value('float32', value)[0]
            name = f'${operations.last_index}'
            var = SimpleVar(
                name=name,
                type=var_type,
                value=f'{value}',
            )
            operations.append(var)
            return value, var
        if token.name in {'False', 'True'}:
            value_ass, parse_type = parse_value(var_type, token.name)
            if var_type != parse_type:
                raise Exception(f'Unexpected type \'{parse_type}\' neer token \'{token}\'')
            name = f'${operations.last_index}'
            var = SimpleVar(
                name=name,
                type=var_type,
                value=f'{value_ass}',
            )
            operations.append(var)
            return value_ass, var
        var_ass = variables.get(value)
        if not var_ass:
            raise Exception(f'Not found var in all variables: \'{token}\'')
        var = deepcopy(var_ass)
        if isinstance(var_ass, ArrayVar):
            check_array(tree.indexes, var_ass)
            value_ass = var_ass.get_value(tree.indexes)
            var.sizes = tree.indexes
        elif isinstance(var_ass, SimpleVar):
            value_ass = var_ass.value
        else:
            raise Exception(f'Unexpected type of var \'{var_ass}\'')
        if value_ass is None:
            raise Exception(f'Value of \'{var_ass}\' is None')
        operations.append(var)
        return value_ass, var

    left_val, lvar = evaluate_logic(tree.left, variables, var_type, operations)
    right_val, rvar = evaluate_logic(tree.right, variables, var_type, operations)

    name = f'${operations.last_index}'

    if token.name == 'not':
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'not {lvar.name}',
        )
        operations.append(var)
        return not left_val, var
    if token.name == 'and':
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} and {rvar.name}',
        )
        operations.append(var)
        return left_val and right_val, var
    if token.name == 'or':
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} or {rvar.name}',
        )
        operations.append(var)
        return left_val or right_val, var
    elif token.name == 'rel' and token.value == 6:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} != {rvar.name}',
        )
        operations.append(var)
        return left_val != right_val, var
    elif token.name == 'rel' and token.value == 5:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} == {rvar.name}',
        )
        operations.append(var)
        return left_val == right_val, var
    elif token.name == 'rel' and token.value == 4:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} >= {rvar.name}',
        )
        operations.append(var)
        return left_val >= right_val, var
    elif token.name == 'rel' and token.value == 3:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} > {rvar.name}',
        )
        operations.append(var)
        return left_val > right_val, var
    elif token.name == 'rel' and token.value == 2:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} <= {rvar.name}',
        )
        operations.append(var)
        return left_val <= right_val, var
    elif token.name == 'rel' and token.value == 1:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} < {rvar.name}',
        )
        operations.append(var)
        return left_val < right_val, var
