from copy import deepcopy
from data import *


class Node:
    """Узел абстрактного синтаксического дерева для арифметических выражений"""
    def __init__(self, token: Token, left=None, right=None):
        self.token = token
        self.indexes = []  # Для индексов массивов
        self.left = left
        self.right = right

    def __repr__(self):
        if self.left and self.right:
            return f"({self.left} {self.token} {self.right})"
        else:
            return str(self.token)


def precedence(op):
    """Приоритет арифметических операций"""
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
    """
    Строит дерево арифметического выражения из списка токенов
    
    Поддерживает:
    - Числовые константы
    - Идентификаторы (переменные)
    - Индексы массивов [...]
    - Арифметические операции +, -, *, /
    - Скобки ()
    
    Останавливается при встрече с ';'
    """
    values = []  # стек для значений (узлов)
    ops = []     # стек для операторов

    while pos < len(lst) and lst[pos].name != ';':
        token = lst[pos]

        # Операнды: числа, идентификаторы, логические константы
        if token.name in ['num', 'id', 'false', 'true']:
            values.append(Node(token))

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

        # Арифметические операции
        elif token.name in ['+', '*']:
            while (
                ops
                and ops[-1].name != '('
                and precedence(ops[-1]) >= precedence(token)
            ):
                apply_op(ops, values)
            ops.append(token)
        
        # Индекс массива
        elif token.name == '[':
            if not values:
                raise Exception(f'Array index without variable at position {pos}')
            
            node = values[-1]  # Последний узел должен быть переменной
            
            # Парсим индексы массива
            pos += 1
            index_tree, pos = build_expression_tree(lst, pos)
            
            if lst[pos].name != ']':
                raise Exception(f'Expected ], found: {lst[pos]}')
            
            # Сохраняем дерево индекса в узле переменной
            node.indexes.append(index_tree)
            # Не увеличиваем pos здесь, это будет сделано в конце цикла
        
        else:
            raise Exception(f'Unexpected token in arithmetic expression: \'{token}\'')

        pos += 1

    # Обрабатываем оставшиеся операторы
    while ops:
        if ops[-1].name == '(':
            raise Exception('Unmatched opening parenthesis')
        apply_op(ops, values)

    return values[0] if values else None, pos


def evaluate(tree: Node, variables: dict[str, SimpleVar | ArrayVar], var_type: str,
             operations: list[SimpleVar | ArrayVar]) -> tuple[float | int, SimpleVar | ArrayVar]:
    """
    Вычисляет значение арифметического выражения, представленного деревом
    
    Args:
        tree: корень дерева выражения
        variables: таблица символов
        var_type: ожидаемый тип результата
        operations: список операций для промежуточного кода
        
    Returns:
        (значение, переменная_с_результатом)
    """
    token = tree.token

    # Листовые узлы (операнды)
    if tree.left is None and tree.right is None:
        value = token.value
        
        # Числовая константа
        if token.name == 'num':
            value_ass, parse_type = parse_value(var_type, value)
            if var_type != parse_type:
                raise Exception(f'Type mismatch: expected {var_type}, got {parse_type} near token \'{token}\'')
            
            # Создаем временную переменную для константы
            temp_name = f'${operations.last_index}'
            var = SimpleVar(
                name=temp_name,
                type=var_type,
                value=value_ass,
            )
            operations.append(var)
            return value_ass, var
        
        # Переменная или массив
        var_ass = variables.get(value)
        if not var_ass:
            raise Exception(f'Undeclared variable: \'{value}\'')
        
        var = deepcopy(var_ass)
        
        # Обработка массива с индексами
        if isinstance(var_ass, ArrayVar):
            if not tree.indexes:
                raise Exception(f'Array \'{value}\' requires index')
            
            # Вычисляем индекс
            if len(tree.indexes) != 1:
                raise Exception(f'Array \'{value}\' requires exactly 1 index (one-dimensional)')
            
            index_val, index_var = evaluate(tree.indexes[0], variables, 'int', operations)
            
            if not isinstance(index_val, int):
                raise Exception(f'Array index must be integer, got: {type(index_val)}')
            
            if index_val < 0 or index_val >= var_ass.size:
                raise Exception(f'Array index {index_val} out of bounds [0, {var_ass.size})')
            
            value_ass = var_ass.get_value(index_val)
            if value_ass is None:
                value_ass = 0  # Неинициализированные элементы = 0
            
            # Создаем переменную для элемента массива
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

    # Рекурсивное вычисление бинарных операций
    left_val, lvar = evaluate(tree.left, variables, var_type, operations)
    right_val, rvar = evaluate(tree.right, variables, var_type, operations)

    temp_name = f'${operations.last_index}'

    # Сложение
    if token.name == '+' and token.value == 1:
        var = SimpleVar(
            name=temp_name,
            type=var_type,
            value=f'{lvar.name} + {rvar.name}',
        )
        operations.append(var)
        return left_val + right_val, var
    
    # Вычитание
    elif token.name == '+' and token.value == 2:
        var = SimpleVar(
            name=temp_name,
            type=var_type,
            value=f'{lvar.name} - {rvar.name}',
        )
        operations.append(var)
        return left_val - right_val, var
    
    # Умножение
    elif token.name == '*' and token.value == 1:
        var = SimpleVar(
            name=temp_name,
            type=var_type,
            value=f'{lvar.name} * {rvar.name}',
        )
        operations.append(var)
        return left_val * right_val, var
    
    # Деление
    elif token.name == '*' and token.value == 2:
        if right_val == 0:
            raise Exception('Division by zero')
        var = SimpleVar(
            name=temp_name,
            type=var_type,
            value=f'{lvar.name} / {rvar.name}',
        )
        operations.append(var)
        return left_val / right_val, var
    
    else:
        raise Exception(f'Unknown operation: {token}')