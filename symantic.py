from copy import deepcopy
from logic_tree import *
from tree import *
from data import *


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def is_key(lst: list[Token], pos: int, key: str) -> bool:
    """Проверка, является ли токен на позиции pos ключевым словом key"""
    try:
        return lst[pos].name == key
    except:
        return False


def is_keys(lst: list[Token], pos: int, keys: list[str]) -> tuple[str | None, bool]:
    """Проверка, является ли токен одним из ключевых слов"""
    for key in keys:
        if is_key(lst, pos, key):
            return key, True
    return None, False


def check_key(lst: list[Token], pos: int, key: str):
    """Проверка обязательного наличия ключевого слова"""
    if not is_key(lst, pos, key):
        raise Exception(f'Expected \'{key}\', but found: \'{lst[pos]}\'')


def is_id(lst: list[Token], pos: int, value: any = None) -> bool:
    """Проверка, является ли токен идентификатором"""
    _is_id = lst[pos].name == 'id'
    has_value = lst[pos].value == value if value else True
    return _is_id and has_value


def check_id(lst: list[Token], pos: int, value: any = None):
    """Проверка обязательного наличия идентификатора"""
    if not is_id(lst, pos, value):
        raise Exception(f'Expected identifier{f" \'{value}\'" if value else ""}, found: \'{lst[pos]}\'')


def check_count_braces(lst: list[Token]):
    """Проверка парности фигурных скобок"""
    cnt = 0
    for pos, obj in enumerate(lst):
        if is_key(lst, pos, '{'):
            cnt += 1
        if is_key(lst, pos, '}'):
            cnt -= 1
    if cnt != 0:
        raise Exception('Unmatched braces: count \'{\' does not match \'}\'')


def get_num_const(lst: list[Token], pos: int) -> int:
    """Получение числовой константы"""
    check_key(lst, pos, 'num')
    return int(float(lst[pos].value))  # Преобразуем через float для поддержки вещественных


# ============================================================================
# ПАРСИНГ ОБЪЯВЛЕНИЙ
# ============================================================================

def get_var_declaration(lst: list[Token], pos: int) -> tuple[SimpleVar | ArrayVar, int]:
    """
    Парсинг объявления переменной
    Синтаксис: Тип Имя [Размер]? ;
    
    Примеры:
        int x;
        float arr[10];
    
    Returns:
        (переменная, новая_позиция)
    """
    # Получаем тип
    var_type, found = is_keys(lst, pos, TYPES)
    if not found:
        # Проверяем, может это пользовательский тип
        if is_id(lst, pos):
            var_type = lst[pos].value
            pos += 1
        else:
            raise Exception(f'Expected type, found: \'{lst[pos]}\'')
    else:
        pos += 1
    
    # Получаем имя
    check_id(lst, pos)
    name = lst[pos].value
    pos += 1
    
    # Проверяем, массив ли это
    if is_key(lst, pos, '['):
        pos += 1
        size = get_num_const(lst, pos)
        pos += 1
        check_key(lst, pos, ']')
        pos += 1
        check_key(lst, pos, ';')
        pos += 1
        
        return ArrayVar(
            name=name,
            type=var_type,
            size=size,
            values=defaultdict(lambda: None)
        ), pos
    else:
        # Простая переменная
        check_key(lst, pos, ';')
        pos += 1
        
        return SimpleVar(
            name=name,
            type=var_type,
            value=None
        ), pos


def parse_type_definition(lst: list[Token], pos: int, type_aliases: dict) -> int:
    """
    Парсинг определения типа
    Синтаксис: type Имя_нового_типа Имя_базового_типа;
    
    Пример: type MyInt int;
    
    Returns:
        новая_позиция
    """
    check_key(lst, pos, 'type')
    pos += 1
    
    check_id(lst, pos)
    new_type_name = lst[pos].value
    pos += 1
    
    # Получаем базовый тип
    base_type, found = is_keys(lst, pos, TYPES)
    if not found:
        if is_id(lst, pos):
            base_type = lst[pos].value
            if base_type not in type_aliases:
                raise Exception(f'Unknown type: {base_type}')
            base_type = type_aliases[base_type]
        else:
            raise Exception(f'Expected type, found: \'{lst[pos]}\'')
    pos += 1
    
    check_key(lst, pos, ';')
    pos += 1
    
    # Сохраняем алиас типа
    type_aliases[new_type_name] = base_type
    
    return pos


