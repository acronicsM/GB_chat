import argparse
import logging
import threading
from datetime import datetime
from random import randint
import socket
import time
from json import JSONDecodeError
import log.server_log_config
from log.logger_func import log_func
from common.utils import *
from meta import ClientVerifier

fmt = '%Y-%m-%d %H:%M:%S'
logger = logging.getLogger('chat.client')
ACCOUNT_NAME = f'guest{randint(1, 99999999)}'
MYCHATS = {'84HTEde1bQS', '1'}


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def send_exit_message(self):
        msg = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

        self.sock.send(encode_message(msg))

    def send_message(self):
        msg_text = input('Ваше сообщение: ')
        chat_id = input('Укажите id чата: ')

        if chat_id not in MYCHATS:
            MYCHATS.add(chat_id)
            send_one_presence(self.sock, chat_id, False)
            time.sleep(0.5)  # Ожидаем отправки сообщения

        msg = {
            ACTION: MESSAGE,
            TIME: datetime.now().timestamp(),
            MESSAGE_TEXT: msg_text,
            ACC: ACCOUNT_NAME,
            CHATID: chat_id,
        }

        self.sock.send(encode_message(msg))

    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
    def run(self):
        print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'm':
                self.send_message()
            elif command == 'h':
                print_help()
            elif command == 'e':
                try:
                    self.send_exit_message()
                except:
                    pass
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)  # Задержка необходима, чтобы успело уйти сообщение о выходе
                break
            else:
                print('Команда не распознана, попробуйте снова. help - вывести поддерживаемые команды.')


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = self.get_message()
                is_message = ACTION in message and message[ACTION] == MESSAGE
                is_presence = 'response' in message and message['response'] == 200
                is_my_chat = CHATID in message and message[CHATID] in MYCHATS
                if is_message and is_my_chat:
                    print(f_msg := format_message(message))
                    logger.info(f_msg)
                elif is_presence:
                    pass  # ничего не делаем
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, JSONDecodeError):
                logger.critical(f'Потеряно соединение с сервером.')
                break

    def get_message(self):
        response = self.sock.recv(MAX_PACKAGE_LENGTH)
        if isinstance(response, bytes):
            response = decode_message(response)
            if isinstance(response, dict):
                return response

        return None


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


def print_help():
    print('Поддерживаемые команды:')
    print('m - отправить сообщение. Кому и текст будет запрошены отдельно.')
    print('h - вывести подсказки по командам')
    print('e - выход из программы')


def format_message(msg):
    return f'{datetime.utcfromtimestamp(msg[TIME]).strftime(fmt)}[{msg[ACC]}]: {msg[MESSAGE_TEXT]}'


def send_presence(sock, chat_id=None) -> None:
    for i in MYCHATS:
        if chat_id and chat_id != i:
            continue

        response = send_one_presence(sock, i)

        try:
            if not decode_message(response)['response'] == 200:
                raise ConnectionRefusedError
        except Exception:
            raise ConnectionRefusedError


def send_one_presence(sock, chat_id: str, need_response=True):
    message = {
        ACTION: PRESENCE,
        TIME: time.time(),
        ACC: ACCOUNT_NAME,
        CHATID: chat_id,
    }

    sock.send(encode_message(message))

    if need_response:
        response = sock.recv(1024)
        return response

    return


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
    receiver = ClientReader(name, transport)
    receiver.daemon = True
    receiver.start()

    # затем запускаем отправку сообщений и взаимодействие с пользователем.
    user_interface = ClientSender(name, transport)
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
