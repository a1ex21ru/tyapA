import os.path
import sys

 
# Чтение файла
def read_file(filename):
    # Открытие файла
    if not os.path.exists('program.txt'):
        print('Не удалось открыть файл', filename)
        sys.exit(-1)
    program_text = str()

    # Создание cписка символов
    with open(filename) as f:
        program_text = ' '.join(f.readlines())
        program_text = list(program_text)
    # print(program_text)
    return program_text


# Бинарный поиск по словам
def binary_find(lst, word):
    l, r = 0, len(lst)
    while l <= r:
        mid = (l + r) // 2
        if lst[mid] == word:
            return True
        elif lst[mid] < word:
            l = mid + 1
        else:
            r = mid - 1
    return False
