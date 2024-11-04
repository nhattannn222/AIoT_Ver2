from flask import Flask
from .db import db
from flask_jwt_extended import JWTManager
from .config import Config
from .routes.device_routes import device_bp
from .routes.userInfo_routes import user_bp
from .routes.auth_routes import auth_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load configuration

    # CORS configuration to allow specific origins and credentials
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    jwt = JWTManager(app)  # Initialize JWT
    db.init_app(app)  # Connect Flask app with the database

    # Register blueprints for routing
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    app.register_blueprint(user_bp, url_prefix='/api/users')

    return app
