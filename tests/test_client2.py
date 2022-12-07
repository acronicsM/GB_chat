import unittest
import Lesson_5_Paramonov.client2 as client2


class TestClient2(unittest.TestCase):

    def test_connector(self):
        connect = client2.connector('localhost', 8777)
        self.assertEqual(connect[1], True, 'Соединение не установлено')

    def test_decode_message_no_msg(self):
        answ = client2.decode_message(b'')
        self.assertEqual(answ['Error'], 400)

    def test_decode_message_error_msg(self):
        answ = client2.decode_message(b'dfdsfdf')
        self.assertEqual(answ['Error'], 400)

    def test_decode_message_true_msg(self):
        answ = client2.decode_message(b'{"response": 200, "time": 1}')
        self.assertEqual(answ, {"response": 200, "time": 1})

    def test_encode_message(self):
        answ = client2.encode_message({'action': 'presence', 'msg': 'тест'})
        self.assertEqual(answ, b'{"action": "presence", "msg": "\\u0442\\u0435\\u0441\\u0442"}')

    def test_send_presence(self):
        connect = client2.connector('localhost', 7777)[0]
        t = client2.send_presence(connect)
        connect.close()

        data = client2.decode_message(t)

        self.assertEqual('Error' in data, False)


if __name__ == "__main__":
    unittest.main()
