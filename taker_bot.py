import os
import json
import requests
from web3 import Web3
from eth_account.messages import encode_defunct
from dotenv import load_dotenv
from wallet_storage import WalletStorage
import getpass

class TakerBot:
    def __init__(self, storage_password=None):
        if storage_password is None:
            storage_password = getpass.getpass("Enter your wallet storage password: ")
        
        self.wallet_storage = WalletStorage(storage_password)
        try:
            self.private_key, self.wallet_address = self.wallet_storage.load_wallet()
        except FileNotFoundError:
            print("No stored wallet found. Please run setup_wallet.py first!")
            exit(1)
            
        self.base_url = "https://lightmining-api.taker.xyz"
        self.rpc_url = "https://rpc-mainnet.taker.xyz/"
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id,en-US;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://earn.taker.xyz',
            'Referer': 'https://earn.taker.xyz/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
            'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
        self.token = None

    def generate_nonce(self):
        """Generate nonce for wallet signing"""
        payload = {"walletAddress": self.wallet_address}
        response = self.session.post(f"{self.base_url}/wallet/generateNonce", json=payload)
        if response.status_code == 200:
            return response.json()['data']['nonce']
        raise Exception(f"Failed to generate nonce: {response.text}")

    def sign_message(self, message):
        """Sign message with wallet private key"""
        message_hash = encode_defunct(text=message)
        signed_message = self.web3.eth.account.sign_message(message_hash, private_key=self.private_key)
        return signed_message.signature.hex()

    def login(self):
        """Login with wallet signature"""
        nonce = self.generate_nonce()
        signature = self.sign_message(nonce)
        
        payload = {
            "address": self.wallet_address,
            "signature": signature,
            "message": nonce
        }
        
        response = self.session.post(f"{self.base_url}/wallet/login", json=payload)
        if response.status_code == 200:
            data = response.json()
            self.token = data['data']['token']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            return data
        raise Exception(f"Failed to login: {response.text}")

    def get_user_info(self):
        """Get user information"""
        response = self.session.get(f"{self.base_url}/user/getUserInfo")
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get user info: {response.text}")

    def get_total_mining_time(self):
        """Get total mining time"""
        response = self.session.get(f"{self.base_url}/assignment/totalMiningTime")
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get total mining time: {response.text}")

    def get_assignment_list(self):
        """Get assignment list"""
        response = self.session.post(f"{self.base_url}/assignment/list")
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get assignment list: {response.text}")

    def get_balance(self):
        """Get wallet balance using RPC"""
        payload = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "eth_getBalance",
            "params": [self.wallet_address, "latest"]
        }
        response = self.session.post(self.rpc_url, json=payload)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get balance: {response.text}")

def main():
    try:
        bot = TakerBot()
        print("Logging in...")
        login_result = bot.login()
        print(f"Login successful: {json.dumps(login_result, indent=2)}")

        print("\nGetting user info...")
        user_info = bot.get_user_info()
        print(f"User info: {json.dumps(user_info, indent=2)}")

        print("\nGetting total mining time...")
        mining_time = bot.get_total_mining_time()
        print(f"Mining time: {json.dumps(mining_time, indent=2)}")

        print("\nGetting assignment list...")
        assignments = bot.get_assignment_list()
        print(f"Assignments: {json.dumps(assignments, indent=2)}")

        print("\nGetting wallet balance...")
        balance = bot.get_balance()
        print(f"Balance: {json.dumps(balance, indent=2)}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 