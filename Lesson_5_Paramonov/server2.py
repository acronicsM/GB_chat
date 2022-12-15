from socket import socket, AF_INET, SOCK_STREAM
from select import select
from datetime import datetime
import json, logging, argparse
import log.server_log_config
from log.logger_func import log_func

logger = logging.getLogger('chat.server')

HOST: str = 'localhost'
PORT: int = 7777

CHATSID = dict()

class Chat():
    __slots__ = ['id', 'unsentMessages', 'sockets']
    def __init__(self, id):
        self.id = id
        self.unsentMessages = dict()
        self.sockets = set()


def arg_parser():
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


def response_message(message: dict, sock: socket) -> bytes:
    user = message.get('USER')
    acc_name, chat_id = user.get('ACCOUNT_NAME'), user.get('chat_id')

    msg_chat = CHATSID.setdefault(chat_id, Chat(chat_id))
    msg_chat.sockets.add(sock)

    for i in msg_chat.sockets:
        if i != sock:
            msg_chat.unsentMessages.setdefault(i, []).append((message['msg'], message['time'], acc_name))

    new_msg = []
    if sock in msg_chat.unsentMessages:
        for msg, time, acc in msg_chat.unsentMessages[sock]:
            new_msg.append({'msg': msg, 'time': time, 'acc': acc, })


    return encode_message({"response": 200, 'time': datetime.now().timestamp(), 'new_msg': new_msg})


@log_func(logger)
def response_error(error) -> bytes:
    return encode_message({"response": 400, 'time': datetime.now().timestamp(), "error": error, })


def read_requests(r_clients, all_clients):
    """
    Чтение запросов из списка клиентов
    """
    responses = {} # Словарь ответов сервера вида {сокет: запрос}
    for sock in r_clients:
        try:
            data = sock.recv(1024).decode('utf-8')
            responses[sock] = data
        except:
            print('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
            all_clients.remove(sock)
    return responses


def write_responses(requests, w_clients, all_clients):
    """
    Эхо-ответ сервера клиентам, от которых были запросы
    """
    for sock in w_clients:
        if sock in requests:
            try:
                # Подготовить и отправить ответ сервера
                resp = requests[sock].encode('utf-8')
                # Эхо-ответ сделаем чуть непохожим на оригинал
                sock.send(read_message(resp, sock))
            except: # Сокет недоступен, клиент отключился
                print('Клиент {} {} отключился'.format(sock.fileno(),
                sock.getpeername()))
                sock.close()
                all_clients.remove(sock)


@log_func(logger)
def read_message(message: bytes, sock: socket) -> bytes:
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
    if data['action'] == 'message':
        return response_message(data, sock)

    logger.warning(f'Неизвестная команда: {data["action"]}')
    return response_error('Неизвестный "action"')


def mainloop():
    """
    Основной цикл обработки запросов клиентов
    """

    address = (HOST, PORT)
    clients = []
    messages = []
    s = socket(AF_INET, SOCK_STREAM)
    s.bind(address)
    s.listen(5)
    s.settimeout(0.2)  # Таймаут для операций с сокетом
    while True:
        try:
            conn, addr = s.accept()  # Проверка подключений
        except OSError as e:
            pass  # timeout вышел
        else:
            print("Получен запрос на соединение от %s" % str(addr))
            clients.append(conn)
        finally:
            # Проверить наличие событий ввода-вывода
            wait, r, w = 10, [], []
            try:
                r, w, e = select(clients, clients, [], wait)
            except:
                pass  # Ничего не делать, если какой-то клиент отключился
            requests = read_requests(r, clients)  # Сохраним запросы клиентов
            if requests:
                write_responses(requests, w, clients)  # Выполним отправку ответов клиентам



def write_responses_for_chat(chat_id: int, chat:Chat):
    for _ in range(len(chat.unsentMessages)):
        msg, time, acc, sock = chat.unsentMessages.pop()

        message = {
            'action': 'in_msg',
            'msg': msg,
            'time': time,
            'acc': acc,
        }

        for i in chat.sockets:
            if i != sock:
                resp = encode_message(message)
                i.send(resp)



if __name__ == '__main__':
    mainloop()

