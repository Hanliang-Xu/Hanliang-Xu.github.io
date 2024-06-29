from flask import jsonify


def handle_error(error_message, status_code=400):
  response = jsonify({"error": error_message})
  response.status_code = status_code
  return response
