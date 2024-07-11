from flask import Blueprint, request, send_file, current_app

from backend.utils.error_handler import handle_error

download_bp = Blueprint('download', __name__)


@download_bp.route('/download', methods=['GET'])
def download_report():
  report_type = request.args.get('type')
  config = current_app.config['paths']

  report_files = {
    'major_errors': config['major_error_report'],
    'errors': config['error_report'],
    'warnings': config['warning_report'],
    'report': config['final_report']
  }

  file_path = report_files.get(report_type)
  if file_path:
    return send_file(file_path, as_attachment=True)
  else:
    return handle_error("Invalid report type", 400)
