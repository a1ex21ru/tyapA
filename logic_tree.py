from copy import deepcopy
from data import *


class Node:
    """Узел абстрактного синтаксического дерева для логических выражений"""
    def __init__(self, token: Token, left=None, right=None):
        self.token = token
        self.indexes = []  # Для индексов массивов
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
    """Приоритет логических операций"""
    if op.name in ['and', 'or']:
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
        raise Exception(f'Invalid logical operation, {e}')


def build_expression_tree_logic(lst: list[Token], pos: int):
    """
    Строит дерево логического выражения из списка токенов
    
    Поддерживает:
    - Логические константы (true, false)
    - Числовые константы (для сравнений)
    - Идентификаторы (переменные)
    - Индексы массивов [...]
    - Логические операции &&, ||, !
    - Операции сравнения <, <=, >, >=, ==, !=
    - Скобки ()
    
    Останавливается при встрече с '{' или ';'
    """
    values = []  # стек для значений (узлов)
    ops = []     # стек для операторов

    while pos < len(lst) and lst[pos].name not in ['{', ';']:
        token = lst[pos]

        # Операнды: числа, идентификаторы, логические константы
        if token.name in ['num', 'id', 'true', 'false']:
            values.append(Node(token))
            
            # Если есть унарный NOT в стеке, применяем его сразу
            if ops and ops[-1].name == 'not':
                apply_op(ops, values)

        # Открывающая скобка
        elif token.name == '(':
            ops.append(token)

        # Закрывающая скобка
        elif token.name == ')':
            while ops and ops[-1].name != '(':
                apply_op(ops, values)
            try:
                ops.pop()  # убираем '('
            except Exception as e:
                raise Exception(f'Unmatched parentheses: {e}')

        # Логические и реляционные операции
        elif token.name in ['and', 'or', 'rel']:
            while (
                ops
                and ops[-1].name != '('
                and precedence(ops[-1]) >= precedence(token)
            ):
                apply_op(ops, values)
            ops.append(token)
        
        # Унарное отрицание
        elif token.name == 'not':
            ops.append(token)
        
        # Индекс массива
        elif token.name == '[':
            if not values:
                raise Exception(f'Array index without variable at position {pos}')
            
            node = values[-1]
            
            # Парсим индекс
            pos += 1
            
            # Для индекса используем арифметическое выражение
            from tree import build_expression_tree
            index_tree, pos = build_expression_tree(lst, pos)
            
            if lst[pos].name != ']':
                raise Exception(f'Expected ], found: {lst[pos]}')
            
            node.indexes.append(index_tree)
        
        else:
            raise Exception(f'Unexpected token in logical expression: \'{token}\'')

        pos += 1

    # Обрабатываем оставшиеся операторы
    while ops:
        if ops[-1].name == '(':
            raise Exception('Unmatched opening parenthesis')
        apply_op(ops, values)

    return values[0] if values else None, pos


