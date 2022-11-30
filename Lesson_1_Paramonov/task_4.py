"""
Задание 4.

Преобразовать слова «разработка», «администрирование», «protocol»,
«standard» из строкового представления в байтовое и выполнить
обратное преобразование (используя методы encode и decode).

Подсказки:
--- используйте списки и циклы, не дублируйте функции
"""

row_string = ['разработка', 'администрирование', 'protocol', 'standard']

for i in row_string:
    encode_el = i.encode('utf-8')
    decode_el = encode_el.decode('utf-8')
    print(f'{encode_el} - {decode_el}')