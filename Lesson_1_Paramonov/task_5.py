"""
Задание 5.

Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
преобразовать результаты из байтовового в строковый тип на кириллице.

Подсказки:
--- используйте модуль chardet, иначе задание не засчитается!!!
"""

from subprocess import Popen, PIPE
from chardet import detect


for i in ['youtube.com', 'yandex.ru']:
    print(i)
    print('*'*20)
    ping = Popen(['ping', i], stdout=PIPE)

    for row in ping.stdout:
        result = detect(row)
        row = row.decode(result['encoding']).encode('utf-8')
        print(row.decode('utf-8'))

