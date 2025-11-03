"""
Convert PEM public key to JWK format
Epic Backend Services requires JWK format if using JWK Set URL
"""

import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import base64


def pem_to_jwk(pem_file_path, key_id='epic-backend-key'):
    """
    Convert PEM public key to JWK (JSON Web Key) format
    """
    # Read the PEM file
    with open(pem_file_path, 'rb') as f:
        pem_data = f.read()
    
    # Load the public key
    public_key = serialization.load_pem_public_key(
        pem_data,
        backend=default_backend()
    )
    
    # Get the public numbers
    public_numbers = public_key.public_numbers()
    
    # Convert to base64url (no padding)
    def int_to_base64url(num):
        num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
        return base64.urlsafe_b64encode(num_bytes).rstrip(b'=').decode('utf-8')
    
    # Create JWK
    jwk = {
        "kty": "RSA",
        "kid": key_id,
        "use": "sig",
        "alg": "RS384",
        "n": int_to_base64url(public_numbers.n),
        "e": int_to_base64url(public_numbers.e)
    }
    
    return jwk


def create_jwks(pem_file_path='./keys/public_key.pem', output_file='./keys/jwks.json'):
    """
    Create a JWKS (JSON Web Key Set) file
    This is what Epic expects at your JWK Set URL
    """
    jwk = pem_to_jwk(pem_file_path)
    
    jwks = {
        "keys": [jwk]
    }
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(jwks, f, indent=2)
    
    print(f"✓ JWKS file created: {output_file}")
    print("\nContents:")
    print(json.dumps(jwks, indent=2))
    
    return jwks


if __name__ == '__main__':
    import os
    
    pem_path = './keys/public_key.pem'
    
    if not os.path.exists(pem_path):
        print("❌ Public key not found!")
        print("Run: python generate_keys.py first")
        exit(1)
    
    print("Converting PEM to JWK format...")
    jwks = create_jwks(pem_path)
    
    print("\n" + "="*60)
    print("✓ Conversion complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. This JWK will be hosted at: /api/backend/.well-known/jwks.json")
    print("2. In Epic, enter your JWK Set URL:")
    print("   https://health-analytics.duckdev.me/api/backend/.well-known/jwks.json")
    print("3. Epic will fetch this file to verify your signatures")
