
import argparse
from socket import *
from datetime import datetime
import json
import logging
import log.client_log_config
from log.logger_func import log_func


logger = logging.getLogger('chat.client')

HOST: str = 'localhost'
PORT: int = 8888
ACCOUNT_NAME = 'guest'


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', nargs='?', default='localhost')
    parser.add_argument('port', nargs='?', type=int, default='7777')
    return parser.parse_args()


@log_func(logger)
def connector(host: str, port: int) -> tuple:
    try:
        s = socket(AF_INET, SOCK_STREAM)  # Создать сокет TCP
        s.connect((host, port))  # Соединиться с сервером
        logger.info(f'соединение установлено: {host}:{port}')
    except ConnectionError:
        logger.error(f'ConnectionError {host}:{port}', exc_info=True)
        return None, False

    return s, True


@log_func(logger)
def decode_message(message: bytes) -> dict:

    if not message:
        logger.warning(f'Сообщение пустое: {message}')
        return {'Error': 400, 'msg': 'Пустой ответ сервера'}

    try:
        return json.loads(message.decode('utf-8'))
    except ValueError:
        logger.error(f'Ошибка json разбора: {message}')
        return {'Error': 400, 'msg': f'Ошибка разбора ответа сервера: {message}'}


@log_func(logger)
def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')



@log_func(logger)
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


@log_func(logger)
def checking_response(data: dict) -> bool:
    if 'response' not in data and data['response'] == 200:
        pass


if __name__ == "__main__":
    logger.info('Старт клиента')
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
