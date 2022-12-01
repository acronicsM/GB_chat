# Программа сервера для получения приветствия от клиента и отправки ответа

"""
клиент отправляет запрос серверу;
сервер отвечает соответствующим кодом результата.
Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
Функции сервера:
1) принимает сообщение клиента;
2) формирует ответ клиенту;
3) отправляет ответ клиенту;
4) имеет параметры командной строки:
                                    -p <port> — TCP-порт для работы (по умолчанию использует 7777);
                                    -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import argparse
from socket import *
from datetime import datetime
import json

HOST: str = 'localhost'
PORT: int = 7777

def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', nargs='?', default='localhost')
    parser.add_argument('port', nargs='?', type=int, default='7777')
    return parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)  # Создает сокет TCP
s.bind((HOST, PORT))  # Присваивает порт 8888
s.listen(5)  # Переходит в режим ожидания запросов; Одновременно обслуживает не более; 5 запросов.


def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')


def response_presence(message: dict) -> bytes:
    response =  {
        "response": 200,
        'time': datetime.now().timestamp(),
    }

    return encode_message(response)


def response_error() -> bytes:
    response = {
        "response": 400,
        'time': datetime.now().timestamp(),
        "error": "Wrong action, try again",
    }
    return encode_message(response)


def read_message(message: bytes) -> bytes:
    data = json.loads(message.decode('utf-8'))

    print(f'Пришло сообщение\n{data}')

    if not ('action' in data and 'time' in data):
        return response_error()

    if data['action'] == 'presence':
        return response_presence(data)


parser = createParser()
HOST = parser.host
PORT = parser.port

while True:
    client, addr = s.accept()
    data = client.recv(1000000)
    client.send( read_message(data))
    client.close()
