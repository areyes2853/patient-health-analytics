import requests
import json
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
import os
from datetime import datetime

class EpicFHIRClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.fhir_url = os.getenv('EPIC_FHIR_URL', 'https://fhirauth.patientdev.repldev.rep/api/FHIR/R4')
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/fhir+json'
        }
    
    def search_patients(self, count=5):
        """Search for patients from Epic"""
        try:
            url = f"{self.fhir_url}/Patient"
            params = {'_count': count}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching patients: {e}")
            return None
    
    def get_patient_observations(self, patient_id):
        """Get observations (labs, vitals) for a patient"""
        try:
            url = f"{self.fhir_url}/Observation"
            params = {'patient': patient_id,
                      'category': 'laboratory'
                      }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching observations: {e}")
            return None
    
    def get_patient_details(self, patient_id):
        """Get specific patient demographics"""
        try:
            url = f"{self.fhir_url}/Patient/{patient_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching patient details: {e}")
            return None

def get_epic_auth_url():
    """Generate Epic OAuth2 authorization URL with proper URL encoding"""
    client_id = os.getenv('EPIC_CLIENT_ID')
    redirect_uri = os.getenv('REDIRECT_URI')
    auth_url = os.getenv('EPIC_AUTH_URL')
    
    scope = 'patient/Patient.read patient/Observation.read'
    
    # URL-encode the redirect_uri - this is crucial for OAuth!
    # Epic requires the redirect_uri to be properly encoded in the query string
    encoded_redirect_uri = quote(redirect_uri, safe='')
    
    print(f"\n=== EPIC AUTH URL DEBUG ===")
    print(f"Client ID: {client_id}")
    print(f"Raw redirect_uri: {redirect_uri}")
    print(f"Encoded redirect_uri: {encoded_redirect_uri}")
    print(f"Auth URL base: {auth_url}")
    
    full_url = f"{auth_url}?client_id={client_id}&redirect_uri={encoded_redirect_uri}&response_type=code&scope={scope}"
    print(f"Full auth URL: {full_url}")
    print(f"=== END DEBUG ===\n")
    
    return full_url

def save_observations_to_db(conn, patient_id, fhir_patient_id, observations_data):
    """Save observations to database"""
    try:
        cursor = conn.cursor()
        
        for obs in observations_data:
            query = """
            INSERT INTO patient_observations 
            (patient_id, fhir_patient_id, test_name, test_code, value, unit, observation_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                patient_id,
                fhir_patient_id,
                obs.get('code', 'Unknown'),
                obs.get('code', ''),
                str(obs.get('value', 'N/A')),
                obs.get('unit', ''),
                obs.get('date', None)
            ))
        
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error saving observations: {e}")
        conn.rollback()
        return False
    
def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    try:
        token_url = os.getenv('EPIC_TOKEN_URL')
        client_id = os.getenv('EPIC_CLIENT_ID')
        redirect_uri = os.getenv('REDIRECT_URI')
        
        print(f"\n=== TOKEN EXCHANGE DEBUG ===")
        print(f"Token URL: {token_url}")
        print(f"Code: {code}")
        print(f"Redirect URI: {redirect_uri}")
        print(f"=== END DEBUG ===\n")
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error exchanging code: {e}")
        return None