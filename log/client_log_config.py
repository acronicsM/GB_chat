import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('chat.client')

# Создаем объект форматирования:
_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
formatter = logging.Formatter(_log_format)

file_handler = TimedRotatingFileHandler('chat.client.log', encoding='utf-8', when="midnight", interval=1, backupCount=7)
file_handler.setLevel(logging.INFO)
file_handler.suffix = "%Y-%m-%d"
file_handler.setFormatter(formatter)

# Добавляем в логгер новый обработчик событий и устанавливаем уровень логирования
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # Создаем потоковый обработчик логирования (по умолчанию sys.stderr):
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.info('Тестовый запуск логирования')
