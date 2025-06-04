import os
import json
import base64
import csv
import urllib.parse
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def parse_proxy_url(url: str) -> dict:
    """Parse proxy URL into components
    Supports formats:
    - protocol://username:password@host:port
    - protocol://host:port
    """
    try:
        # Remove spaces
        url = url.strip()
        
        # Split protocol
        if "://" not in url:
            raise ValueError("Invalid URL format. Must include '://'")
        protocol, rest = url.split("://", 1)
        
        # Clean protocol
        protocol = protocol.lower()
        if protocol not in ['http', 'https', 'socks5']:
            raise ValueError("Protocol must be http, https, or socks5")
            
        # Split authentication and host
        if "@" in rest:
            auth, host_port = rest.rsplit("@", 1)
            # Handle special characters in username/password
            if ":" not in auth:
                raise ValueError("Invalid authentication format")
            username, password = auth.split(":", 1)
            username = urllib.parse.unquote(username)
            password = urllib.parse.unquote(password)
        else:
            host_port = rest
            username = password = ""
            
        # Split host and port
        if ":" not in host_port:
            raise ValueError("Missing port number")
        host, port = host_port.rsplit(":", 1)
        
        # Validate port
        if not port.isdigit():
            raise ValueError("Port must be a number")
            
        return {
            'protocol': protocol,
            'host': host,
            'port': port,
            'username': username,
            'password': password
        }
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Invalid proxy URL format: {str(e)}")

def format_proxy_url(proxy_data: dict) -> str:
    """Format proxy data into displayable URL (hiding password)"""
    if not proxy_data:
        return "No proxy"
        
    # If proxy_data is already in URL format (contains 'http' or 'https')
    if isinstance(proxy_data, dict) and 'http' in proxy_data:
        return proxy_data['http'].replace('://', '://****@') if '@' in proxy_data['http'] else proxy_data['http']
        
    auth = ""
    if proxy_data.get('username'):
        # URL encode username and password
        username = urllib.parse.quote(proxy_data['username'])
        auth = f"{username}:****@"
        
    return f"{proxy_data['protocol']}://{auth}{proxy_data['host']}:{proxy_data['port']}"