# ============================================================================
# ПАРСИНГ ВЫРАЖЕНИЙ И ОПЕРАТОРОВ
# ============================================================================

def parse_assignment(
    lst: list[Token],
    pos: int,
    variables: dict[str, SimpleVar | ArrayVar],
    operations: list[SimpleVar | ArrayVar],
) -> int:
    """
    Парсинг оператора присваивания
    Синтаксис: Переменная = Выражение;
    
    Примеры:
        x = 5;
        arr[i] = x + 1;
    """
    check_id(lst, pos)
    name = lst[pos].value
    var_ass = variables.get(name)
    if not var_ass:
        raise Exception(f'Undeclared variable: \'{name}\'')
    
    iter_pos = pos + 1
    
    # Проверяем, массив ли это
    if isinstance(var_ass, ArrayVar):
        check_key(lst, iter_pos, '[')
        iter_pos += 1
        
        # Парсим индекс
        index_tree, iter_pos = build_expression_tree(lst, iter_pos)
        check_key(lst, iter_pos, ']')
        iter_pos += 1
        
        # Вычисляем индекс
        index_val, index_var = evaluate(index_tree, variables, 'int', operations)
        if not isinstance(index_val, int):
            raise Exception(f'Array index must be integer, got: {type(index_val)}')
        
        check_key(lst, iter_pos, 'ass')
        iter_pos += 1
        
        # Парсим правую часть
        tree, iter_pos = build_expression_tree(lst, iter_pos)
        val, var = evaluate(tree, variables, var_ass.type, operations)
        
        # Устанавливаем значение
        var_ass.set_value(index_val, val)
        
        # Генерируем операцию
        operations.append(
            SimpleVar(
                name=f"{var_ass.name}[{index_val}]",
                type=var_ass.type,
                value=var.name
            )
        )
        
    elif isinstance(var_ass, SimpleVar):
        check_key(lst, iter_pos, 'ass')
        iter_pos += 1
        
        # Парсим правую часть
        if var_ass.type == 'bool':
            tree, iter_pos = build_expression_tree_logic(lst, iter_pos)
            val, var = evaluate_logic(tree, variables, var_ass.type, operations)
        else:
            tree, iter_pos = build_expression_tree(lst, iter_pos)
            val, var = evaluate(tree, variables, var_ass.type, operations)
        
        # Устанавливаем значение
        var_ass.set_value(val)
        
        # Генерируем операцию
        operations.append(
            SimpleVar(
                name=var_ass.name,
                type=var_ass.type,
                value=var.name
            )
        )
    else:
        raise Exception(f'Unexpected variable type: {type(var_ass)}')
    
    return iter_pos


