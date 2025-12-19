import PySimpleGUI as sg

from synth import *
from interfaces import *
from symantic import *

filename = 'program.txt'

# LAYOUT = [
#     [
#         sg.Text('Входной файл:'),
#         sg.InputText(),
#         sg.FileBrowse('Выбор', key='browse', change_submits=True),
#         sg.Button('Загрузить', key='load_input'),
#         sg.Submit('Старт', key='start')
#     ],
#     [
#         sg.Output(size=(50, 30), key="file_input"),
#         sg.Output(size=(50, 30), key="stack_callable"),
#         sg.Output(size=(25, 30), key="stack_variable"),
#     ],
#     [
#         sg.Output(size=(134, 5))
#     ],
# ]

LAYOUT = [
    [
        sg.Text('Входной файл:'),
        sg.InputText(key='filepath', expand_x=True),
        sg.FileBrowse('Выбор', key='browse', change_submits=True),
        sg.Button('Загрузить', key='load_input'),
        sg.Submit('Старт', key='start')
    ],
    [
        sg.Multiline(
            size=(50, 30), 
            key="file_input", 
            #font=('Courier New', 10),
            expand_x=True,
            expand_y=True
        ),
        sg.Multiline(
            size=(50, 30), 
            key="stack_callable",
            #font=('Courier New', 10),
            expand_x=True,
            expand_y=True
        ),
        sg.Multiline(
            size=(25, 30), 
            key="stack_variable",
            #font=('Courier New', 10),
            expand_x=True,
            expand_y=True
        ),
    ],
    [
        sg.Multiline(
            size=(134, 5),
            key='output',
            autoscroll=True,
            expand_x=True
        )
    ],
]

DEBUG = False

def print_to_output(window, message):
    """Вывод сообщения в окно output"""
    try:
        current = window['output'].get()
        window['output'].update(current + '\n' + message)
    except:
        print(message)


def main():
    window = sg.Window(
        'Транслятор - Алексеев Дмитрий (Вариант 22)',
        LAYOUT,
        resizable=True, 
        finalize=True
    )
    
    # Переменная для хранения текста программы
    current_program_text = None
    
    while True:
        event, values = window.read()
        
        if event in (None, 'Exit', 'Cancel'):
            break
        
        if event == 'load_input':
            try:
                # Получаем путь к файлу
                filepath = values['browse']
                
                if not filepath:
                    print_to_output(window, 'Пожалуйста, выберите файл')
                    continue
                
                # Читаем файл с обработкой разных кодировок
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        current_program_text = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(filepath, 'r', encoding='cp1251') as f:
                            current_program_text = f.read()
                    except:
                        with open(filepath, 'r', encoding='latin-1') as f:
                            current_program_text = f.read()
                
                # Отображаем содержимое файла
                window['file_input'].update(current_program_text)
                window['filepath'].update(filepath)
                # print_to_output(window, f'Файл загружен: {os.path.basename(filepath)}')
                window['output'].update(f'Файл загружен: {os.path.basename(filepath)}')
                
            except FileNotFoundError:
                print_to_output(window, f'Файл не найден: {filepath}')
            except Exception as e:
                print_to_output(window, f'Ошибка при загрузке файла: {e}')
        
        if event == 'start':
            try:
                # Получаем текст программы из окна
                program_text = window['file_input'].get()
                
                if not program_text or program_text.strip() == '':
                    print_to_output(window, 'Нет программы для обработки. Загрузите файл.')
                    continue
                
                # Очищаем окна вывода
                window['stack_callable'].update('')
                window['stack_variable'].update('')
                
                # 1. Лексический анализ
                tokens = synth(program_text)
                print_to_output(window, f'Лексический анализ: {len(tokens)} токенов')
                
                # 2. Семантический анализ
                operations = symantic(tokens)
                print_to_output(window, f'Семантический анализ: {len(operations)} операций')
                
                # 3. Визуализация результатов
                stack_calls_output = stack_calls(operations)
                stack_vars_output = stack_variables(operations)
                
                window['stack_callable'].update(stack_calls_output)
                window['stack_variable'].update(stack_vars_output)
                
                print_to_output(window, 'Трансляция завершена успешно!')
                
            except Exception as e:
                print_to_output(window, f'ОШИБКА: {e}')
                import traceback
                error_details = traceback.format_exc()
                print_to_output(window, f'Подробности:\n{error_details}')
    
    window.close()


if __name__ == '__main__':
    if DEBUG:
        # без GUI
        try:
            program_text = read_file(filename)
            tokens = synth(program_text)
            operations = symantic(tokens)
            print("=== Стек вызовов ===")
            print(stack_calls(operations))
            print("\n=== Распределение памяти ===")
            print(stack_variables(operations))
        except Exception as e:
            print(f'Ошибка: {e}')
            import traceback
            traceback.print_exc()
    else:
        main()