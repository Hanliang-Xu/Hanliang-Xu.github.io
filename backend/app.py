from flask import Flask
from flask_cors import CORS
from backend.routes import upload_routes, download_routes, home_routes
from backend.utils.config_loader import load_config

app = Flask(__name__)
CORS(app)

config = load_config('backend/config.yaml')

app.config.update(config)

# Register blueprints
app.register_blueprint(home_routes.home_bp)
app.register_blueprint(upload_routes.upload_bp)
app.register_blueprint(download_routes.download_bp)

if __name__ == '__main__':
    app.run(host=config['server']['host'], port=config['server']['port'])