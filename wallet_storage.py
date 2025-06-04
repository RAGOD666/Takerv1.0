import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from web3 import Web3

class WalletStorage:
    def __init__(self, storage_password):
        """Initialize wallet storage with encryption"""
        self.storage_file = "wallets_data.enc"
        self.salt_file = "wallet_salt.key"
        self._init_encryption(storage_password)
        self.web3 = Web3(Web3.HTTPProvider("https://rpc-mainnet.taker.xyz/"))
        
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

    def _load_wallets(self):
        """Load all stored wallets"""
        if not os.path.exists(self.storage_file):
            return {}
            
        with open(self.storage_file, "rb") as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = json.loads(self.fernet.decrypt(encrypted_data))
            return decrypted_data
        except:
            return {}

    def _save_wallets(self, wallets_data):
        """Save all wallets data"""
        encrypted_data = self.fernet.encrypt(json.dumps(wallets_data).encode())
        with open(self.storage_file, "wb") as f:
            f.write(encrypted_data)

    def _get_next_wallet_number(self):
        """Get next available wallet number"""
        wallets = self._load_wallets()
        existing_numbers = [int(name.split('_')[1]) for name in wallets.keys() if name.startswith('Wallet_')]
        return max(existing_numbers, default=0) + 1

    def _validate_private_key(self, private_key: str) -> tuple:
        """Validate private key and return (private_key, address)"""
        try:
            # Remove '0x' prefix if present
            clean_key = private_key.strip().replace('0x', '')
            
            # Validate key length
            if len(clean_key) != 64:
                raise ValueError("Invalid private key length")
                
            # Validate hex format
            int(clean_key, 16)
            
            # Get address from private key
            account = self.web3.eth.account.from_key(clean_key)
            return clean_key, account.address
            
        except ValueError as e:
            raise ValueError(f"Invalid private key format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error validating private key: {str(e)}")

    def add_wallet(self, private_key: str) -> str:
        """Add a single wallet and return its name"""
        clean_key, address = self._validate_private_key(private_key)
        
        wallets = self._load_wallets()
        
        # Check if wallet already exists
        for name, data in wallets.items():
            if data['address'].lower() == address.lower():
                raise ValueError(f"Wallet already exists as {name}")
        
        wallet_number = self._get_next_wallet_number()
        wallet_name = f"Wallet_{wallet_number}"
        
        wallets[wallet_name] = {
            'private_key': clean_key,
            'address': address
        }
        
        self._save_wallets(wallets)
        print(f"Added {wallet_name}: {address}")
        return wallet_name

    def bulk_add_wallets(self, private_keys: str) -> tuple:
        """Add multiple wallets from comma-separated private keys
        Returns tuple of (success_count, failed_count, errors)
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        # Split and clean private keys
        keys = [key.strip() for key in private_keys.split(',') if key.strip()]
        
        for key in keys:
            try:
                self.add_wallet(key)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to add wallet with key ending in ...{key[-8:]}: {str(e)}")
        
        return success_count, failed_count, errors

    def get_wallet(self, wallet_name: str) -> tuple:
        """Get wallet private key and address"""
        wallets = self._load_wallets()
        if wallet_name not in wallets:
            raise ValueError(f"Wallet {wallet_name} not found")
            
        wallet = wallets[wallet_name]
        return wallet['private_key'], wallet['address']

    def remove_wallet(self, wallet_name: str):
        """Remove a wallet"""
        wallets = self._load_wallets()
        if wallet_name in wallets:
            del wallets[wallet_name]
            self._save_wallets(wallets)
            print(f"Removed wallet {wallet_name}")
        else:
            print(f"Wallet {wallet_name} not found")

    def bulk_remove_wallets(self, selection: str) -> tuple:
        """Remove multiple wallets based on selection string
        Selection format can be:
        - Range: "1-5" (removes wallets 1 through 5)
        - Specific: "1,3,5" (removes wallets 1, 3, and 5)
        - Mixed: "1-3,5,7-9" (removes wallets 1,2,3,5,7,8,9)
        Returns tuple of (success_count, failed_count, errors)
        """
        success_count = 0
        failed_count = 0
        errors = []
        wallets = self._load_wallets()
        
        # Get all wallet numbers for validation
        wallet_numbers = {}  # number -> wallet_name mapping
        for name in wallets.keys():
            try:
                if name.startswith("Wallet_"):
                    num = int(name.split("_")[1])
                    wallet_numbers[num] = name
            except (IndexError, ValueError):
                continue
        
        # Parse selection string
        to_remove = set()  # set of wallet numbers to remove
        parts = selection.replace(" ", "").split(",")
        
        for part in parts:
            try:
                if "-" in part:
                    # Handle range (e.g., "1-5")
                    start, end = map(int, part.split("-"))
                    if start > end:
                        start, end = end, start
                    to_remove.update(range(start, end + 1))
                else:
                    # Handle single number
                    to_remove.add(int(part))
            except ValueError:
                errors.append(f"Invalid selection format: {part}")
                continue
        
        # Remove selected wallets
        removed_names = set()  # track removed wallets to avoid duplicates
        for num in to_remove:
            wallet_name = wallet_numbers.get(num)
            if wallet_name and wallet_name not in removed_names:
                try:
                    del wallets[wallet_name]
                    removed_names.add(wallet_name)
                    success_count += 1
                    print(f"Removed {wallet_name}")
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Failed to remove {wallet_name}: {str(e)}")
            else:
                failed_count += 1
                errors.append(f"Wallet_{num} not found")
        
        if success_count > 0:
            self._save_wallets(wallets)
            
        return success_count, failed_count, errors

    def list_wallets(self) -> list:
        """List all stored wallets"""
        wallets = self._load_wallets()
        
        # Sort wallets by number
        sorted_wallets = []
        for name, data in wallets.items():
            try:
                if name.startswith("Wallet_"):
                    num = int(name.split("_")[1])
                    sorted_wallets.append((num, name, data['address']))
            except (IndexError, ValueError):
                # Handle non-standard wallet names
                sorted_wallets.append((float('inf'), name, data['address']))
        
        sorted_wallets.sort()  # Sort by number
        return [(name, addr) for _, name, addr in sorted_wallets]

def setup_new_wallet():
    """Interactive function to set up new wallet storage"""
    print("\n=== Wallet Storage Setup ===")
    storage_password = input("Enter a strong password to protect your wallet storage: ")
    
    storage = WalletStorage(storage_password)
    
    while True:
        print("\nEnter wallet details (or press Enter to finish):")
        private_key = input("Private Key: ").strip()
        
        if not private_key:
            break
            
        try:
            wallet_name = storage.add_wallet(private_key)
        except ValueError as e:
            print(f"\nError: {str(e)}")
            continue
            
        add_another = input("\nAdd another wallet? (y/n): ").lower()
        if add_another != 'y':
            break
    
    print("\nWallet setup completed!")
    print("Please remember your storage password - it's needed to access your wallets!")

if __name__ == "__main__":
    setup_new_wallet() 