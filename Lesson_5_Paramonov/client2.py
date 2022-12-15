from socket import *
from select import select
from datetime import datetime
import json, logging, argparse
import log.client_log_config
from log.logger_func import log_func
from random import randint

fmt = '%Y-%m-%d %H:%M:%S'
logger = logging.getLogger('chat.client')

HOST: str = 'localhost'
PORT: int = 7777
ACCOUNT_NAME = f'guest{randint(1, 99999999)}'


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
def send_presence(connect_socket: socket) -> bool:
    message = {
        'action': 'presence',
        'time': datetime.now().timestamp(),
        'type': 'Работаю',
        'USER': {
            'ACCOUNT_NAME': ACCOUNT_NAME
        }
    }

    connect_socket.send(encode_message(message))

    response = connect_socket.recv(1024)
    is200 = False
    try:
        is200 = decode_message(response)['response'] == 200
    except:
        pass

    if not is200:
        logger.warning(f'Ошибка приветсвия {response}')

    return is200


def send_message(sock):
    msg = {
        'action': 'message',
        'time': datetime.now().timestamp(),
        'msg': input('Ваше сообщение: '),
        'USER': {
            'ACCOUNT_NAME': ACCOUNT_NAME,
            'chat_id': 1,
        }
    }

    sock.send(encode_message(msg))  # Отправить!

    response = sock.recv(1024)
    response = decode_message(response)
    is200 = False
    try:
        is200 = response['response'] == 200
    except:
        pass

    if not is200:
        logger.info(f'сообщение не доставлено {response}')
        return

    print('[СИСТЕМА]: сообщение доставлено')

    for i in response['new_msg']:
        print(f'{datetime.utcfromtimestamp(i["time"]).strftime(fmt)}[{i["acc"]}]: {i["msg"]}')







def start_client():
    logger.info('Старт клиента')

    parser = createParser()

    with socket(AF_INET, SOCK_STREAM) as sock: # Создать сокет TCP
        try:
            sock.connect((parser.host, parser.port)) # Соединиться с сервером
            logger.info(f'Установлено соединение с сервером {parser.host}:{parser.port}')
        except ConnectionRefusedError:
            logger.error(f'Ошибка установки соединения с сервером {parser.host}:{parser.port}')
            return

        # Приветсвие
        if not send_presence(sock):
            logger.error(f'Ошибка установки соединения с сервером {parser.host}:{parser.port}')
            return

        while True:
           send_message(sock)


if __name__ == "__main__":
    start_client()

