# app/routes/backend_services.py
"""
Backend Services routes - No user login required
Perfect for automated bulk data operations
"""

from flask import jsonify, request
from datetime import datetime
import pandas as pd
from . import backend_bp
from epic_backend_auth import EpicBackendAuth, EpicBulkExport


# Initialize backend auth client (singleton)
backend_auth = None

def get_backend_auth():
    """Get or create backend auth client"""
    global backend_auth
    if backend_auth is None:
        backend_auth = EpicBackendAuth()
    return backend_auth


@backend_bp.route('/backend/test-connection', methods=['GET'])
def test_backend_connection():
    """Test backend services authentication"""
    try:
        auth = get_backend_auth()
        success = auth.test_connection()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Backend Services authentication working!",
                "client_id": auth.client_id,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Authentication failed"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@backend_bp.route('/backend/bulk-patients', methods=['GET'])
def bulk_export_patients():
    """
    Automated bulk patient export - NO USER LOGIN REQUIRED
    This is the key feature that solves your login problem!
    """
    try:
        # Get count from query parameter
        count = request.args.get('count', 100, type=int)
        
        # Initialize clients
        auth = get_backend_auth()
        bulk = EpicBulkExport(auth)
        
        print(f"Fetching {count} patients via Backend Services...")
        
        # Fetch patients (no user login needed!)
        patients_data = bulk.simple_patient_export(count=count)
        
        # Process patient data
        processed_patients = []
        gender_counts = {'male': 0, 'female': 0, 'other': 0}
        
        for resource in patients_data:
            name = resource.get('name', [{}])[0]
            gender = resource.get('gender', 'unknown').lower()
            dob = resource.get('birthDate')
            
            # Calculate age
            age = None
            if dob:
                from datetime import datetime as dt
                birth_date = dt.strptime(dob, '%Y-%m-%d')
                age = (dt.now() - birth_date).days // 365
            
            processed_patients.append({
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
        
        # Create DataFrame for analytics
        df = pd.DataFrame(processed_patients)
        
        stats = {
            'total_patients': len(processed_patients),
            'gender_counts': gender_counts,
            'average_age': float(df['age'].mean()) if 'age' in df.columns and not df['age'].isna().all() else None,
            'age_range': {
                'min': int(df['age'].min()) if 'age' in df.columns and not df['age'].isna().all() else None,
                'max': int(df['age'].max()) if 'age' in df.columns and not df['age'].isna().all() else None
            }
        }
        
        return jsonify({
            "status": "success",
            "data": processed_patients,
            "stats": stats,
            "table_html": df.to_html(classes='table table-striped table-hover'),
            "auth_method": "Backend Services (No User Login)",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"BACKEND BULK EXPORT ERROR: {error_msg}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": error_msg
        }), 500


@backend_bp.route('/backend/patient/<patient_id>/observations', methods=['GET'])
def get_patient_observations_backend(patient_id):
    """Get observations for a patient using backend services"""
    try:
        auth = get_backend_auth()
        token = auth.get_access_token()
        
        import requests
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/fhir+json'
        }
        
        url = f"{auth.fhir_url}/Observation"
        params = {'patient': patient_id, 'category': 'laboratory'}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        obs_data = response.json()
        
        observations = []
        for entry in obs_data.get('entry', []):
            resource = entry.get('resource', {})
            observations.append({
                'code': resource.get('code', {}).get('coding', [{}])[0].get('display', 'Unknown'),
                'value': resource.get('valueQuantity', {}).get('value', 'N/A'),
                'unit': resource.get('valueQuantity', {}).get('unit', ''),
                'date': resource.get('effectiveDateTime', 'N/A')
            })
        
        df = pd.DataFrame(observations) if observations else pd.DataFrame()
        
        return jsonify({
            "status": "success",
            "data": observations,
            "table_html": df.to_html(classes='table table-striped') if not df.empty else "<p>No observations found</p>",
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@backend_bp.route('/backend/bulk-export-start', methods=['POST'])
def start_bulk_export():
    """
    Initiate a full FHIR bulk data export
    This uses the official $export operation
    """
    try:
        auth = get_backend_auth()
        bulk = EpicBulkExport(auth)
        
        # Get parameters
        resource_type = request.json.get('resource_type', 'Patient')
        params = request.json.get('params', {})
        
        # Initiate export
        status_url = bulk.initiate_export(resource_type, params)
        
        return jsonify({
            "status": "initiated",
            "status_url": status_url,
            "message": "Bulk export started. Poll the status URL to check progress.",
            "timestamp": datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@backend_bp.route('/backend/bulk-export-status', methods=['POST'])
def check_bulk_export_status():
    """Check status of a bulk export operation"""
    try:
        status_url = request.json.get('status_url')
        
        if not status_url:
            return jsonify({"error": "status_url required"}), 400
        
        auth = get_backend_auth()
        bulk = EpicBulkExport(auth)
        
        result = bulk.check_export_status(status_url)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@backend_bp.route('/backend/token-info', methods=['GET'])
def get_token_info():
    """Get information about the current access token"""
    try:
        auth = get_backend_auth()
        
        return jsonify({
            "has_token": auth.access_token is not None,
            "token_expiry": auth.token_expiry.isoformat() if auth.token_expiry else None,
            "client_id": auth.client_id,
            "fhir_url": auth.fhir_url
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@backend_bp.route('/backend/.well-known/jwks.json', methods=['GET'])
def get_jwks():
    """Serve JWKS (JSON Web Key Set) for Epic to verify signatures"""
    # Hardcoded JWKS - this is your PUBLIC key (safe to share)
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "epic-backend-key",
                "use": "sig",
                "alg": "RS384",
                "n": "ljZu5kNEmi1ED3_Ceaqh5hT8Ude8HIaA6XFYesu_SNnvbFaBfa_Hua_8ypdCRmAgqzzjzlAyaCmmDrsKyKySiieBVaDJYBUSroPAQCcSOe4a_UjLbgqAZutqjr72PszlcwFyFHKSRT-261ZuFCGOkmYnv8D3XKiY0cnVd4LjWI1OXQ21pEEXDb2EXyxZhZtgpt4oWlb-BRGa5cRPpDB-yAzNm21ZJadZB_171XlzMtVb3-vx3mllTuIYyCKGkvXIgZlX_MHdOEezHGbtsMo3YKNhNHsc-fpstSshIf51Emaeuh3NwSArFNGvSdEeozQA9AvBJEF7AnDtiRhU2T2PEDsDA6KxUR3jhXytjRsvZW083R4C-2okuHTGLBfomw_ru-euubHgkvTN2U18kv-ZNXB3AdTxG5Ava9IOxGaUzu9SDGVzVg3o0EF2zbYepcceN378HtuzBkB8FpLjC1zGDMAfx73w5dN7FRtH0BClpPAbTzfaG93-T2d7qTo0fhkZLZXxDOHwn3ekJ5WRF0VOfkFrmtw4h-73ivzIhqnwg1wiDBLZO4uUvHo1E4S4pZLhL-6BQFedmDAmm-S89g4j7uOIczS4XxqTloYE-8SQ9U2LCn6DSQWT5o08iMWric5xQJZYNl_djgze_BuwAX3hWEHUuif3iNmpCFD2Y4aACXc",
                "e": "AQAB"
            }
        ]
    }
    
    return jsonify(jwks), 200
