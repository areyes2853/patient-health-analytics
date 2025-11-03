"""
Epic Backend Services (System-to-System) Authentication
Uses JWT-based authentication for automated bulk data access without user login
"""

import jwt
import time
import uuid
import requests
import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class EpicBackendAuth:
    """
    Handles Backend Services authentication for Epic FHIR
    No user login required - perfect for bulk data operations
    """
    
    def __init__(self):
        self.client_id = os.getenv('EPIC_BACKEND_CLIENT_ID')
        self.token_url = os.getenv('EPIC_TOKEN_URL')
        self.fhir_url = os.getenv('EPIC_FHIR_URL')
        self.private_key_path = os.getenv('PRIVATE_KEY_PATH', './keys/private_key.pem')
        self.access_token = None
        self.token_expiry = None
        
    def load_private_key(self):
        """Load RSA private key from file or environment variable"""
        try:
            # First try environment variable (for production)
            private_key_pem = os.getenv('PRIVATE_KEY_PEM')
            if private_key_pem:
                # Handle both formats: literal \n and actual newlines
                if '\\n' in private_key_pem:
                    # Convert literal \n to actual newlines
                    private_key_pem = private_key_pem.replace('\\n', '\n')
                
                # Clean up the key (remove extra whitespace)
                private_key_pem = private_key_pem.strip()
                
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
                print("✓ Loaded private key from environment variable")
                return private_key
            
            # Fallback to file (for local development)
            with open(self.private_key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            print(f"✓ Loaded private key from file: {self.private_key_path}")
            return private_key
        except FileNotFoundError:
            raise Exception(f"Private key not found at {self.private_key_path} and PRIVATE_KEY_PEM env var not set. Run generate_keys.py first.")
        except Exception as e:
            raise Exception(f"Error loading private key: {e}")
    
    def create_jwt_assertion(self):
        """
        Create JWT assertion for client authentication
        This is signed with your private key
        """
        private_key = self.load_private_key()
        
        # JWT claims
        now = int(time.time())
        claims = {
            'iss': self.client_id,  # Issuer: your client ID
            'sub': self.client_id,  # Subject: your client ID
            'aud': self.token_url,  # Audience: Epic's token endpoint
            'jti': str(uuid.uuid4()),  # Unique identifier for this JWT
            'exp': now + 300,  # Expires in 5 minutes
            'iat': now  # Issued at
        }
        
        # Sign JWT with private key
        jwt_token = jwt.encode(
            claims,
            private_key,
            algorithm='RS384',  # Epic uses RS384
            headers={'kid': 'epic-backend-key'}  # Key ID
        )
        
        return jwt_token
    
    def get_access_token(self, force_refresh=False):
        """
        Get access token using Backend Services authentication
        Token is cached and reused until it expires
        """
        # Return cached token if still valid
        if not force_refresh and self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                print("Using cached access token")
                return self.access_token
        
        try:
            # Create JWT assertion
            jwt_assertion = self.create_jwt_assertion()
            
            # Request access token
            data = {
                'grant_type': 'client_credentials',
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': jwt_assertion,
                'scope': 'system/Patient.read system/Observation.read system/*.read'
            }
            
            print(f"Requesting access token from: {self.token_url}")
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiry (usually 15 minutes, we'll refresh 1 minute early)
            expires_in = token_data.get('expires_in', 900)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            
            print(f"✓ Access token obtained (expires in {expires_in}s)")
            return self.access_token
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to get access token: {error_detail}")
        except Exception as e:
            raise Exception(f"Authentication error: {e}")
    
    def test_connection(self):
        """Test the backend services connection"""
        try:
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/fhir+json'
            }
            
            # Test with a simple metadata query
            response = requests.get(f"{self.fhir_url}/metadata", headers=headers)
            response.raise_for_status()
            
            print("✓ Backend Services authentication successful!")
            return True
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False


class EpicBulkExport:
    """
    Handles FHIR Bulk Data Export operations
    Uses Backend Services authentication
    """
    
    def __init__(self, auth_client):
        self.auth = auth_client
        self.fhir_url = auth_client.fhir_url
    
    def initiate_export(self, resource_type='Patient', params=None):
        """
        Initiate a bulk data export
        Returns a Content-Location URL to check status
        """
        try:
            token = self.auth.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/fhir+json',
                'Prefer': 'respond-async'  # Required for bulk export
            }
            
            # Build export URL
            export_url = f"{self.fhir_url}/{resource_type}/$export"
            
            # Optional parameters
            if params:
                export_url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            
            print(f"Initiating bulk export: {export_url}")
            response = requests.get(export_url, headers=headers)
            
            if response.status_code == 202:  # Accepted
                status_url = response.headers.get('Content-Location')
                print(f"✓ Export initiated. Status URL: {status_url}")
                return status_url
            else:
                raise Exception(f"Export initiation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Failed to initiate export: {e}")
    
    def check_export_status(self, status_url):
        """
        Check the status of a bulk export operation
        Returns 'in-progress', 'complete', or error
        """
        try:
            token = self.auth.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/fhir+json'
            }
            
            response = requests.get(status_url, headers=headers)
            
            if response.status_code == 202:
                # Still processing
                retry_after = response.headers.get('Retry-After', 'unknown')
                return {
                    'status': 'in-progress',
                    'retry_after': retry_after
                }
            elif response.status_code == 200:
                # Complete!
                return {
                    'status': 'complete',
                    'data': response.json()
                }
            else:
                return {
                    'status': 'error',
                    'message': response.text
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def download_export_file(self, file_url):
        """
        Download an ndjson file from bulk export
        Returns the data as a list of FHIR resources
        """
        try:
            token = self.auth.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            
            # Parse ndjson (newline-delimited JSON)
            resources = []
            for line in response.text.strip().split('\n'):
                if line:
                    resources.append(eval(line))  # or use json.loads(line)
            
            return resources
            
        except Exception as e:
            raise Exception(f"Failed to download export file: {e}")
    
    def simple_patient_export(self, count=100):
        """
        Simplified patient export using standard search
        (When full bulk export is not available in sandbox)
        """
        try:
            token = self.auth.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/fhir+json'
            }
            
            url = f"{self.fhir_url}/Patient"
            params = {'_count': count}
            
            print(f"Fetching {count} patients...")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            patients = []
            
            for entry in data.get('entry', []):
                resource = entry.get('resource', {})
                patients.append(resource)
            
            print(f"✓ Retrieved {len(patients)} patients")
            return patients
            
        except Exception as e:
            raise Exception(f"Failed to fetch patients: {e}")
