import unittest
from backend.utils.config_loader import load_config

class TestConfigLoader(unittest.TestCase):

    def test_load_config(self):
        config = load_config('config.yaml')
        self.assertIn('server', config)
        self.assertIn('paths', config)

if __name__ == '__main__':
    unittest.main()