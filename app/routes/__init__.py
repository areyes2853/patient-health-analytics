from flask import Blueprint

# Create blueprints
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api')
epic_bp = Blueprint('epic', __name__, url_prefix='/api')

# Import routes
from . import analytics, epic