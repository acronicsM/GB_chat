from json import loads, dumps
from random import randint

HOST: str = 'localhost'
PORT: int = 7777
ACCOUNT_NAME = f'guest{randint(1, 99999999)}'

MAX_PACKAGE_LENGTH = 1024
ACTION = 'action'
PRESENCE = 'presence'
MESSAGE = 'message'
TIME = 'time'
MESSAGE_TEXT = 'msg'
ACC = 'ACCOUNT_NAME'
CHATID = 'chat_id'
EXIT = 'exit'
MAX_CONNECTIONS = 5


def decode_message(message: bytes) -> dict:
    if not message:
        return {'Error': 400, 'msg': 'Пустой ответ сервера'}

    try:
        return loads(message.decode('utf-8'))
    except ValueError:
        return {'Error': 400, 'msg': f'Ошибка разбора ответа сервера: {message}'}


def encode_message(message: dict) -> bytes:
    return dumps(message).encode('utf-8')