def parse_for_loop(
    lst: list[Token],
    pos: int,
    variables: dict[str, SimpleVar | ArrayVar],
    operations: list[SimpleVar | ArrayVar],
    type_aliases: dict
) -> int:
    """
    Парсинг цикла for в C-style
    Синтаксис: for (Тип Имя = Выражение; Условие; Имя = Выражение) { Операторы }
    
    Пример: for (int i = 0; i < 10; i = i + 1) { ... }
    
    Семантика:
        1. Инициализация переменной цикла (может быть с объявлением)
        2. Проверка условия перед каждой итерацией
        3. Выполнение тела цикла
        4. Выполнение инкремента
        5. Возврат к шагу 2
    """
    check_key(lst, pos, 'for')
    pos += 1
    check_key(lst, pos, '(')
    pos += 1
    
    # ========== ИНИЦИАЛИЗАЦИЯ ==========
    # Проверяем, есть ли объявление типа
    loop_var_name = None
    is_new_var = False
    
    var_type, found = is_keys(lst, pos, TYPES)
    if found:
        # Объявление новой переменной: int i = 0
        pos += 1
        check_id(lst, pos)
        loop_var_name = lst[pos].value
        pos += 1
        
        # Проверяем, не объявлена ли уже
        if loop_var_name in variables:
            raise Exception(f'Variable \'{loop_var_name}\' already declared in this scope')
        
        # Создаем переменную
        loop_var = SimpleVar(name=loop_var_name, type=var_type, value=None)
        variables[loop_var_name] = loop_var
        is_new_var = True
        
    else:
        # Используется существующая переменная: i = 0
        check_id(lst, pos)
        loop_var_name = lst[pos].value
        pos += 1
        
        if loop_var_name not in variables:
            raise Exception(f'Undeclared variable: \'{loop_var_name}\'')
        loop_var = variables[loop_var_name]
    
    # Парсим инициализацию (= Выражение)
    check_key(lst, pos, 'ass')
    pos += 1
    
    init_tree, pos = build_expression_tree_until(lst, pos, [';'])
    init_val, init_var = evaluate(init_tree, variables, loop_var.type, operations)
    loop_var.set_value(init_val)
    operations.append(
        SimpleVar(name=loop_var.name, type=loop_var.type, value=init_var.name)
    )
    
    check_key(lst, pos, ';')
    pos += 1
    
    # ========== УСЛОВИЕ ==========
    # Сохраняем позицию начала условия для повторных проверок
    condition_start_pos = pos
    
    # Первая проверка условия
    cond_tree, pos = build_expression_tree_logic_until(lst, pos, [';'])
    cond_val, cond_var = evaluate_logic(cond_tree, variables, 'bool', operations)
    
    check_key(lst, pos, ';')
    pos += 1
    
    # ========== ИНКРЕМЕНТ ==========
    # Сохраняем позицию инкремента
    increment_start_pos = pos
    
    # Пропускаем инкремент при первой проверке
    # Находим закрывающую скобку
    paren_count = 1
    temp_pos = pos
    while paren_count > 0:
        if is_key(lst, temp_pos, '('):
            paren_count += 1
        elif is_key(lst, temp_pos, ')'):
            paren_count -= 1
        temp_pos += 1
    pos = temp_pos
    
    check_key(lst, pos, '{')
    body_start_pos = pos + 1
    
    # Находим конец тела цикла
    brace_count = 1
    temp_pos = pos + 1
    while brace_count > 0:
        if is_key(lst, temp_pos, '{'):
            brace_count += 1
        elif is_key(lst, temp_pos, '}'):
            brace_count -= 1
        temp_pos += 1
    body_end_pos = temp_pos - 1
    
    # ========== ВЫПОЛНЕНИЕ ЦИКЛА ==========
    while cond_val:
        # Выполняем тело цикла
        parse_statements(lst, body_start_pos, body_end_pos, variables, operations, type_aliases)
        
        # Выполняем инкремент
        inc_pos = increment_start_pos
        check_id(lst, inc_pos)
        inc_name = lst[inc_pos].value
        inc_pos += 1
        check_key(lst, inc_pos, 'ass')
        inc_pos += 1
        inc_tree, _ = build_expression_tree_until(lst, inc_pos, [')'])
        inc_val, inc_var = evaluate(inc_tree, variables, loop_var.type, operations)
        loop_var.set_value(inc_val)
        operations.append(
            SimpleVar(name=loop_var.name, type=loop_var.type, value=inc_var.name)
        )
        
        # Проверяем условие снова
        cond_pos = condition_start_pos
        cond_tree, _ = build_expression_tree_logic_until(lst, cond_pos, [';'])
        cond_val, cond_var = evaluate_logic(cond_tree, variables, 'bool', operations)
    
    # Удаляем переменную цикла из области видимости, если она была объявлена в for
    if is_new_var:
        del variables[loop_var_name]
    
    return body_end_pos + 1


def build_expression_tree_until(lst: list[Token], pos: int, terminators: list[str]):
    """Построение дерева выражения до одного из терминаторов"""
    from tree import build_expression_tree
    
    # Находим позицию терминатора
    end_pos = pos
    paren_depth = 0
    while end_pos < len(lst):
        if is_key(lst, end_pos, '('):
            paren_depth += 1
        elif is_key(lst, end_pos, ')'):
            paren_depth -= 1
        elif paren_depth == 0 and is_keys(lst, end_pos, terminators)[1]:
            break
        end_pos += 1
    
    # Создаем временный список до терминатора и добавляем ';' для совместимости
    temp_list = lst[pos:end_pos] + [Token(name=';', value=0)]
    tree, _ = build_expression_tree(temp_list, 0)
    
    return tree, end_pos


