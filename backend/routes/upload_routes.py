from flask import Blueprint, request
from ..utils.file_handler import handle_upload

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload', methods=['POST'])
def upload_files():
  response, status_code = handle_upload(request)
  return response, status_code
