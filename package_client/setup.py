from setuptools import setup, find_packages

setup(name='messenger_GB_client_acronics_31012023',
      version='1',
      description='Client package',
      packages=find_packages(),  # Будем искать пакеты тут(включаем авто поиск пакетов)
      author_email='test@mail.ru',
      author='Michail Paramonov',
      install_requeres=['PyQt5', 'sqlalchemy', 'pycruptodome', 'pycryptodomex'] #зависимости которые нужно до установить
      )
