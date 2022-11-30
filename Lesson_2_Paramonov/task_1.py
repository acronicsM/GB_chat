# 1. Задание на закрепление знаний по модулю CSV.
# Написать скрипт, осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt, info_3.txt
# и формирующий новый «отчетный» файл в формате CSV.
# Для этого:
# 1) Создать функцию get_data(), в которой в цикле осуществляется перебор файлов, их открытие и считывание данных.
#   В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров
#   «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
#   Значения каждого параметра поместить в соответствующий список.
#   Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list, os_type_list.
#   В этой же функции создать главный список для хранения данных отчета — например,
#   main_data — и поместить в него названия столбцов отчета в виде списка:
#   «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
#   Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла);
#
# 2) Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
#   В этой функции реализовать получение данных через вызов функции get_data(),
#   а также сохранение подготовленных данных в соответствующий CSV-файл;
#
# 3) Проверить работу программы через вызов функции write_to_csv().


from re import finditer
from chardet import detect
from csv import writer as csv_writer


def get_data(param: list, *args):
    if isinstance(param, str):
        param = [param]

    params = {i: [] for i in param}
    pattern = rf'({"|".join(param)}).*\n'

    for i in args:
        with open(i, mode='rb') as file:
            text = file.read()

        text = text.decode(detect(text)['encoding'])
        for match in finditer(pattern, text):
            key, value = map(str.strip, match.group().split(':'))
            params[key].append(value)

    main_data = [param] + [list(i) for i in zip(*params.values())]

    return main_data


def write_to_csv(file_name):
    parameters = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    files = ('info_1.txt', 'info_2.txt', 'info_3.txt')

    data = get_data(parameters, *files)

    with open(file_name, 'w') as f_csv:
        csv_writer(f_csv).writerows(data)


if __name__ == "__main__":
    write_to_csv('new_file.csv')
