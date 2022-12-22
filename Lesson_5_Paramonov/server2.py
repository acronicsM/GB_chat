import argparse
import json
import logging
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM

from select import select

import log.server_log_config
from log.logger_func import log_func

logger = logging.getLogger('chat.server')

HOST: str = 'localhost'
PORT: int = 7777
MAX_CONNECTIONS = 5

MAX_PACKAGE_LENGTH = 1024
ACTION = 'action'
PRESENCE = 'presence'
MESSAGE = 'message'
TIME = 'time'
MESSAGE_TEXT = 'msg'
ACC = 'ACCOUNT_NAME'
CHATID = 'chat_id'
EXIT = 'exit'


@log_func(logger)
def arg_parser():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=PORT, type=int, nargs='?')
    parser.add_argument('-a', default=HOST, nargs='?')
    namespace = parser.parse_args()
    listen_address = namespace.a
    listen_port = namespace.p

    # проверка получения корректного номера порта для работы сервера.
    if not 1023 < listen_port < 65536:
        logger.critical(
            f'Попытка запуска сервера с указанием неподходящего порта {listen_port}. '
            f'Допустимы адреса с 1024 до 65535.')
        exit(1)

    return listen_address, listen_port


@log_func(logger)
def encode_message(message: dict) -> bytes:
    return json.dumps(message).encode('utf-8')


@log_func(logger)
def response_presence() -> bytes:
    return encode_message({"response": 200, 'time': datetime.now().timestamp(), })


@log_func(logger)
def response_error(error) -> bytes:
    return encode_message({"response": 400, 'time': datetime.now().timestamp(), "error": error, })


def read_requests(r_clients, all_clients):
    """
    Чтение запросов из списка клиентов
    """
    responses = {}  # Словарь ответов сервера вида {сокет: запрос}
    for sock in r_clients:
        try:
            data = sock.recv(1024).decode('utf-8')
            responses[sock] = data
        except Exception:
            print('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
            all_clients.remove(sock)
    return responses


@log_func(logger)
def send_message(sock, message):
    """
    Утилита кодирования и отправки сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    """
    sock.send(message)


@log_func(logger)
def process_client_message(message, messages_list, client, clients, chats: dict):
    """
    Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
    проверяет корректность, отправляет словарь-ответ в случае необходимости.
    :param message:
    :param messages_list:
    :param client:
    :param clients:
    :param chats:
    :return:
    """
    logger.debug(f'Разбор сообщения от клиента : {message}')

    is_presence = ACTION in message and message[ACTION] == PRESENCE
    is_message = ACTION in message and message[ACTION] == MESSAGE
    is_exit = ACTION in message and message[ACTION] == EXIT
    is_true_msg = TIME in message and CHATID in message and ACC in message

    if not is_true_msg:  # Нет минимальных параметров
        send_message(client, response_error('Запрос некорректен.'))
        return

    chat_id = message[CHATID]
    acc = message[ACC]

    # Если это сообщение о присутствии, принимаем и отвечаем
    if is_presence:
        # Если такой пользователь ещё не зарегистрирован, регистрируем, иначе отправляем ответ и завершаем соединение.
        if chat_id not in chats:
            chats[chat_id] = {acc: client}
            send_message(client, response_presence())
        elif acc not in chats[chat_id]:
            chats[chat_id][acc] = client
            send_message(client, response_presence())
        else:
            send_message(client, response_error('Имя пользователя уже занято.'))
            clients.remove(client)
            client.close()
        return
    # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
    elif is_message:
        messages_list.append(message)
        return
    # Если клиент выходит
    elif is_exit:
        clients.remove(chats[chat_id][acc])
        chats[chat_id][acc].close()
        chats[chat_id].pop(acc)
        return
    # Иначе отдаём Bad request
    else:
        send_message(client, response_error('Запрос некорректен.'))
        return


@log_func(logger)
def process_message(message, chats, listen_socks):
    """
    Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
    список зарегистрированных пользователей и слушающие сокеты. Ничего не возвращает.
    :param message:
    :param chats:
    :param listen_socks:
    :return:
    """

    acc, chat_id = message[ACC], message[CHATID]

    on_acc = []
    if chat_id in chats:
        for recipient, sock in chats[chat_id].items():
            on_acc.append(sock in listen_socks)
            if recipient != acc and sock in listen_socks:
                send_message(sock, encode_message(message))
                logger.info(f'Отправлено сообщение пользователю {acc} в чат {chat_id}.')
    else:
        logger.error(f'Чат {chat_id} не зарегистрирован на сервере, отправка сообщения невозможна.')

    if not any(on_acc):
        raise ConnectionError


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


def mainloop():
    """
    Основной цикл обработки запросов клиентов
    """
    host, port = arg_parser()

    logger.info(f'Запущен сервер: {host}:{port}')

    transport = socket(AF_INET, SOCK_STREAM)
    transport.bind((host, port))
    transport.settimeout(0.5)
    transport.listen(MAX_CONNECTIONS)

    clients = []  # список клиентов
    messages = []  # очередь сообщений
    chats = dict()  # список чатов

    while True:
        try:
            conn, addr = transport.accept()  # Проверка подключений
        except OSError:
            pass  # timeout вышел
        else:
            print("Получен запрос на соединение от %s" % str(addr))
            clients.append(conn)

        recv_data_lst, send_data_lst, err_lst = [], [], []

        # Проверить наличие событий ввода-вывода
        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select(clients, clients, [], 0)
        except Exception:
            pass  # Ничего не делать, если какой-то клиент отключился

        # принимаем сообщения и если ошибка, исключаем клиента.
        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message, clients, chats)
                except Exception as e:
                    logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.{e}')
                    clients.remove(client_with_message)

        # Если есть сообщения, обрабатываем каждое.
        for i in messages:
            acc, chat_id = i[ACC], i[CHATID]
            try:
                process_message(i, chats, send_data_lst)
            except Exception as e:
                logger.info(f'Связь с клиентом с именем {acc} была потеряна: {e}')
                clients.remove(chats[chat_id][acc])
                chats[chat_id].pop(acc)

        messages.clear()


if __name__ == '__main__':
    mainloop()
