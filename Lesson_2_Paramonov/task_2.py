# ### 2. Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах.
#  Написать скрипт, автоматизирующий его заполнение данными.
# Для этого:
# 1) Создать функцию write_order_to_json(), в которую передается 5 параметров —
#   товар (item), количество (quantity), цена (price), покупатель (buyer), дата (date).
#   Функция должна предусматривать запись данных в виде словаря в файл orders.json.
#   При записи данных указать величину отступа в 4 пробельных символа;
#
# 2) Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра.

import json


def write_order_to_json(item, quantity, price, buyer, date):
    with open('orders.json') as file:
        data = json.load(file)

    data['orders'].append({
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date,
    })

    with open('orders.json', mode='w') as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    write_order_to_json('item', 1, 102, 'buyer', 'date')
    write_order_to_json('item1', 1, 102, 'buyer', 'date')
    write_order_to_json('item2', 1, 102, 'buyer', 'date')
    write_order_to_json('item3', 1, 102, 'buyer', 'date')