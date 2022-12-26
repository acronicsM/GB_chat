"""
Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""

from ipaddress import ip_address
from subprocess import Popen, PIPE


def ping_address(address, timeout=500, requests=1):
    try:
        adr = ip_address(address)
    except ValueError:
        adr = address

    proc = Popen(f"ping {adr} -w {timeout} -n {requests}", shell=False, stdout=PIPE)
    proc.wait()

    return proc.returncode


def ping_addresses(list_ip_addresses: list, timeout=500, requests=1) -> dict:
    results = {address: ping_address(address, timeout, requests) == 0 for address in list_ip_addresses}

    return results


if __name__ == '__main__':
    ip_addresses = ['yandex.ru', '2.2.2.2', '8.8.8.8', '192.168.0.02']
    for k, v in ping_addresses(ip_addresses).items():
        print(f'{k} {"Узел доступен" if v else "Узел недоступен"}')
