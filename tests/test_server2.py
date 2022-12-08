import json
import unittest
import Lesson_5_Paramonov.server2 as server2


def decode_message(message: bytes) -> dict:
    return  json.loads(message.decode('utf-8'))


class TestClient2(unittest.TestCase):

    def test_no_message(self):
        answ = server2.read_message(b'')
        data = decode_message(answ)

        self.assertEqual(data['response'], 400)

    def test_invalid_message(self):
        answ = server2.read_message(b'dfdsfdsf')
        data = decode_message(answ)

        self.assertEqual(data['response'], 400)

    def test_no_presence_message(self):
        answ = server2.read_message(b'{"time": 1}')
        data = decode_message(answ)

        self.assertEqual(data['response'], 400)

    def test_no_time_message(self):
        answ = server2.read_message(b'{"action": "presence"}')
        data = decode_message(answ)

        self.assertEqual(data['response'], 400)

    def test_no_time_and_action_message(self):
        answ = server2.read_message(b'{"test": "test"}')
        data = decode_message(answ)

        self.assertEqual(data['response'], 400)

    def test_unknown_action_message(self):
        answ = server2.read_message(b'{"action": "unknown", "test": "test"}')
        data = decode_message(answ)

        self.assertEqual(data['response'], 400)

    def test_true_message(self):
        answ = server2.read_message(b'{"action": "presence", "time": "1"}')
        data = decode_message(answ)

        self.assertEqual(data['response'], 200)


if __name__ == "__main__":
    unittest.main()
