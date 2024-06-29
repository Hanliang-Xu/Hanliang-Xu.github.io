import unittest

from flask import Flask

from backend.routes.download_routes import download_bp


class TestDownloadRoutes(unittest.TestCase):

  def setUp(self):
    self.app = Flask(__name__)
    self.app.register_blueprint(download_bp)
    self.client = self.app.test_client()

  def test_download_report(self):
    response = self.client.get('/download?type=report')
    self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
  unittest.main()
