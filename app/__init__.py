from flask import Flask, render_template
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
    
    # ===== PAGE ROUTES =====
    @app.route('/')
    def dashboard():
        return render_template('index.html')

    @app.route('/epic-dashboard')
    def epic_dashboard():
        return render_template('epic_dashboard.html')

    @app.route('/bulk-epic-export')
    def bulk_epic_export_page():
        return render_template('bulk-export.html')

    @app.route('/bulk-backend-export')
    def bulk_backend_export_page():
        return render_template('bulk-export-backend.html')
    
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