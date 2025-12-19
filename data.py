import dataclasses
import typing
from enum import StrEnum
from collections import defaultdict

nested_dict = lambda: defaultdict(nested_dict)

TYPES = [
    'int',
    'float',
    'bool',
]

# Ключевые слова языка
key_words = [
    'prog',     # Изменено с 'program' на 'prog'
    'main',
    'type',
    'for',      # Добавлен для цикла for
    'while',    # Оставлен для совместимости
    'true',
    'false',
    '&&',
    '||',
    '!',
    *TYPES,
]


class Type:
    pass


def parse_value(var_type, value):
    """
    Парсинг значения в соответствии с типом
    ИСПРАВЛЕНО: корректная обработка как строк, так и чисел
    """
    match var_type:
        case 'int':
            # Может быть строка или уже int
            if isinstance(value, str):
                return int(float(value)), 'int'  # Через float для "5.0" -> 5
            else:
                return int(value), 'int'
        case 'float':  
            # Может быть строка или уже float/int
            if isinstance(value, str):
                return float(value), 'float'
            else:
                return float(value), 'float'
        case 'bool':
            # Может быть строка "true"/"false" или bool
            if isinstance(value, str):
                return value.lower() == 'true', 'bool'
            else:
                return bool(value), 'bool'
        case _:
            raise Exception(f'Cannot parse value \'{value}\' in type \'{var_type}\'')


@dataclasses.dataclass
class SimpleVar:
    """
    Простая переменная (скаляр)
    
    Attributes:
        name: имя переменной
        type: тип данных (int, float, bool)
        value: текущее значение
        addr: адрес в памяти (для визуализации)
    """
    name: str
    type: str
    value: any
    addr: int = 0

    def set_value(self, value):
        """Установка значения с приведением типа"""
        self.value, _ = parse_value(self.type, value)


@dataclasses.dataclass
class ArrayVar:
    """
    Массив (одномерный)
    
    Attributes:
        name: имя массива
        type: тип элементов (int, float, bool)
        size: размер массива
        values: словарь значений с индексами
        addr: адрес в памяти
    """
    name: str
    type: str
    size: int
    values: defaultdict = dataclasses.field(default_factory=nested_dict)
    addr: int = 0

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def set_value(self, index, value):
        """
        Установка значения элемента массива
        
        Args:
            index: индекс элемента (целое число)
            value: значение для установки
        """
        if not isinstance(index, int):
            raise TypeError(f"Array index must be int, not {type(index)}")
        if index < 0 or index >= self.size:
            raise IndexError(f"Array index {index} out of range [0, {self.size})")
        self.values[index], _ = parse_value(self.type, value)

    def get_value(self, index):
        """
        Получение значения элемента массива
        
        Args:
            index: индекс элемента
            
        Returns:
            Значение элемента или None если не инициализирован
        """
        if not isinstance(index, int):
            raise TypeError(f"Array index must be int, not {type(index)}")
        if index < 0 or index >= self.size:
            raise IndexError(f"Array index {index} out of range [0, {self.size})")
        return self.values.get(index)


@dataclasses.dataclass
class Token:
    """
    Токен (лексема)
    
    Attributes:
        name: тип токена (id, num, prog, main, и т.д.)
        value: значение токена
    """
    name: str
    value: any

    def __str__(self):
        return f'("{self.name}": {self.value})'

    def __repr__(self):
        return f'("{self.name}": {self.value})'


# Константы размеров типов в байтах
SIZES = {
    'int': 4,
    'float': 8,
    'bool': 1,
}


# Коды операций
class OpCode:
    """Коды операций для промежуточного кода"""
    ADD = 'add'
    SUB = 'sub'
    MULT = 'mult'
    DIV = 'div'
    ASS = 'ass'
    AND = 'and'
    OR = 'or'
    NOT = 'not'
    LT = 'lt'      # <
    LE = 'le'      # <=
    GT = 'gt'      # >
    GE = 'ge'      # >=
    EQ = 'eq'      # ==
    NE = 'ne'      # !=
    GOTO = 'goto'
    IF_GOTO = 'if_goto'
    LABEL = 'label'


# Категории идентификаторов
class Category:
    """Категории идентификаторов в таблице символов"""
    VAR = 'var'           # Переменная
    CONST = 'const'       # Константа
    TYPE = 'type'         # Определение типа
    TEMP = 'temp'         # Временная переменная


@dataclasses.dataclass
class ForLoopContext:
    """
    Контекст цикла for для отслеживания переменных
    
    Attributes:
        loop_var: переменная-счетчик цикла
        start_label: метка начала цикла
        end_label: метка конца цикла
    """
    loop_var: SimpleVar
    start_label: str
    end_label: str