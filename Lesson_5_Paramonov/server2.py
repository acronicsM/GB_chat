import argparse
from socket import *
from datetime import datetime
import json
import logging
import log.server_log_config
from log.logger_func import log_func

logger = logging.getLogger('chat.server')

HOST: str = 'localhost'
PORT: int = 7777


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', nargs='?', default='localhost')
    parser.add_argument('port', nargs='?', type=int, default='7777')
    return parser.parse_args()


@log_func(logger)
def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')


@log_func(logger)
def response_presence(message: dict) -> bytes:
    return encode_message({"response": 200, 'time': datetime.now().timestamp(), })


@log_func(logger)
def response_error(error) -> bytes:
    return encode_message({"response": 400, 'time': datetime.now().timestamp(), "error": error, })


@log_func(logger)
def read_message(message: bytes) -> bytes:
    logger.info(f'Чтение сообщения: {message}')

    if not message:
        response_error('Пустой запрос клиента')

    try:
        data = json.loads(message.decode('utf-8'))
    except ValueError:
        logger.error(f'Ошибка json разбора: {message}')
        return response_error('Ошибка разбора запроса клиента')

    print(f'Пришло сообщение\n{data}')

    if not ('action' in data and 'time' in data):
        logger.warning(f'Неверный формат сообщения: {message}')
        return response_error('Отсутсвуют обязательные параметры "action" "time"')

    if data['action'] == 'presence':
        return response_presence(data)

    logger.warning(f'Неизвестная команда: {data["action"]}')
    return response_error('Неизвестный "action"')


@log_func(logger)
def main():
    logger.info(f'Старт сервера')
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
