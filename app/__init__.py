# app/__init__.py
from flask import Flask
from flask_cors import CORS
import os

def create_app():
    # Specify folder locations
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static')
    app.secret_key = 'your-secret-key-change-in-production'
    CORS(app)
    
    # Import and register blueprints
    from app.routes import analytics_bp, epic_bp
    app.register_blueprint(analytics_bp)
    app.register_blueprint(epic_bp)
    
    return app