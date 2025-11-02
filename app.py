# Epic FHIR integration and Flask API for Patient Health Analytics
from epic_fhir import EpicFHIRClient, get_epic_auth_url, exchange_code_for_token, save_observations_to_db
from flask import request, session, redirect, url_for
import pandas as pd
import json

from flask import render_template
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'admin'),
        password=os.getenv('DB_PASSWORD', 'healthpass123'),
        database=os.getenv('DB_NAME', 'patient_health_analytics'),
        port=5432
    )
    return conn

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "API is running ✓"}), 200

@app.route('/', methods=['GET'])
def dashboard():
    return render_template('index.html')

# Get total patient count
@app.route('/api/patients/count', methods=['GET'])
def patient_count():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM patients;"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "data": count,
            "query": query,
            "description": "Returns the total number of patients in the database",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all patients
@app.route('/api/patients', methods=['GET'])
def get_patients():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT patient_id, first_name, last_name, date_of_birth, email FROM patients;"
        cursor.execute(query)
        patients = cursor.fetchall()
        
        # Convert to list of dicts
        patient_list = [
            {
                "id": p[0],
                "first_name": p[1],
                "last_name": p[2],
                "date_of_birth": str(p[3]),
                "email": p[4]
            }
            for p in patients
        ]
        
        conn.close()
        
        return jsonify({
            "data": patient_list,
            "query": query,
            "description": "Returns all patients with their basic information",
            "count": len(patient_list),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all conditions
@app.route('/api/conditions', methods=['GET'])
def get_conditions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT condition_id, condition_name, description, severity_level FROM conditions;"
        cursor.execute(query)
        conditions = cursor.fetchall()
        
        condition_list = [
            {
                "id": c[0],
                "name": c[1],
                "description": c[2],
                "severity": c[3]
            }
            for c in conditions
        ]
        
        conn.close()
        
        return jsonify({
            "data": condition_list,
            "query": query,
            "description": "Returns all medical conditions in the database",
            "count": len(condition_list),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get patient conditions (analytics)
@app.route('/api/analytics/patient-conditions', methods=['GET'])
def patient_conditions_analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT c.condition_name, COUNT(pc.patient_id) as patient_count
        FROM conditions c
        LEFT JOIN patient_conditions pc ON c.condition_id = pc.condition_id
        GROUP BY c.condition_id, c.condition_name
        ORDER BY patient_count DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        analytics = [
            {
                "condition": r[0],
                "patient_count": r[1]
            }
            for r in results
        ]
        
        conn.close()
        
        return jsonify({
            "data": analytics,
            "query": query.strip(),
            "description": "Shows how many patients have each condition (grouped by condition name, ordered by frequency)",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== EPIC FHIR ROUTES =====

@app.route('/epic/login', methods=['GET'])
def epic_login():
    """Redirect user to Epic OAuth login"""
    auth_url = get_epic_auth_url()
    return redirect(auth_url)

@app.route('/callback', methods=['GET'])
def epic_callback():
    """Handle Epic OAuth callback"""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    
    token_response = exchange_code_for_token(code)
    if not token_response:
        return jsonify({"error": "Failed to get access token"}), 500
    
    # Store token in session (in production, use secure storage)
    session['epic_token'] = token_response.get('access_token')
    
    return redirect('/epic-dashboard')

@app.route('/epic-dashboard', methods=['GET'])
def epic_dashboard():
    """Show Epic patient data"""
    return render_template('epic_dashboard.html')

@app.route('/api/epic/patients', methods=['GET'])
def get_epic_patients():
    """Fetch patients from Epic FHIR"""
    try:
        access_token = session.get('epic_token')
        if not access_token:
            return jsonify({"error": "Not authenticated with Epic"}), 401
        
        client = EpicFHIRClient(access_token)
        patients_response = client.search_patients(count=5)
        
        if not patients_response:
            return jsonify({"error": "Failed to fetch patients"}), 500
        
        # Parse and format patient data
        patients_data = []
        for entry in patients_response.get('entry', []):
            resource = entry.get('resource', {})
            name = resource.get('name', [{}])[0]
            
            patients_data.append({
                'id': resource.get('id'),
                'first_name': name.get('given', [''])[0],
                'last_name': name.get('family', ''),
                'dob': resource.get('birthDate'),
                'gender': resource.get('gender'),
                'avatar': f'https://ui-avatars.com/api/?name={name.get("given", [""])[0]}+{name.get("family", "")}'
            })
        
        # Create pandas dataframe
        df = pd.DataFrame(patients_data)
        
        return jsonify({
            "data": patients_data,
            "table_html": df.to_html(classes='table table-striped'),
            "query": "Patient.search() from Epic FHIR",
            "description": "Fetching 5 patients from Epic test system with SMART authentication",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/epic/observations/<patient_id>', methods=['GET'])
def get_patient_obs(patient_id):
    """Fetch observations for a specific patient"""
    try:
        access_token = session.get('epic_token')
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401
        
        client = EpicFHIRClient(access_token)
        obs_response = client.get_patient_observations(patient_id)
        
        if not obs_response:
            return jsonify({"error": "No observations found"}), 404
        
        # Parse observations
        observations = []
        for entry in obs_response.get('entry', []):
            resource = entry.get('resource', {})
            observations.append({
                'code': resource.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                'value': resource.get('valueQuantity', {}).get('value', 'N/A'),
                'unit': resource.get('valueQuantity', {}).get('unit', ''),
                'date': resource.get('effectiveDateTime', 'N/A')
            })
        
        # Create pandas dataframe
        df = pd.DataFrame(observations)
        
        return jsonify({
            "data": observations,
            "table_html": df.to_html(classes='table table-striped'),
            "description": "Patient observations and lab results from Epic",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/epic/save-observations/<patient_id>', methods=['POST'])
def save_observations(patient_id):
    """Save Epic observations to database"""
    try:
        access_token = session.get('epic_token')
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Get observations from Epic
        client = EpicFHIRClient(access_token)
        obs_response = client.get_patient_observations(patient_id)
        
        if not obs_response or 'entry' not in obs_response:
            return jsonify({"error": "No observations found"}), 404
        
        # Parse observations
        observations = []
        for entry in obs_response.get('entry', []):
            resource = entry.get('resource', {})
            observations.append({
                'code': resource.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                'value': resource.get('valueQuantity', {}).get('value', 'N/A'),
                'unit': resource.get('valueQuantity', {}).get('unit', ''),
                'date': resource.get('effectiveDateTime', None)
            })
        
        # Save to database
        conn = get_db_connection()
        
        # First, try to find patient in local database
        cursor = conn.cursor()
        query = "SELECT patient_id FROM patients LIMIT 1"  # For now, save to first patient
        cursor.execute(query)
        result = cursor.fetchone()
        local_patient_id = result[0] if result else 1
        
        # Save observations
        success = save_observations_to_db(conn, local_patient_id, patient_id, observations)
        
        conn.close()
        
        if success:
            return jsonify({
                "message": "Observations saved successfully",
                "count": len(observations),
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({"error": "Failed to save observations"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patient-observations', methods=['GET'])
def get_patient_observations_db():
    """Retrieve saved observations from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT test_name, value, unit, observation_date 
        FROM patient_observations 
        ORDER BY observation_date DESC
        LIMIT 100
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        observations = [
            {
                "test_name": r[0],
                "value": r[1],
                "unit": r[2],
                "date": str(r[3]) if r[3] else None
            }
            for r in results
        ]
        
        conn.close()
        
        return jsonify({
            "data": observations,
            "count": len(observations),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/epic/bulk-export', methods=['GET'])
def epic_bulk_export():
    """Fetch all patients from Epic FHIR and return demographic data"""
    try:
        access_token = session.get('epic_token')
        if not access_token:
            return jsonify({"error": "Not authenticated with Epic"}), 401
        
        client = EpicFHIRClient(access_token)
        patients_response = client.search_patients(count=100)  # Get up to 100 patients
        
        if not patients_response:
            return jsonify({"error": "Failed to fetch patients"}), 500
        
        # Parse and format patient data
        patients_data = []
        gender_counts = {'male': 0, 'female': 0, 'other': 0}
        conditions_count = {}
        
        for entry in patients_response.get('entry', []):
            resource = entry.get('resource', {})
            name = resource.get('name', [{}])[0]
            gender = resource.get('gender', 'unknown').lower()
            dob = resource.get('birthDate')
            
            # Calculate age
            if dob:
                from datetime import datetime
                birth_date = datetime.strptime(dob, '%Y-%m-%d')
                age = (datetime.now() - birth_date).days // 365
            else:
                age = None
            
            patients_data.append({
                'id': resource.get('id'),
                'first_name': name.get('given', [''])[0],
                'last_name': name.get('family', ''),
                'dob': dob,
                'age': age,
                'gender': gender if gender in ['male', 'female'] else 'other',
                'avatar': f'https://ui-avatars.com/api/?name={name.get("given", [""])[0]}+{name.get("family", "")}'
            })
            
            # Count genders
            if gender in ['male', 'female']:
                gender_counts[gender] += 1
            else:
                gender_counts['other'] += 1
        
        # Create pandas dataframe
        df = pd.DataFrame(patients_data)
        
        # Calculate statistics
        stats = {
            'total_patients': len(patients_data),
            'gender_counts': gender_counts,
            'average_age': float(df['age'].mean()) if 'age' in df.columns else None,
            'age_range': {
                'min': int(df['age'].min()) if 'age' in df.columns else None,
                'max': int(df['age'].max()) if 'age' in df.columns else None
            }
        }
        
        return jsonify({
            "data": patients_data,
            "stats": stats,
            "table_html": df.to_html(classes='table table-striped table-hover'),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/bulk-epic-export', methods=['GET'])
def bulk_epic_export_page():
    """Show bulk export page"""
    return render_template('bulk-export.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)