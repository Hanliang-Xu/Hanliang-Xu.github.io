import unittest

from flask import Flask

from backend.routes.upload_routes import upload_bp


class TestUploadRoutes(unittest.TestCase):

  def setUp(self):
    self.app = Flask(__name__)
    self.app.register_blueprint(upload_bp)
    self.client = self.app.test_client()

  def test_upload_files(self):
    # Simulate file upload and validate response
    pass


if __name__ == '__main__':
  unittest.main()
