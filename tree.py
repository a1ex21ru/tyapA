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
    if not ops:
        raise Exception('Operator stack is empty')
    if len(values) < 2:
        raise Exception(f'Not enough values for operation. Values: {len(values)}, need 2')
    
    try:
        op = ops.pop()
        right = values.pop()
        left = values.pop()
        node = Node(op, left, right)
        values.append(node)
    except Exception as e:
        raise Exception(f'Invalid operation: {e}')


def build_expression_tree(lst: list[Token], pos: int, terminators: list[str] = None):
    """
    Строит дерево арифметического выражения из списка токенов
    
    ИСПРАВЛЕНО: теперь останавливается на любом терминаторе, не только на ';'
    
    Args:
        lst: список токенов
        pos: начальная позиция
        terminators: список терминаторов (по умолчанию [';'])
    
    Поддерживает:
    - Числовые константы
    - Идентификаторы (переменные)
    - Индексы массивов [...]
    - Арифметические операции +, -, *, /
    - Скобки ()
    """
    if terminators is None:
        terminators = [';']
    
    values = []  # стек для значений (узлов)
    ops = []     # стек для операторов

    while pos < len(lst) and lst[pos].name not in terminators:
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
            if not ops or ops[-1].name != '(':
                raise Exception('Unmatched closing parenthesis')
            ops.pop()  # убираем '('

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
            
            # Рекурсивно парсим индекс до ']'
            pos += 1
            index_tree, pos = build_expression_tree(lst, pos, terminators=[']'])
            
            if pos >= len(lst) or lst[pos].name != ']':
                raise Exception(f'Expected ], found: {lst[pos] if pos < len(lst) else "EOF"}')
            
            # Сохраняем дерево индекса в узле переменной
            node.indexes.append(index_tree)
            # pos уже указывает на ']', увеличим его в конце цикла
        
        else:
            # Неожиданный токен - возможно, это терминатор
            if token.name in terminators:
                break
            raise Exception(f'Unexpected token in arithmetic expression: \'{token}\'')

        pos += 1

    # Обрабатываем оставшиеся операторы
    while ops:
        if ops[-1].name == '(':
            raise Exception('Unmatched opening parenthesis')
        apply_op(ops, values)

    if not values:
        return None, pos
    
    return values[0], pos


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
    if not tree:
        raise Exception('Empty expression tree')
    
    token = tree.token

    # Листовые узлы (операнды)
    if tree.left is None and tree.right is None:
        value = token.value
        
        # Числовая константа
        if token.name == 'num':
            value_ass, parse_type = parse_value(var_type, value)
            # Не требуем строгого соответствия типов для констант
            # int можно присвоить в float и наоборот
            
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
                index_val = int(index_val)  # Приводим к int
            
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
                # Разрешаем использование неинициализированных переменных (значение = 0)
                value_ass = 0
                var_ass.value = 0
        
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