import requests
import json
from requests.auth import HTTPBasicAuth
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
            params = {'patient': patient_id}
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
    """Generate Epic OAuth2 authorization URL"""
    client_id = os.getenv('EPIC_CLIENT_ID')
    redirect_uri = os.getenv('REDIRECT_URI')
    auth_url = os.getenv('EPIC_AUTH_URL')
    
    scope = 'patient/Patient.read patient/Observation.read'
    
    return f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    try:
        token_url = os.getenv('EPIC_TOKEN_URL')
        client_id = os.getenv('EPIC_CLIENT_ID')
        redirect_uri = os.getenv('REDIRECT_URI')
        
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