import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import string

from typing import Tuple

def _generate_password(length: int = 12) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Length of the password
        
    Returns:
        Secure random password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def salt_key(master_key: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode('utf-8')))
    return key

def encrypt_private_key(private_key: str, master_key: str) -> str:
    """
    Encrypt a private key for database storage.
    
    Args:
        private_key: The private key to encrypt
        master_key: The master password or key used for encryption
        
    Returns:
        An encrypted string in the format: salt:encrypted_data (base64 encoded)
    """
    salt = os.urandom(16)
    key = salt_key(master_key, salt)
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(private_key.encode('utf-8'))
    result = base64.b64encode(salt + encrypted_data).decode('utf-8')
    return result

def decrypt_private_key(encrypted_data: str, master_key: str) -> str:
    """
    Decrypt an encrypted private key.
    
    Args:
        encrypted_data: The encrypted private key string
        master_key: The master password or key used for decryption
        
    Returns:
        The decrypted private key
        
    Raises:
        ValueError: If the encrypted data is invalid or has been tampered with
    """
    data = base64.b64decode(encrypted_data)
    salt = data[:16]
    token = data[16:]
    key = salt_key(master_key, salt)
    cipher = Fernet(key)
    try:
        plaintext = cipher.decrypt(token)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