def evaluate_logic(tree: Node, variables: dict[str, SimpleVar | ArrayVar], var_type: str,
                   operations: list[SimpleVar | ArrayVar]) -> tuple[bool | int | float, SimpleVar | ArrayVar]:
    """
    Вычисляет значение логического выражения, представленного деревом
    
    Args:
        tree: корень дерева выражения
        variables: таблица символов
        var_type: ожидаемый тип результата (обычно 'bool')
        operations: список операций для промежуточного кода
        
    Returns:
        (значение, переменная_с_результатом)
    """
    if not tree:
        return None, None
    
    token = tree.token

    # Листовые узлы (операнды)
    if tree.left is None and tree.right is None:
        value = token.value
        
        # Числовая константа
        if token.name == 'num':
            value = parse_value('float', value)[0]
            temp_name = f'${operations.last_index}'
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{value}',
            )
            operations.append(var)
            return value, var
        
        # Логическая константа
        if token.name in {'false', 'true'}:
            value_ass, parse_type = parse_value(var_type, token.name)
            if var_type != parse_type:
                raise Exception(f'Type mismatch: expected {var_type}, got {parse_type} near token \'{token}\'')
            
            temp_name = f'${operations.last_index}'
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{value_ass}',
            )
            operations.append(var)
            return value_ass, var
        
        # Переменная или массив
        var_ass = variables.get(value)
        if not var_ass:
            raise Exception(f'Undeclared variable: \'{token}\'')
        
        var = deepcopy(var_ass)
        
        # Обработка массива с индексами
        if isinstance(var_ass, ArrayVar):
            if not tree.indexes:
                raise Exception(f'Array \'{value}\' requires index')
            
            if len(tree.indexes) != 1:
                raise Exception(f'Array \'{value}\' requires exactly 1 index')
            
            # Вычисляем индекс
            from tree import evaluate as evaluate_arith
            index_val, index_var = evaluate_arith(tree.indexes[0], variables, 'int', operations)
            
            if not isinstance(index_val, int):
                raise Exception(f'Array index must be integer, got: {type(index_val)}')
            
            if index_val < 0 or index_val >= var_ass.size:
                raise Exception(f'Array index {index_val} out of bounds [0, {var_ass.size})')
            
            value_ass = var_ass.get_value(index_val)
            if value_ass is None:
                value_ass = 0
            
            var = SimpleVar(
                name=f"{var_ass.name}[{index_val}]",
                type=var_ass.type,
                value=value_ass
            )
        
        # Обработка простой переменной
        elif isinstance(var_ass, SimpleVar):
            if tree.indexes:
                raise Exception(f'Variable \'{value}\' is not an array')
            value_ass = var_ass.value
            if value_ass is None:
                raise Exception(f'Variable \'{value}\' is not initialized')
        
        else:
            raise Exception(f'Unexpected variable type: {type(var_ass)}')
        
        operations.append(var)
        return value_ass, var

    # Унарная операция NOT
    if tree.right is None and tree.left is not None:
        left_val, lvar = evaluate_logic(tree.left, variables, var_type, operations)
        
        temp_name = f'${operations.last_index}'
        
        if token.name == 'not':
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'not {lvar.name}',
            )
            operations.append(var)
            return not left_val, var

    # Бинарные операции
    left_val, lvar = evaluate_logic(tree.left, variables, var_type, operations)
    right_val, rvar = evaluate_logic(tree.right, variables, var_type, operations)

    temp_name = f'${operations.last_index}'

    # Логические операции
    if token.name == 'and':
        var = SimpleVar(
            name=temp_name,
            type=var_type,
            value=f'{lvar.name} and {rvar.name}',
        )
        operations.append(var)
        return left_val and right_val, var
    
    if token.name == 'or':
        var = SimpleVar(
            name=temp_name,
            type=var_type,
            value=f'{lvar.name} or {rvar.name}',
        )
        operations.append(var)
        return left_val or right_val, var
    
    # Операции сравнения
    if token.name == 'rel':
        if token.value == 1:  # <
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{lvar.name} < {rvar.name}',
            )
            operations.append(var)
            return left_val < right_val, var
        
        elif token.value == 2:  # <=
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{lvar.name} <= {rvar.name}',
            )
            operations.append(var)
            return left_val <= right_val, var
        
        elif token.value == 3:  # >
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{lvar.name} > {rvar.name}',
            )
            operations.append(var)
            return left_val > right_val, var
        
        elif token.value == 4:  # >=
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{lvar.name} >= {rvar.name}',
            )
            operations.append(var)
            return left_val >= right_val, var
        
        elif token.value == 5:  # ==
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{lvar.name} == {rvar.name}',
            )
            operations.append(var)
            return left_val == right_val, var
        
        elif token.value == 6:  # !=
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=f'{lvar.name} != {rvar.name}',
            )
            operations.append(var)
            return left_val != right_val, var
    
    raise Exception(f'Unknown operation: {token}')