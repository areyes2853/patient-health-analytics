"""
Generate RSA public/private key pair for Epic Backend Services authentication
Run this once to create your keys, then register the public key with Epic
"""

import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def generate_keys(key_dir='./keys'):
    """
    Generate RSA-384 key pair for JWT signing
    """
    # Create keys directory if it doesn't exist
    os.makedirs(key_dir, exist_ok=True)
    
    print("Generating RSA key pair...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,  # Epic recommends 4096-bit keys
        backend=default_backend()
    )
    
    # Save private key
    private_key_path = os.path.join(key_dir, 'private_key.pem')
    with open(private_key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"✓ Private key saved to: {private_key_path}")
    print("  ⚠️  Keep this file SECRET and secure!")
    
    # Generate public key
    public_key = private_key.public_key()
    
    # Save public key (PEM format)
    public_key_path = os.path.join(key_dir, 'public_key.pem')
    with open(public_key_path, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print(f"✓ Public key saved to: {public_key_path}")
    
    # Also save in JWK format (useful for some systems)
    print("\n" + "="*60)
    print("PUBLIC KEY (to register with Epic):")
    print("="*60)
    with open(public_key_path, 'r') as f:
        print(f.read())
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Keep private_key.pem SECRET - never share or commit to git")
    print("2. Register public_key.pem with Epic's developer portal")
    print("3. Update your .env file with:")
    print(f"   PRIVATE_KEY_PATH={private_key_path}")
    print("4. Test connection with: python test_backend_auth.py")
    print("="*60)


if __name__ == '__main__':
    generate_keys()