class ProxyStorage:
    def __init__(self, storage_password):
        """Initialize proxy storage with encryption"""
        self.storage_file = "proxies_data.enc"
        self.salt_file = "proxy_salt.key"
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

    def _load_proxies(self):
        """Load all stored proxies"""
        if not os.path.exists(self.storage_file):
            return {}
            
        with open(self.storage_file, "rb") as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = json.loads(self.fernet.decrypt(encrypted_data))
            return decrypted_data
        except:
            return {}

    def _save_proxies(self, proxies_data):
        """Save all proxies data"""
        encrypted_data = self.fernet.encrypt(json.dumps(proxies_data).encode())
        with open(self.storage_file, "wb") as f:
            f.write(encrypted_data)

    def add_proxy(self, proxy_data: dict):
        """Add a proxy configuration without wallet assignment"""
        proxies = self._load_proxies()
        
        # Generate unique key for unassigned proxy
        proxy_key = f"proxy_{len(proxies) + 1}"
        while proxy_key in proxies:
            proxy_key = f"proxy_{int(proxy_key.split('_')[1]) + 1}"
        
        proxies[proxy_key] = proxy_data
        self._save_proxies(proxies)
        print(f"Added proxy: {format_proxy_url(proxy_data)}")

    def get_proxy(self, wallet_address: str) -> dict:
        """Get proxy settings for a wallet"""
        proxies = self._load_proxies()
        proxy_data = proxies.get(wallet_address.lower())
        
        if not proxy_data:
            return None
            
        # Format proxy URL
        auth = f"{proxy_data['username']}:{proxy_data['password']}@" if proxy_data.get('username') else ""
        proxy_url = f"{proxy_data['protocol']}://{auth}{proxy_data['host']}:{proxy_data['port']}"
        
        # Return in requests format
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    def remove_proxy(self, wallet_address: str):
        """Remove proxy for a wallet"""
        proxies = self._load_proxies()
        if wallet_address.lower() in proxies:
            del proxies[wallet_address.lower()]
            self._save_proxies(proxies)
            print(f"Proxy removed for wallet {wallet_address}")
        else:
            print(f"No proxy found for wallet {wallet_address}")

    def list_proxies(self) -> list:
        """List all stored proxies"""
        proxies = self._load_proxies()
        return [(addr, data) for addr, data in proxies.items()]

    def get_proxy_stats(self) -> dict:
        """Get statistics about proxy usage"""
        proxies = self._load_proxies()
        
        # Count unique proxy configurations
        unique_configs = {}
        unassigned_count = 0
        assigned_count = 0
        
        for key, data in proxies.items():
            # Create a unique key for the proxy configuration
            proxy_key = f"{data['protocol']}://{data['host']}:{data['port']}"
            if data.get('username'):
                proxy_key = f"{data['protocol']}://{data['username']}:****@{data['host']}:{data['port']}"
            
            if key.startswith('proxy_'):
                unassigned_count += 1
            else:
                assigned_count += 1
            
            if proxy_key not in unique_configs:
                unique_configs[proxy_key] = {'count': 0, 'wallets': []}
            
            unique_configs[proxy_key]['count'] += 1
            if not key.startswith('proxy_'):
                unique_configs[proxy_key]['wallets'].append(key)
        
        return {
            'total_proxies': len(unique_configs),
            'assigned_wallets': assigned_count,
            'unassigned_proxies': unassigned_count,
            'proxy_usage': {proxy: len(wallets['wallets']) for proxy, wallets in unique_configs.items()}
        }

    def auto_assign_proxies(self, wallet_addresses: list) -> tuple:
        """Automatically assign proxies to wallets in sequence"""
        success_count = 0
        failed_count = 0
        errors = []
        
        # Get all proxy configurations
        proxies = self._load_proxies()
        all_proxy_data = []
        
        # First, collect unassigned proxies
        for key, data in proxies.items():
            if key.startswith('proxy_'):
                # Ensure proxy data has all required fields
                if isinstance(data, dict) and all(k in data for k in ['protocol', 'host', 'port']):
                    all_proxy_data.append(data)
                else:
                    print(f"Warning: Skipping invalid proxy data format: {data}")
        
        if not all_proxy_data:
            return 0, 0, ["No valid proxies available"]
        
        # Start with a clean slate - remove all wallet assignments but keep unassigned proxies
        new_proxies = {}
        
        # Assign proxies to wallets in sequence
        for i, wallet_address in enumerate(wallet_addresses):
            try:
                # Use modulo to cycle through proxies if more wallets than proxies
                proxy_data = all_proxy_data[i % len(all_proxy_data)]
                # Make a deep copy to avoid reference issues
                new_proxy_data = {
                    'protocol': proxy_data['protocol'],
                    'host': proxy_data['host'],
                    'port': proxy_data['port'],
                    'username': proxy_data.get('username', ''),
                    'password': proxy_data.get('password', '')
                }
                new_proxies[wallet_address.lower()] = new_proxy_data
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to assign proxy to {wallet_address}: {str(e)}")
        
        # Add back the unassigned proxies
        for key, data in proxies.items():
            if key.startswith('proxy_'):
                new_proxies[key] = data
        
        if success_count > 0:
            self._save_proxies(new_proxies)
            
        return success_count, failed_count, errors

    def bulk_add_proxies(self, proxy_list: list) -> tuple:
        """Add multiple proxies at once
        proxy_list format: list of dicts with format:
        {
            'wallet_address': 'address',
            'protocol': 'http/https/socks5',
            'host': 'proxy.example.com',
            'port': '8080',
            'username': 'user',  # optional
            'password': 'pass'   # optional
        }
        Returns tuple of (success_count, failed_count, errors)
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        proxies = self._load_proxies()
        
        for proxy in proxy_list:
            try:
                if not all(k in proxy for k in ['wallet_address', 'protocol', 'host', 'port']):
                    raise ValueError("Missing required fields")
                    
                if proxy['protocol'] not in ['http', 'https', 'socks5']:
                    raise ValueError(f"Invalid protocol: {proxy['protocol']}")
                    
                wallet_address = proxy['wallet_address'].lower()
                proxy_data = {
                    'protocol': proxy['protocol'],
                    'host': proxy['host'],
                    'port': proxy['port'],
                    'username': proxy.get('username', ''),
                    'password': proxy.get('password', '')
                }
                
                proxies[wallet_address] = proxy_data
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to add proxy for {proxy.get('wallet_address', 'unknown')}: {str(e)}")
                
        if success_count > 0:
            self._save_proxies(proxies)
            
        return success_count, failed_count, errors

    def import_proxies_from_csv(self, csv_file: str) -> tuple:
        """Import proxies from a CSV file
        CSV format:
        wallet_address,protocol,host,port,username,password
        Returns tuple of (success_count, failed_count, errors)
        """
        proxy_list = []
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    proxy_list.append({
                        'wallet_address': row['wallet_address'],
                        'protocol': row['protocol'],
                        'host': row['host'],
                        'port': row['port'],
                        'username': row.get('username', ''),
                        'password': row.get('password', '')
                    })
                    
            return self.bulk_add_proxies(proxy_list)
            
        except Exception as e:
            return 0, 0, [f"Failed to read CSV file: {str(e)}"]

    def import_proxies_from_json(self, json_file: str) -> tuple:
        """Import proxies from a JSON file
        JSON format: list of objects with fields:
        {
            "wallet_address": "address",
            "protocol": "http/https/socks5",
            "host": "proxy.example.com",
            "port": "8080",
            "username": "user",  # optional
            "password": "pass"   # optional
        }
        Returns tuple of (success_count, failed_count, errors)
        """
        try:
            with open(json_file, 'r') as f:
                proxy_list = json.load(f)
                
            if not isinstance(proxy_list, list):
                return 0, 0, ["Invalid JSON format: root must be an array"]
                
            return self.bulk_add_proxies(proxy_list)
            
        except Exception as e:
            return 0, 0, [f"Failed to read JSON file: {str(e)}"]

    def bulk_add_proxies_from_urls(self, proxy_urls: str) -> tuple:
        """Add multiple proxies from comma-separated URLs
        Returns tuple of (success_count, failed_count, errors)
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        # Split and clean URLs
        urls = [url.strip() for url in proxy_urls.split(',') if url.strip()]
        
        for url in urls:
            try:
                proxy_data = parse_proxy_url(url)
                self.add_proxy(proxy_data)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to add proxy {url}: {str(e)}")
        
        return success_count, failed_count, errors

    def get_unassigned_proxies(self) -> list:
        """Get list of proxies not assigned to any wallet"""
        proxies = self._load_proxies()
        return [data for key, data in proxies.items() if key.startswith('proxy_')]

    def add_proxy(self, proxy_data: dict):
        """Add a proxy configuration without wallet assignment"""
        proxies = self._load_proxies()
        
        # Generate unique key for unassigned proxy
        proxy_key = f"proxy_{len(proxies) + 1}"
        while proxy_key in proxies:
            proxy_key = f"proxy_{int(proxy_key.split('_')[1]) + 1}"
        
        proxies[proxy_key] = proxy_data
        self._save_proxies(proxies)
        print(f"Added proxy: {format_proxy_url(proxy_data)}") 