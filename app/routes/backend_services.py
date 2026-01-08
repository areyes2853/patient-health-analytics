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
        import traceback
        auth = get_backend_auth()
        if not auth.client_id:
            return jsonify({
                "status": "error",
                "message": "EPIC_BACKEND_CLIENT_ID is not set in the backend environment."
            }), 500
        if not auth.token_url:
            return jsonify({
                "status": "error",
                "message": "EPIC_TOKEN_URL is not set in the backend environment."
            }), 500
        if not auth.fhir_url:
            return jsonify({
                "status": "error",
                "message": "EPIC_FHIR_URL is not set in the backend environment."
            }), 500
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
        # Print full traceback to logs
        print("\n=== BACKEND AUTH ERROR ===")
        print(traceback.format_exc())
        print("========================\n")
        
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
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
                "n": "poz85kBB_vI9VyaaY0bpWYgZpqklPjriY3Hxk7tkfMzA48V0Jq4X0MybSBB5jcKgfPgXKBjNU7vDhv9nk6Y3woUsRtYvt3dPV3uIt8hDDzStr-O2LrVO0rYA35L4b78lfRnGJ71pj3IuM-7LzaiViQKAgaDL1lXQ9YP0t0q1IdFdlph_91DqOEQk3qogmG_sX3AAOYAWjYTBnZPuq_KasZvjxnEu0-v2sOW0vZAc9Oa50Vd2i_EOImLENR6Re0K9jEPvK99aTaVdrTFOPEExuLZgOHsA6--77RUEn9UHUAS2pfrcsrpRUPtCCZR_qcZ6dw_11HwoBrbfpEEaCJXzw9m66Q9s2GRi-_A6hjMy8JpZPZV5Ovfk5abyVrWgjNtLWpbAQrAy_t0D81Kkxw5z3YPi7LjJPK8_ZU-GTMwIXB93wubx0h2F8eHfvLL-cS6ugY1uyUFDzl583vWKkjoMjnWeEVjAH5epRwKIw3ZyQmmWpDg3yl_yS1Ro6kxdcpTf9wED0_7bQbZgENQuAsdwxCcCiOJ7EmkFHYD7HWyFe7XjLN6pxhwQIDUTqRIL3uS_K5h_kU6nYIihiJPOje2WG6eUrnt7Tog9wB8GI--JdsV2SnneVRY9mJTF3nrNfATqc3D2yqAx5Y4lXCyzk70L6BBrDhNvSAwM9Nth_qg4FDE",
      "e": "AQAB"
            }
        ]
    }
    
    return jsonify(jwks), 200
