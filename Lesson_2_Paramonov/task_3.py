### 3. Задание на закрепление знаний по модулю yaml. Написать скрипт,
# автоматизирующий сохранение данных в файле YAML-формата.
# Для этого:
# 1) Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список,
#   второму — целое число, третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом,
#   отсутствующим в кодировке ASCII (например, €);
#
# 2) Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
#   При этом обеспечить стилизацию файла с помощью параметра default_flow_style,
#   а также установить возможность работы с юникодом: allow_unicode = True;
# 3) Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.

import yaml


def write_to_yaml(file, data):
    with open(file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def read_yaml(file):
    with open(file) as f:
        read_data = yaml.load(f, Loader=yaml.FullLoader)

    return read_data


if __name__ == "__main__":
    d = {
        '1€': [1, '2', 'dsd'],
        '2€': 8,
        '3€': {'temp1': 1},
    }

    file_name = 'test.yaml'
    write_to_yaml(file_name, d)

    data_file = read_yaml(file_name)

    if data_file != d:
        print('данные не совпадают')
    else:
        print('данные совпадают')