def build_expression_tree_logic_until(lst: list[Token], pos: int, terminators: list[str]):
    """Построение дерева логического выражения до одного из терминаторов"""
    from logic_tree import build_expression_tree_logic
    
    # Находим позицию терминатора
    end_pos = pos
    paren_depth = 0
    while end_pos < len(lst):
        if is_key(lst, end_pos, '('):
            paren_depth += 1
        elif is_key(lst, end_pos, ')'):
            paren_depth -= 1
        elif paren_depth == 0 and is_keys(lst, end_pos, terminators)[1]:
            break
        end_pos += 1
    
    # Создаем временный список до терминатора
    temp_list = lst[pos:end_pos] + [Token(name=';', value=0)]
    tree, _ = build_expression_tree_logic(temp_list, 0)
    
    return tree, end_pos


def parse_statements(
    lst: list[Token],
    start_pos: int,
    end_pos: int,
    variables: dict[str, SimpleVar | ArrayVar],
    operations: list[SimpleVar | ArrayVar],
    type_aliases: dict
):
    """
    Парсинг последовательности операторов
    """
    pos = start_pos
    while pos < end_pos and not is_key(lst, pos, '}'):
        if is_key(lst, pos, 'id'):
            # Оператор присваивания
            pos = parse_assignment(lst, pos, variables, operations)
            if is_key(lst, pos, ';'):
                pos += 1
        elif is_key(lst, pos, 'for'):
            # Цикл for
            pos = parse_for_loop(lst, pos, variables, operations, type_aliases)
        elif is_key(lst, pos, ';'):
            # Пустой оператор
            pos += 1
        else:
            raise Exception(f'Unexpected token in statement: {lst[pos]}')


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

class Operations(list):
    """Список операций с автоинкрементным счетчиком"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_index = 0

    @property
    def last_index(self):
        self._last_index += 1
        return self._last_index


def symantic(tokens):
    """
    Главная функция семантического анализа
    
    Этапы:
    1. Проверка заголовка программы (prog Name;)
    2. Обработка объявлений (переменных и типов)
    3. Обработка основного блока main { }
    
    Returns:
        Список операций (промежуточный код)
    """
    # Фильтруем комментарии
    lst = [Token(name=k, value=v) for data in tokens for k, v in data.items() if k != 'com']
    
    # Проверка структуры программы
    check_key(lst, 0, 'prog')
    check_id(lst, 1)
    check_key(lst, 2, ';')
    check_count_braces(lst)
    
    pos = 3
    variables: dict[str, SimpleVar | ArrayVar] = {}
    type_aliases: dict[str, str] = {}  # Алиасы типов (type MyInt int)
    
    # ========== ОБРАБОТКА ОБЪЯВЛЕНИЙ ==========
    while not is_key(lst, pos, 'main'):
        if is_key(lst, pos, 'type'):
            # Определение типа
            pos = parse_type_definition(lst, pos, type_aliases)
        elif is_keys(lst, pos, TYPES)[1] or is_id(lst, pos):
            # Объявление переменной
            var, pos = get_var_declaration(lst, pos)
            if var.name in variables:
                raise Exception(f'Variable \'{var.name}\' already declared')
            variables[var.name] = var
        else:
            raise Exception(f'Unexpected token in declarations: {lst[pos]}')
    
    # Создаем список операций с начальными значениями переменных
    operations: Operations[SimpleVar | ArrayVar] = Operations(variables.values())
    
    # ========== ОБРАБОТКА MAIN ==========
    check_key(lst, pos, 'main')
    pos += 1
    check_key(lst, pos, '{')
    pos += 1
    
    # Находим конец main
    brace_count = 1
    main_start = pos
    temp_pos = pos
    while brace_count > 0:
        if is_key(lst, temp_pos, '{'):
            brace_count += 1
        elif is_key(lst, temp_pos, '}'):
            brace_count -= 1
        temp_pos += 1
    main_end = temp_pos - 1
    
    # Парсим тело main
    parse_statements(lst, main_start, main_end, variables, operations, type_aliases)
    
    check_key(lst, main_end, '}')
    
    return operations