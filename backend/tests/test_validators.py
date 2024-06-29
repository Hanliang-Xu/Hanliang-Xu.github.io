import unittest
from backend.utils.validators import NumberValidator, StringValidator

class TestValidators(unittest.TestCase):

    def test_number_validator(self):
        validator = NumberValidator(min_error=0, max_error=100)
        self.assertIsNone(validator.validate(50)[0])
        self.assertIsNotNone(validator.validate(-1)[2])
        self.assertIsNotNone(validator.validate(101)[2])

    def test_string_validator(self):
        validator = StringValidator(allowed_values=['yes', 'no'], major_error=True)
        self.assertIsNone(validator.validate('yes')[0])
        self.assertIsNotNone(validator.validate('maybe')[0])

if __name__ == '__main__':
    unittest.main()