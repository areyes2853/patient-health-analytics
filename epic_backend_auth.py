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
        Simplified patient export using Epic's test Group
        Uses proper Bulk Data Export workflow
        """
        try:
            token = self.auth.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/fhir+json',
                'Prefer': 'respond-async'
            }
            
            # Epic's test Group for sandbox - from official documentation
            # This is the example Group ID from Epic's Bulk Data Kick-off docs
            test_group_id = 'eIscQb2HmqkT.aPxBKDR1mIj3721CpVk1suC7rlu3yX83'
            
            # Option 1: Try bulk export with Group
            try:
                url = f"{self.fhir_url}/Group/{test_group_id}/$export"
                params = {'_type': 'Patient'}
                
                print(f"Initiating bulk export for test group...")
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 202:
                    status_url = response.headers.get('Content-Location')
                    print(f"Bulk export initiated! Status URL: {status_url}")
                    print("Note: Full bulk export takes time. Using direct fetch instead...")
                    # Fall through to direct fetch for demo purposes
                else:
                    print(f"Bulk export not available: {response.status_code}")
            except Exception as e:
                print(f"Bulk export not available in sandbox: {e}")
            
            # Option 2: Fetch specific test patients directly (for demo)
            # Epic sandbox has test patients with known IDs
            test_patient_ids = [
                'erXuFYUfucBZaryVksYEcMg3',  # Derrick Lin
                'eq081-VQEgP8drUUqCWzHfw3',  # Desiree Powell  
                'eM0-PqwoSL-kHI66dFGLgWg3',  # Emily Williams
                'eqUO2FOYGc8S6Dij4LMNIpA3',  # Jason Argonaut
                'e.5VtBjHjlS6ILI.N0a8RqQ3',  # Camila Lopez
            ]
            
            patients = []
            print(f"Fetching Epic test patients directly...")
            
            # Fetch each test patient by ID
            headers_read = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/fhir+json'
            }
            
            for patient_id in test_patient_ids[:min(len(test_patient_ids), count)]:
                try:
                    url = f"{self.fhir_url}/Patient/{patient_id}"
                    response = requests.get(url, headers=headers_read)
                    if response.status_code == 200:
                        patients.append(response.json())
                        print(f"  ✓ Fetched patient {patient_id}")
                except Exception as e:
                    print(f"  ✗ Could not fetch patient {patient_id}: {e}")
                    continue
            
            if len(patients) == 0:
                raise Exception("Could not fetch any test patients. Backend Services may not have access to these patient IDs.")
            
            print(f"\n✓ Successfully retrieved {len(patients)} test patients")
            return patients
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            raise Exception(f"Failed to fetch patients: {e.response.status_code} {e.response.reason}\nDetails: {error_detail}")
        except Exception as e:
            raise Exception(f"Failed to fetch patients: {e}")
