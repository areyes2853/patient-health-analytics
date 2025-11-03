# app/routes/epic.py
from flask import jsonify, session, redirect, request
from datetime import datetime
import pandas as pd
from . import epic_bp
from epic_fhir import EpicFHIRClient, get_epic_auth_url, exchange_code_for_token, save_observations_to_db
from app.utils import get_db_connection

# ===== AUTHENTICATION ROUTES =====
@epic_bp.route('/epic/login', methods=['GET'])
def epic_login():
    """Redirect user to Epic OAuth login"""
    auth_url = get_epic_auth_url()
    return redirect(auth_url)


@epic_bp.route('/callback', methods=['GET'])
def epic_callback():
    """Handle Epic OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    print(f"DEBUG: Callback received - code: {code}, error: {error}")
    
    if error:
        print(f"ERROR from Epic: {error}")
        return jsonify({"error": f"Epic error: {error}"}), 400
    
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    
    token_response = exchange_code_for_token(code)
    print(f"DEBUG: Token response: {token_response}")
    
    if not token_response:
        return jsonify({"error": "Failed to get access token"}), 500
    
    session['epic_token'] = token_response.get('access_token')
    return redirect('/epic-dashboard')

# ===== API ROUTES =====
@epic_bp.route('/epic/patients', methods=['GET'])
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

@epic_bp.route('/epic/observations/<patient_id>', methods=['GET'])
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
        
        observations = []
        for entry in obs_response.get('entry', []):
            resource = entry.get('resource', {})
            observations.append({
                'code': resource.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                'value': resource.get('valueQuantity', {}).get('value', 'N/A'),
                'unit': resource.get('valueQuantity', {}).get('unit', ''),
                'date': resource.get('effectiveDateTime', 'N/A')
            })
        
        df = pd.DataFrame(observations)
        
        return jsonify({
            "data": observations,
            "table_html": df.to_html(classes='table table-striped'),
            "description": "Patient observations and lab results from Epic",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@epic_bp.route('/epic/save-observations/<patient_id>', methods=['POST'])
def save_observations(patient_id):
    """Save Epic observations to database"""
    try:
        access_token = session.get('epic_token')
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401
        
        client = EpicFHIRClient(access_token)
        obs_response = client.get_patient_observations(patient_id)
        
        if not obs_response or 'entry' not in obs_response:
            return jsonify({"error": "No observations found"}), 404
        
        observations = []
        for entry in obs_response.get('entry', []):
            resource = entry.get('resource', {})
            observations.append({
                'code': resource.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                'value': resource.get('valueQuantity', {}).get('value', 'N/A'),
                'unit': resource.get('valueQuantity', {}).get('unit', ''),
                'date': resource.get('effectiveDateTime', None)
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id FROM patients LIMIT 1")
        result = cursor.fetchone()
        local_patient_id = result[0] if result else 1
        
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

@epic_bp.route('/epic/bulk-export', methods=['GET'])
def epic_bulk_export():
    """Fetch all patients from Epic FHIR and return demographic data"""
    try:
        access_token = session.get('epic_token')
        if not access_token:
            return jsonify({"error": "Not authenticated with Epic"}), 401
        
        client = EpicFHIRClient(access_token)
        patients_response = client.search_patients(count=100)
        
        if not patients_response:
            return jsonify({"error": "Failed to fetch patients"}), 500
        
        patients_data = []
        gender_counts = {'male': 0, 'female': 0, 'other': 0}
        
        for entry in patients_response.get('entry', []):
            resource = entry.get('resource', {})
            name = resource.get('name', [{}])[0]
            gender = resource.get('gender', 'unknown').lower()
            dob = resource.get('birthDate')
            
            if dob:
                from datetime import datetime as dt
                birth_date = dt.strptime(dob, '%Y-%m-%d')
                age = (dt.now() - birth_date).days // 365
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
            
            if gender in ['male', 'female']:
                gender_counts[gender] += 1
            else:
                gender_counts['other'] += 1
        
        df = pd.DataFrame(patients_data)
        
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
        import traceback
        error_msg = traceback.format_exc()
        print(f"BULK EXPORT ERROR: {error_msg}")  # Prints to Docker logs
        return jsonify({"error": str(e), "traceback": error_msg}), 500