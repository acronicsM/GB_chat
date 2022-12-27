# ————— __getattr__ + __getattribute__
class ValidatingDB:
    def __init__(self):
        self.exists = 5
    def __getattr__(self, name):
        print(' ValidatingDB.__getattr__(%s)' % name)
        value = 'Super %s' % name
        setattr(self, name, value)
        return value
    def __getattribute__(self, name):
        print(' ValidatingDB.__getattribute__(%s)' % name)
        return super().__getattribute__(name)

data = ValidatingDB()
print('Атрибут exists:', data.exists)
print('Атрибут foo: ', data.foo)
print('Снова атрибут foo: ', data.foo)
print('Есть ли атрибут zoom в объекте:', hasattr(data, 'zoom'))
print('Атрибут face в объекте, доступ через getattr:', getattr(data, 'face'))
# Использование метода __setattr__
class SavingDB:
    def __setattr__(self, name, value):
        print(' SavingDB.__setattr__(%s, %r)' % (name, value))
        # Сохранение данных в БД
        # ...
        super().__setattr__(name, value)

data = SavingDB()
print('data.__dict__ до установки атрибута: ', data.__dict__)
data.foo = 5
print('data.__dict__ после установки атрибута: ', data.__dict__)
data.foo = 7
print('data.__dict__ в итоге:', data.__dict__)
