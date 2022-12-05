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


def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')


def response_presence(message: dict) -> bytes:
    return encode_message({"response": 200, 'time': datetime.now().timestamp(),})


def response_error(error) -> bytes:
    return encode_message({"response": 400, 'time': datetime.now().timestamp(), "error": error, })


def read_message(message: bytes) -> bytes:

    if not message:
        response_error('Пустой запрос клиента')

    try:
        data = json.loads(message.decode('utf-8'))
    except ValueError:
        return response_error('Ошибка разбора запроса клиента')

    print(f'Пришло сообщение\n{data}')

    if not ('action' in data and 'time' in data):
        return response_error('Отсутсвуют обязательные параметры "action" "time"')

    if data['action'] == 'presence':
        return response_presence(data)

    return response_error('Неизвестный "action"')


def main():
    transport = socket(AF_INET, SOCK_STREAM)
    # transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    transport.bind((HOST, PORT))

    # Слушаем порт
    transport.listen(1)

    while True:
        client, addr = transport.accept()
        message_from_cient = client.recv(1024)

        response = read_message(message_from_cient)

        client.send(response)
        client.close()


if __name__ == '__main__':
    parser = createParser()
    HOST, PORT = parser.host, parser.port

    main()
