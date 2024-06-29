import unittest
from flask import Flask
from backend.utils.error_handler import handle_error

class TestErrorHandler(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_handle_error(self):
        with self.app.test_request_context():
            response = handle_error("Test error")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), {"error": "Test error"})

if __name__ == '__main__':
    unittest.main()