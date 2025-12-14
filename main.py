import PySimpleGUI as sg

from synth import *
from interfaces import *
from symantic import *

filename = 'program.txt'

LAYOUT = [
    [
        sg.Text('Входной файл:'),
        sg.InputText(),
        sg.FileBrowse('Выбор', key='browse', change_submits=True),
        sg.Button('Загрузить', key='load_input'),
        sg.Submit('Старт', key='start')
    ],
    [
        sg.Output(size=(50, 30), key="file_input"),
        sg.Output(size=(50, 30), key="stack_callable"),
        sg.Output(size=(25, 30), key="stack_variable"),
    ],
    [
        sg.Output(size=(134, 5))
    ],
]

DEBUG = False 


def main():
    window = sg.Window('Алексеев Дмитрий ИВТ-41-22', LAYOUT)
    
    # Переменная для хранения текста программы
    current_program_text = None
    
    while True:
        event, values = window.read()
        
        if event in (None, 'Exit', 'Cancel'):
            break
        
        if event == 'load_input':
            try:
                
                filepath = values['browse']
                if not filepath:
                    print('Пожалуйста, выберите файл')
                    continue
                
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

                window['file_input'].update(current_program_text)
                print(f'Файл загружен: {filepath}')
                
            except FileNotFoundError:
                print(f'Файл не найден: {filepath}')
            except Exception as e:
                print(f'Ошибка при загрузке файла: {e}')
        
        if event == 'start':
            try:
                program_text = window['file_input'].get()
                
                if not program_text or program_text.strip() == '':
                    print('Нет программы для обработки. Загрузите файл.')
                    continue
                
                window['stack_callable'].update('')
                window['stack_variable'].update('')
                
                print('Начало трансляции...')

                # 1. Лексический анализ
                tokens = synth(program_text)
                print(f'Лексический анализ: {len(tokens)} токенов')
                
                # 2. Семантический анализ
                operations = symantic(tokens)
                print(f'Семантический анализ: {len(operations)} операций')
                
                # 3. Визуализация результатов
                stack_calls_output = stack_calls(operations)
                stack_vars_output = stack_variables(operations)
                
                window['stack_callable'].update(stack_calls_output)
                window['stack_variable'].update(stack_vars_output)
                
                print('Трансляция завершена успешно!')
                
            except Exception as e:
                print(f'Ошибка: {e}')
                import traceback
                traceback.print_exc()
    
    window.close()


if __name__ == '__main__':
    if DEBUG:
        # Режим отладки без GUI
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
        # Режим с GUI
        main()