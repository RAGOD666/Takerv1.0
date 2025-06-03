import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class WalletStorage:
    def __init__(self, storage_password):
        """Initialize wallet storage with a password"""
        self.storage_file = "wallet_data.enc"
        self.salt_file = "salt.key"
        self._init_encryption(storage_password)
        
    def _init_encryption(self, password):
        """Initialize encryption with password"""
        if os.path.exists(self.salt_file):
            with open(self.salt_file, "rb") as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_file, "wb") as f:
                f.write(salt)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)

    def save_wallet(self, private_key: str, address: str):
        """Save wallet credentials"""
        data = {
            "private_key": private_key,
            "address": address
        }
        encrypted_data = self.fernet.encrypt(json.dumps(data).encode())
        with open(self.storage_file, "wb") as f:
            f.write(encrypted_data)
        print("Wallet credentials saved successfully!")

    def load_wallet(self) -> tuple:
        """Load wallet credentials"""
        if not os.path.exists(self.storage_file):
            raise FileNotFoundError("No wallet data found. Please save wallet first.")
            
        with open(self.storage_file, "rb") as f:
            encrypted_data = f.read()
        
        decrypted_data = json.loads(self.fernet.decrypt(encrypted_data))
        return decrypted_data["private_key"], decrypted_data["address"]

    def delete_wallet(self):
        """Delete stored wallet data"""
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
            print("Wallet data deleted successfully!")
        else:
            print("No wallet data found.")

def setup_new_wallet():
    """Interactive function to set up new wallet storage"""
    print("\n=== Wallet Storage Setup ===")
    storage_password = input("Enter a strong password to protect your wallet storage: ")
    
    storage = WalletStorage(storage_password)
    
    print("\nEnter your wallet credentials:")
    private_key = input("Private Key (without 0x): ")
    address = input("Wallet Address (with 0x): ")
    
    storage.save_wallet(private_key, address)
    print("\nWallet credentials have been securely stored!")
    print("Please remember your storage password - it's needed to access your wallet!")

if __name__ == "__main__":
    setup_new_wallet() 