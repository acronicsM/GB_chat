"""
Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate). Таблица должна состоять из двух колонок
"""

from tabulate import tabulate
from task_2 import host_range_ping


def host_range_ping_tab():
    result = dict()
    for k, v in host_range_ping().items():
        result.setdefault('Reachable' if v else 'Unreachable', []).append(k)

    print(tabulate(result, headers='keys', tablefmt="pipe", stralign="center"))


if __name__ == "__main__":
    host_range_ping_tab()

