"""
Test Epic Backend Services authentication
Run this to verify your setup is working
"""

import os
from dotenv import load_dotenv
from epic_backend_auth import EpicBackendAuth, EpicBulkExport

# Load environment variables
load_dotenv()


def test_backend_auth():
    """Test backend services authentication"""
    print("\n" + "="*60)
    print("TESTING EPIC BACKEND SERVICES AUTHENTICATION")
    print("="*60 + "\n")
    
    try:
        # Initialize auth client
        print("1. Initializing Backend Services client...")
        auth = EpicBackendAuth()
        
        # Check configuration
        print(f"   Client ID: {auth.client_id}")
        print(f"   Token URL: {auth.token_url}")
        print(f"   FHIR URL: {auth.fhir_url}")
        print(f"   Private Key: {auth.private_key_path}")
        
        if not auth.client_id:
            print("\n✗ ERROR: EPIC_BACKEND_CLIENT_ID not set in .env")
            return False
        
        # Test connection
        print("\n2. Testing connection...")
        if auth.test_connection():
            print("\n✓ SUCCESS! Backend Services authentication is working!")
            
            # Try a simple patient query
            print("\n3. Testing patient query...")
            bulk = EpicBulkExport(auth)
            patients = bulk.simple_patient_export(count=5)
            
            print(f"\n✓ Retrieved {len(patients)} test patients:")
            for i, patient in enumerate(patients[:3], 1):
                name = patient.get('name', [{}])[0]
                first = name.get('given', [''])[0]
                last = name.get('family', '')
                print(f"   {i}. {first} {last} (ID: {patient.get('id')})")
            
            print("\n" + "="*60)
            print("✓ ALL TESTS PASSED!")
            print("="*60)
            print("\nYour app is ready for automated bulk operations!")
            print("No user login required for bulk data access.")
            return True
        else:
            print("\n✗ Connection test failed")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Run 'python generate_keys.py' to create keys")
        print("2. Register public key with Epic")
        print("3. Update .env with correct credentials")
        print("4. Ensure EPIC_BACKEND_CLIENT_ID is set")
        return False


if __name__ == '__main__':
    test_backend_auth()
