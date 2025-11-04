from flask import Flask
from flask_cors import CORS
import os

def create_app():
    # Specify folder locations
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static')
    
    # Use environment variable for secret key in production
    app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    CORS(app)
    
    # Import and register blueprints
    try:
        from app.routes import analytics_bp, epic_bp, backend_bp
        app.register_blueprint(analytics_bp)
        app.register_blueprint(epic_bp)
        app.register_blueprint(backend_bp)
    except Exception as e:
        print(f"Error loading blueprints: {e}")
        raise
    
    return app