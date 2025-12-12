from utils import *
from data import *


def synth(program_text):
    key_words.sort()
    sost = 0
    pos = 0
    identifier = ''
    digit = ''
    out_buffer = list()
    while pos < len(program_text):
        if sost == 0:
            if program_text[pos] == '<':
                sost = 1
            elif program_text[pos] == '>':
                sost = 2
            elif program_text[pos] == '=':
                sost = 11
            elif program_text[pos] == '!':
                sost = 12
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
                sost = 3
            elif program_text[pos] == '&':
                sost = 7
            elif program_text[pos] == '|':
                sost = 8
            elif program_text[pos] == '+':
                out_buffer.append({'+': 1})
            elif program_text[pos] == '-':
                out_buffer.append({'+': 2})
            elif program_text[pos].isalpha():
                identifier += program_text[pos]
                sost = 6
            elif program_text[pos].isdigit():
                digit += program_text[pos]
                sost = 10
        elif sost == 1:
            if program_text[pos] == '=':
                out_buffer.append({'rel': 2})
            else:
                out_buffer.append({'rel': 1})
                pos -= 1
            sost = 0
        elif sost == 2:
            if program_text[pos] == '=':
                out_buffer.append({'rel': 4})
            else:
                out_buffer.append({'rel': 3})
                pos -= 1
            sost = 0
        elif sost == 3:
            if program_text[pos] == '*':
                sost = 4
            else:
                out_buffer.append({'*': 2})
                sost = 0
        elif sost == 4:
            if program_text[pos] == '*':
                sost = 5
        elif sost == 5:
            if program_text[pos] == '/':
                out_buffer.append({'com': 0})
                sost = 0
            else:
                sost = 4
        elif sost == 6:
            if program_text[pos].isalpha() or program_text[pos].isdigit():
                identifier += program_text[pos]
            else:
                if binary_find(key_words, identifier):
                    out_buffer.append({identifier: 0})
                else:
                    out_buffer.append({'id': identifier})
                pos -= 1
                identifier = ''
                sost = 0
        elif sost == 7:
            if program_text[pos] == '&':
                out_buffer.append({'and': 0})
                sost = 0
            else:
                print('Ошибка в автомате &&!')
                exit(-1)
        elif sost == 8:
            if program_text[pos] == '|':
                out_buffer.append({'or': 0})
                sost = 0
            else:
                print('Ошибка в автомате ||!')
                exit(-1)
        elif sost == 10:
            if program_text[pos].isdigit():
                digit += program_text[pos]
            elif program_text[pos] == '.':
                digit += program_text[pos]
                sost = 13
            elif program_text[pos] == 'e':
                digit += program_text[pos]
                sost = 15
            else:
                out_buffer.append({'num': digit})
                pos -= 1
                digit = ''
                sost = 0
        elif sost == 11:
            if program_text[pos] == '=':
                out_buffer.append({'rel': 5})
            else:
                out_buffer.append({'ass': 0})
                pos -= 1
            sost = 0
        elif sost == 12:
            if program_text[pos] == '=':
                out_buffer.append({'rel': 6})
                sost = 0
            else:
                pos -= 1
                sost = 0
                out_buffer.append({'not': 0})
        elif sost == 13:
            if program_text[pos].isdigit():
                digit += program_text[pos]
                sost = 14
            else:
                print('Ошибка в автомате чисел! (Состояние 13)')
                exit(-1)
        elif sost == 14:
            if program_text[pos].isdigit():
                digit += program_text[pos]
            elif program_text[pos] == 'e':
                digit += program_text[pos]
                sost = 15
            else:
                out_buffer.append({'num': digit})
                pos -= 1
                digit = ''
                sost = 0
        elif sost == 15:
            if program_text[pos].isdigit():
                digit += program_text[pos]
                sost = 17
            elif program_text[pos] == '+' or program_text[pos] == '-':
                digit += program_text[pos]
                sost = 16
            else:
                print('Ошибка в автомате чисел! (Состояние 15)')
                exit(-1)
        elif sost == 16:
            if program_text[pos].isdigit():
                digit += program_text[pos]
                sost = 17
            else:
                print('Ошибка в автомате чисел! (Состояние 16)')
                exit(-1)
        elif sost == 17:
            if program_text[pos].isdigit():
                digit += program_text[pos]
            else:
                out_buffer.append({'num': digit})
                pos -= 1
                digit = ''
                sost = 0
        else:
            pass
        pos += 1

    return out_buffer
