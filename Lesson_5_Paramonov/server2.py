import argparse
import logging
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM
from select import select
import log.server_log_config
from log.logger_func import log_func
from meta import ServerVerifier, Port
from common.utils import *

logger = logging.getLogger('chat.server')


# Основной класс сервера
class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, host_addres, port):
        # Параментры подключения
        self.addr = host_addres
        self.port = port
        self.clients = []  # список клиентов
        self.messages = []  # очередь сообщений
        self.chats = dict()  # список чатов

    def init_socket(self):
        logger.info(f'Запущен сервер: {self.addr}:{self.port}')

        transport = socket(AF_INET, SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                print("Получен запрос на соединение от %s" % str(client_address))
                self.clients.append(client)

            recv_data_lst, send_data_lst, err_lst = [], [], []

            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for i in self.messages:
                acc, chat_id = i[ACC], i[CHATID]
                try:
                    self.process_message(i, send_data_lst)
                except Exception as e:
                    logger.info(f'Связь с клиентом с именем {acc} была потеряна: {e}')
                    self.clients.remove(self.chats[chat_id][acc])
                    self.chats[chat_id].pop(acc)
            self.messages.clear()

    def process_message(self, message, listen_socks):
        acc, chat_id = message[ACC], message[CHATID]

        on_acc = []
        if chat_id in self.chats:
            for recipient, sock in self.chats[chat_id].items():
                on_acc.append(sock in listen_socks)
                if recipient != acc and sock in listen_socks:
                    send_message(sock, encode_message(message))
                    logger.info(f'Отправлено сообщение пользователю {acc} в чат {chat_id}.')
        else:
            logger.error(f'Чат {chat_id} не зарегистрирован на сервере, отправка сообщения невозможна.')

        if not any(on_acc):
            raise ConnectionError

    def process_client_message(self, message, client):
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
            if chat_id not in self.chats:
                self.chats[chat_id] = {acc: client}
                send_message(client, response_presence())
            elif acc not in self.chats[chat_id]:
                self.chats[chat_id][acc] = client
                send_message(client, response_presence())
            else:
                send_message(client, response_error('Имя пользователя уже занято.'))
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif is_message:
            self.messages.append(message)
            return
        # Если клиент выходит
        elif is_exit:
            self.clients.remove(self.chats[chat_id][acc])
            self.chats[chat_id][acc].close()
            self.chats[chat_id].pop(acc)
            return
        # Иначе отдаём Bad request
        else:
            send_message(client, response_error('Запрос некорректен.'))
            return


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


def main():
    listen_address, listen_port = arg_parser()

    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
