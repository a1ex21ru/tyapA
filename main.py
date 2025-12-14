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
    while True:
        event, values = window.read()
        if event == 'load_input':
            try:
                program_text = read_file(values['browse'])
                window['file_input'].update(''.join(program_text))
            except Exception as e:
                print(e)
        if event == 'start':
            try:
                tokens = synth(window['file_input'].get())
                operations = symantic(tokens)
                window['stack_variable'].update(stack_variables(operations))
                window['stack_callable'].update(stack_calls(operations))
            except Exception as e:
                print(e)
        if event in (None, 'Exit', 'Cancel'):
            break


if __name__ == '__main__':
    if DEBUG:
        program_text = read_file(filename)
        tokens = synth(program_text)
        operations = symantic(tokens)
        # print(stack_calls(operations))
        # print(stack_variables(operations))
    else:
        main()
