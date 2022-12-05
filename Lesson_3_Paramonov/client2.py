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

HOST: str = 'localhost'
PORT: int = 8888
ACCOUNT_NAME = 'guest'


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', nargs='?', default='localhost')
    parser.add_argument('port', nargs='?', type=int, default='7777')
    return parser.parse_args()


def connector(host: str, port: int) -> tuple:
    try:
        s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
        s.connect((host, port))  # Соединиться с сервером
    except ConnectionError:
        return None, False

    return s, True


def decode_message(message: bytes) -> dict:

    if not message:
        return {'Error': 400, 'msg': 'Пустой ответ сервера'}

    try:
        return json.loads(message.decode('utf-8'))
    except ValueError:
        return {'Error': 400, 'msg': f'Ошибка разбора ответа сервера: {message}'}


def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')


def send_presence(connect_socket: socket) -> bytes:
    message = {
        'action': 'presence',
        'time': datetime.now().timestamp(),
        'type': 'Работаю',
        'USER': {
            'ACCOUNT_NAME': ACCOUNT_NAME
        }
    }

    message_text = encode_message(message)

    connect_socket.send(message_text)

    return connect_socket.recv(1024)


def checking_response(data: dict) -> bool:
    if 'response' not in data\
            and data['response'] == 200:
        pass


if __name__ == "__main__":
    parser = createParser()
    HOST = parser.host
    PORT = parser.port

    connect = connector(HOST, PORT)
    if connect[1]:
        connect = connect[0]
    else:
        exit('ошибка подключения к серверу')

    response = send_presence(connect)

    data = decode_message(response)
    connect.close()

    print(f'Пришло сообщение\n{data}')
