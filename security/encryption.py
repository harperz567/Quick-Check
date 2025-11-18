from cryptography.fernet import Fernet
from flask import current_app
import base64

def get_cipher():
    """
    获取加密cipher
    """
    key = current_app.config['ENCRYPTION_KEY'].encode()
    # 确保key是32字节
    if len(key) < 32:
        key = key.ljust(32, b'0')
    elif len(key) > 32:
        key = key[:32]
    
    # Fernet需要base64编码的32字节key
    key = base64.urlsafe_b64encode(key)
    return Fernet(key)

def encrypt_data(plain_text: str) -> str:
    """
    加密敏感数据（如SSN、保险ID）
    """
    if not plain_text:
        return None
    
    cipher = get_cipher()
    encrypted = cipher.encrypt(plain_text.encode())
    return encrypted.decode()

def decrypt_data(encrypted_text: str) -> str:
    """
    解密数据
    """
    if not encrypted_text:
        return None
    
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_text.encode())
    return decrypted.decode()