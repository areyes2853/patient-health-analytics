from app import create_app
from flask import render_template, request, session, redirect
from epic_fhir import exchange_code_for_token

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

# ===== EPIC CALLBACK (NOT in blueprint) =====
@app.route('/callback', methods=['GET'])
def epic_callback():
    """Handle Epic OAuth callback"""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    
    token_response = exchange_code_for_token(code)
    if not token_response:
        return jsonify({"error": "Failed to get access token"}), 500
    
    session['epic_token'] = token_response.get('access_token')
    return redirect('/epic-dashboard')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)