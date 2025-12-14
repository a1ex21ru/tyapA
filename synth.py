from utils import *
from data import *


def synth(program_text):
    """
    Лексический анализатор для языка с синтаксисом:
    - prog (вместо program)
    - int x; (вместо var x int;)
    - Поддержка // и /* */ комментариев
    - for (init; cond; incr) { }
    """
    key_words.sort()
    state = 0
    pos = 0
    identifier = ''
    digit = ''
    out_buffer = list()
    
    while pos < len(program_text):
        if state == 0:
            if program_text[pos] == '<':
                state = 1
            elif program_text[pos] == '>':
                state = 2
            elif program_text[pos] == '=':
                state = 11
            elif program_text[pos] == '!':
                state = 12
            elif program_text[pos] == ';':
                out_buffer.append({';': 0})
            elif program_text[pos] == ',':
                out_buffer.append({',': 0})
            elif program_text[pos] == '.':
                out_buffer.append({'.': 0})
            elif program_text[pos] == '[':
                out_buffer.append({'[': 0})
            elif program_text[pos] == ']':
                out_buffer.append({']': 0})
            elif program_text[pos] == '{':
                out_buffer.append({'{': 0})
            elif program_text[pos] == '}':
                out_buffer.append({'}': 0})
            elif program_text[pos] == '(':
                out_buffer.append({'(': 0})
            elif program_text[pos] == ')':
                out_buffer.append({')': 0})
            elif program_text[pos] == '*':
                out_buffer.append({'*': 1})
            elif program_text[pos] == '/':
                state = 3
            elif program_text[pos] == '&':
                state = 7
            elif program_text[pos] == '|':
                state = 8
            elif program_text[pos] == '+':
                out_buffer.append({'+': 1})
            elif program_text[pos] == '-':
                out_buffer.append({'+': 2})
            elif program_text[pos].isalpha():
                identifier += program_text[pos]
                state = 6
            elif program_text[pos].isdigit():
                digit += program_text[pos]
                state = 10
                
        elif state == 1:  # Состояние после '<'
            if program_text[pos] == '=':
                out_buffer.append({'rel': 2})  # <=
            else:
                out_buffer.append({'rel': 1})  # <
                pos -= 1
            state = 0
            
        elif state == 2:  # Состояние после '>'
            if program_text[pos] == '=':
                out_buffer.append({'rel': 4})  # >=
            else:
                out_buffer.append({'rel': 3})  # >
                pos -= 1
            state = 0
            
        elif state == 3:  # Состояние после '/'
            if program_text[pos] == '*':
                state = 4  # Начало многострочного комментария /* */
            elif program_text[pos] == '/':
                state = 18  # Начало однострочного комментария //
            else:
                out_buffer.append({'*': 2})  # Деление
                pos -= 1
                state = 0
                
        elif state == 4:  # Внутри многострочного комментария
            if program_text[pos] == '*':
                state = 5
                
        elif state == 5:  # После '*' внутри комментария
            if program_text[pos] == '/':
                out_buffer.append({'com': 0})
                state = 0
            else:
                state = 4
                
        elif state == 6:  # Идентификаторы и ключевые слова
            if program_text[pos].isalpha() or program_text[pos].isdigit():
                identifier += program_text[pos]
            else:
                if binary_find(key_words, identifier):
                    out_buffer.append({identifier: 0})
                else:
                    out_buffer.append({'id': identifier})
                pos -= 1
                identifier = ''
                state = 0
                
        elif state == 7:  # Состояние после '&'
            if program_text[pos] == '&':
                out_buffer.append({'and': 0})
                state = 0
            else:
                print('Ошибка в автомате &&!')
                exit(-1)
                
        elif state == 8:  # Состояние после '|'
            if program_text[pos] == '|':
                out_buffer.append({'or': 0})
                state = 0
            else:
                print('Ошибка в автомате ||!')
                exit(-1)
                
        elif state == 10:  # Целая часть числа
            if program_text[pos].isdigit():
                digit += program_text[pos]
            elif program_text[pos] == '.':
                digit += program_text[pos]
                state = 13
            elif program_text[pos] == 'e':
                digit += program_text[pos]
                state = 15
            else:
                out_buffer.append({'num': digit})
                pos -= 1
                digit = ''
                state = 0
                
        elif state == 11:  # Состояние после '='
            if program_text[pos] == '=':
                out_buffer.append({'rel': 5})  # ==
            else:
                out_buffer.append({'ass': 0})  # =
                pos -= 1
            state = 0
            
        elif state == 12:  # Состояние после '!'
            if program_text[pos] == '=':
                out_buffer.append({'rel': 6})  # !=
                state = 0
            else:
                pos -= 1
                state = 0
                out_buffer.append({'not': 0})  # !
                
        elif state == 13:  # После точки в числе
            if program_text[pos].isdigit():
                digit += program_text[pos]
                state = 14
            else:
                print('Ошибка в автомате чисел! (Состояние 13)')
                exit(-1)
                
        elif state == 14:  # Дробная часть числа
            if program_text[pos].isdigit():
                digit += program_text[pos]
            elif program_text[pos] == 'e':
                digit += program_text[pos]
                state = 15
            else:
                out_buffer.append({'num': digit})
                pos -= 1
                digit = ''
                state = 0
                
        elif state == 15:  # После 'e' в научной нотации
            if program_text[pos].isdigit():
                digit += program_text[pos]
                state = 17
            elif program_text[pos] == '+' or program_text[pos] == '-':
                digit += program_text[pos]
                state = 16
            else:
                print('Ошибка в автомате чисел! (Состояние 15)')
                exit(-1)
                
        elif state == 16:  # После знака в экспоненте
            if program_text[pos].isdigit():
                digit += program_text[pos]
                state = 17
            else:
                print('Ошибка в автомате чисел! (Состояние 16)')
                exit(-1)
                
        elif state == 17:  # Экспонента числа
            if program_text[pos].isdigit():
                digit += program_text[pos]
            else:
                out_buffer.append({'num': digit})
                pos -= 1
                digit = ''
                state = 0
                
        elif state == 18:  # Однострочный комментарий //
            if program_text[pos] == '\n':
                out_buffer.append({'com': 0})
                state = 0
            # Продолжаем читать до конца строки
            
        pos += 1

    return out_buffer