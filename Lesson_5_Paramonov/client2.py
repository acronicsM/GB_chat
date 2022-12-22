import argparse
import json
import logging
import threading
from datetime import datetime
from random import randint
import socket
import time
import log.server_log_config
from log.logger_func import log_func

fmt = '%Y-%m-%d %H:%M:%S'
logger = logging.getLogger('chat.client')

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

MyChats = {'84HTEde1bQS', '1'}


@log_func(logger)
def createParser():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=HOST, nargs='?')
    parser.add_argument('port', default=PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=ACCOUNT_NAME, nargs='?')
    namespace = parser.parse_args()
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name


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
def send_presence(connect_socket: socket, chat_id=None) -> None:
    for idchat in MyChats:
        if chat_id and chat_id != idchat:
            continue

        response = send_one_presence(connect_socket, idchat)

        try:
            if not decode_message(response)['response'] == 200:
                raise ConnectionRefusedError
        except Exception:
            raise ConnectionRefusedError


def send_one_presence(connect_socket: socket, chat_id: str, need_response=True):
    message = {
        ACTION: PRESENCE,
        TIME: datetime.now().timestamp(),
        'type': 'Работаю',
        ACC: ACCOUNT_NAME,
        CHATID: chat_id,
    }

    connect_socket.send(encode_message(message))

    if need_response:
        response = connect_socket.recv(1024)
        return response

    return


def send_message(sock):
    msg_text = input('Ваше сообщение: ')
    chat_id = input('Укажите id чата: ')

    if chat_id not in MyChats:
        MyChats.add(chat_id)
        send_one_presence(sock, chat_id, False)
        time.sleep(0.5)  # Ожидаем отправки сообщения

    msg = {
        ACTION: MESSAGE,
        TIME: datetime.now().timestamp(),
        MESSAGE_TEXT: msg_text,
        ACC: ACCOUNT_NAME,
        CHATID: chat_id,
    }

    sock.send(encode_message(msg))


def format_message(msg):
    return f'{datetime.utcfromtimestamp(msg[TIME]).strftime(fmt)}[{msg[ACC]}]: {msg[MESSAGE_TEXT]}'


@log_func(logger)
def get_message(sock):
    """
    Утилита приёма и декодирования сообщения принимает байты, выдаёт словарь,
    если принято что-то другое отдаёт ошибку значения
    :param sock:
    :return:
    """
    response = sock.recv(MAX_PACKAGE_LENGTH)
    if isinstance(response, bytes):
        response = decode_message(response)
        if isinstance(response, dict):
            return response

    return None


@log_func(logger)
def message_from_server(sock):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    while True:
        try:
            message = get_message(sock)
            is_message = ACTION in message and message[ACTION] == MESSAGE
            is_presence = 'response' in message and message['response'] == 200
            is_my_chat = CHATID in message and message[CHATID] in MyChats
            if is_message and is_my_chat:
                print(f_msg := format_message(message))
                logger.info(f_msg)
            elif is_presence:
                pass  # ничего не делаем
            else:
                logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            logger.critical(f'Потеряно соединение с сервером.')
            break


@log_func(logger)
def send_exit_message(sock, account_name):
    """Функция создаёт словарь с сообщением о выходе"""
    msg = {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }

    sock.send(encode_message(msg))


def print_help():
    """Функция выводящая справку по использованию"""
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Кому и текст будет запрошены отдельно. ')
    print('help - вывести подсказки по командам')
    print('exit - выход из программы')


@log_func(logger)
def user_interactive(sock):
    """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            send_message(sock)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_exit_message(sock, ACCOUNT_NAME)
            print('Завершение соединения.')
            logger.info('Завершение работы по команде пользователя.')
            time.sleep(0.5)  # Задержка необходима, чтобы успело уйти сообщение о выходе
            break
        else:
            print('Команда не распознана, попробуйте снова. help - вывести поддерживаемые команды.')


def start_client():
    logger.info('Старт клиента')

    host, port, name = createParser()

    print(name)

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((host, port))
        send_presence(transport)
    except ConnectionRefusedError:
        logger.error(f'Ошибка установки соединения с сервером {host}:{port}')
        return

    logger.info(f'Установлено соединение с сервером {host}:{port}')

    # Если соединение с сервером установлено корректно, запускаем клиентский процесс приёма сообщений
    receiver = threading.Thread(target=message_from_server, args=(transport,))
    receiver.daemon = True
    receiver.start()

    # затем запускаем отправку сообщений и взаимодействие с пользователем.
    user_interface = threading.Thread(target=user_interactive, args=(transport,))
    user_interface.daemon = True
    user_interface.start()

    logger.debug('Запущены процессы')

    # Watchdog основной цикл
    # если один из потоков завершён, то значит или потеряно соединение, или пользователь ввёл exit.
    # Поскольку все события обрабатываются в потоках, достаточно просто завершить цикл.
    while True:
        time.sleep(1)
        if receiver.is_alive() and user_interface.is_alive():
            continue
        break


if __name__ == "__main__":
    start_client()
