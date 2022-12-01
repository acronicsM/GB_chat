# Программа клиента для отправки приветствия серверу и получения ответа

"""
клиент отправляет запрос серверу;
сервер отвечает соответствующим кодом результата.
Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
Функции клиента:
1) сформировать presence-сообщение;
2) отправить сообщение серверу;
3) получить ответ сервера;
4) разобрать сообщение сервера;
5) параметры командной строки скрипта client.py <addr> [<port>]:
                                                                addr — ip-адрес сервера;
                                                                port — tcp-порт на сервере, по умолчанию 7777.
"""
import argparse
from socket import *
from datetime import datetime
import json
import sys

HOST: str = 'localhost'
PORT: int = 7777


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', nargs='?', default='localhost')
    parser.add_argument('port', nargs='?', type=int, default='7777')
    return parser.parse_args()


def connector(host: str, port: int) -> socket:
    s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
    s.connect((host, port))  # Соединиться с сервером

    return s


def decode_message(message: bytes) -> dict:
    return json.loads(message.decode('utf-8'))


def presence(status: str = None) -> bytes:

    message = {
        'action': 'presence',
        'time': datetime.now().timestamp(),
        'type': status,
    }

    return encode_message(message)


def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')


parser = createParser()
HOST = parser.host
PORT = parser.port

connect = connector(HOST, PORT)
connect.send(presence(status='Работаю'))
data = connect.recv(1024)

print(f'Пришло сообщение\n{decode_message(data)}')
connect.close()
