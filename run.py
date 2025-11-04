import os
from app import create_app
from flask import render_template

app = create_app()

# ===== PAGE ROUTES =====
@app.route('/', methods=['GET'])
def dashboard():
    return render_template('index.html')

@app.route('/epic-dashboard', methods=['GET'])
def epic_dashboard():
    return render_template('epic_dashboard.html')

@app.route('/bulk-epic-export', methods=['GET'])
def bulk_epic_export_page():
    return render_template('bulk-export.html')

@app.route('/bulk-backend-export', methods=['GET'])
def bulk_backend_export_page():
    return render_template('bulk-export-backend.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)