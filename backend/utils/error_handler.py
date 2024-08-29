"""
This module provides a utility function to handle errors in a Flask application by returning
a JSON response with a specified error message and HTTP status code.

The `handle_error` function is designed to simplify and standardize the way error responses are
returned to the client. By encapsulating the error handling logic in this function, the application
can maintain consistent error responses, making it easier to manage client-side error handling.
"""

from flask import jsonify


def handle_error(error_message, status_code=400):
  """
  Generate a JSON response for an error.

  :param error_message: A string describing the error.
  :param status_code: The HTTP status code to return with the error (default is 400).
  :return: A Flask `Response` object containing the error message and status code.
  """

  response = jsonify({"error": error_message})
  response.status_code = status_code
  return response
