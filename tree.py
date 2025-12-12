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
        else:
            return str(self.token)


def precedence(op):
    """Приоритет операций"""
    if op.name == '+':
        return 1
    if op.name == '*':
        return 2
    return 0


def apply_op(ops, values):
    """Создаёт узел дерева и помещает его обратно в стек значений"""
    try:
        op = ops.pop()
        right = values.pop()
        left = values.pop()
        node = Node(op, left, right)
        values.append(node)
    except Exception as e:
        raise Exception(f'Invalid operation, {e}')


def build_expression_tree(lst: list[Token], pos: int):
    """Строит дерево выражения из строки"""
    from symantic import is_key, is_keys, parse_indexes
    values = []  # стек для чисел (или узлов)
    ops = []  # стек для операторов

    while not is_key(lst, pos, ';'):
        token = lst[pos]

        if is_keys(lst, pos, ['num', 'id', 'False', 'True'])[1]:
            values.append(Node(token))

        elif is_key(lst, pos, '('):
            ops.append(token)

        elif is_key(lst, pos, ')'):
            while ops and ops[-1].name != '(':
                apply_op(ops, values)
            try:
                ops.pop()  # убираем '('
            except Exception as e:
                raise Exception(f'Invalid operation, {e}')

        elif is_keys(lst, pos, ['+', '*'])[1]:
            while (
                    ops
                    and ops[-1].name != '('
                    and precedence(ops[-1]) >= precedence(token)
            ):
                apply_op(ops, values)
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


def evaluate(tree: Node, variables: dict[str, SimpleVar | ArrayVar], var_type: str,
             operations: list[SimpleVar | ArrayVar]) -> (float | int, SimpleVar | ArrayVar):
    from symantic import check_array

    token = tree.token

    if tree.left is None and tree.right is None:
        value = token.value
        if token.name == 'num':
            value_ass, parse_type = parse_value(var_type, value)
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

    left_val, lvar = evaluate(tree.left, variables, var_type, operations)
    right_val, rvar = evaluate(tree.right, variables, var_type, operations)

    name = f'${operations.last_index}'

    if token.name == '+' and token.value == 1:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} + {rvar.name}',
        )
        operations.append(var)
        return left_val + right_val, var
    elif token.name == '+' and token.value == 2:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} - {rvar.name}',
        )
        operations.append(var)
        return left_val - right_val, var
    elif token.name == '*' and token.value == 1:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} * {rvar.name}',
        )
        operations.append(var)
        return left_val * right_val, var
    elif token.name == '*' and token.value == 2:
        var = SimpleVar(
            name=name,
            type=var_type,
            value=f'{lvar.name} / {rvar.name}',
        )
        operations.append(var)
        return left_val / right_val, var
