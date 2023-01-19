import argparse
import configparser
import logging
import os
import sys
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM
from select import select
import log.server_log_config
from log.logger_func import log_func
from meta import ServerVerifier, Port
from common.utils import *
from server_database import Storage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('chat.server')


# Основной класс сервера
class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, host_addres, port, database):
        # Параметры подключения
        self.addr = host_addres
        self.port = port
        self.clients = []  # список клиентов
        self.messages = []  # очередь сообщений
        self.chats = dict()  # список чатов

        # База данных сервера
        self.database = database

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
                    except Exception as e:
                        print(e)
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        # self.database.user_logout(message[DESTINATION])
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

        is_get_contacts = ACTION in message and message[ACTION] == GET_CONTACTS
        is_add_cotact = ACTION in message and message[ACTION] == ADD_CONTACT
        is_remove_contact = ACTION in message and message[ACTION] == REMOVE_CONTACT
        is_all_users = ACTION in message and message[ACTION] == USERS_REQUEST

        if not is_true_msg:  # Нет минимальных параметров
            send_message(client, response_error('Запрос некорректен.'))
            return

        chat_id = message[CHATID]
        acc = message[ACC]

        # Если это сообщение о присутствии, принимаем и отвечаем
        if is_presence:
            # Если такой пользователь ещё не зарегистрирован, регистрируем, иначе отправляем ответ и завершаем соединение.
            if chat_id not in self.chats:

                client_ip, client_port = client.getpeername()
                self.database.user_login(acc, client_ip, client_port)

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
            self.database.process_message(acc, chat_id)
            self.messages.append(message)
            return
        # Если клиент выходит
        elif is_exit:
            self.database.user_logout(acc)
            self.clients.remove(self.chats[chat_id][acc])
            self.chats[chat_id][acc].close()
            self.chats[chat_id].pop(acc)
            return
        # Если это запрос контакт-листа
        elif is_get_contacts:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(acc)
            send_message(client, encode_message(response))
        # Если это добавление контакта
        elif is_add_cotact:
            self.database.add_contact(acc, chat_id)
            send_message(client, encode_message(RESPONSE_200))
        # Если это удаление контакта
        elif is_remove_contact:
            self.database.remove_contact(acc, chat_id)
            send_message(client, encode_message(RESPONSE_200))
        # Если это запрос известных пользователей
        elif is_all_users:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, encode_message(response))
        # Иначе отдаём Bad request
        else:
            send_message(client, response_error('Запрос некорректен.'))
            return


@log_func(logger)
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
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
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём значения по умолчанию.
    listen_address, listen_port = arg_parser(config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # Инициализация базы данных
    database = Storage(os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.main_loop()


if __name__ == '__main__':
    main()
