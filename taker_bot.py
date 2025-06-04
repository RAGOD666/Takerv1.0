import os
import json
import requests
import time
from web3 import Web3
from eth_account.messages import encode_defunct
from dotenv import load_dotenv

class TakerBot:
    def __init__(self, private_key: str, proxy_settings: dict = None):
        """Initialize TakerBot with credentials and optional proxy"""
        self.base_url = "https://lightmining-api.taker.xyz"
        
        # Configure Web3 with proxy if provided
        if proxy_settings:
            provider_url = "https://rpc-mainnet.taker.xyz/"
            session = requests.Session()
            session.proxies = proxy_settings
            self.web3 = Web3(Web3.HTTPProvider(provider_url, session=session))
        else:
            self.web3 = Web3(Web3.HTTPProvider("https://rpc-mainnet.taker.xyz/"))
            
        self.private_key = private_key.replace('0x', '')
        self.wallet_address = self._get_address()
        
        # Configure session with proxy if provided
        self.session = requests.Session()
        if proxy_settings:
            self.session.proxies = proxy_settings
            
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id,en-US;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://earn.taker.xyz',
            'Referer': 'https://earn.taker.xyz/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.token = None
        self.mining_contract = "0xB3eFE5105b835E5Dd9D206445Dbd66DF24b912AB"
        self.multicall_contract = "0x499f9C7A4aa2c660931dB3bfcd092194F492a92f"
        
    def _get_address(self) -> str:
        """Get wallet address from private key"""
        account = self.web3.eth.account.from_key(self.private_key)
        return account.address

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
        
    def login(self) -> dict:
        """Login to Taker Protocol"""
        try:
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
            raise Exception(f"Login failed: {response.text}")
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")

    def get_user_info(self) -> dict:
        """Get user information"""
        try:
            response = self.session.get(f"{self.base_url}/user/getUserInfo")
            if response.status_code == 200:
                return response.json()
            raise Exception(f"Failed to get user info: {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")

    def get_total_mining_time(self) -> dict:
        """Get total mining time"""
        try:
            response = self.session.get(f"{self.base_url}/assignment/totalMiningTime")
            if response.status_code == 200:
                return response.json()
            raise Exception(f"Failed to get mining time: {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get mining time: {str(e)}")

    def get_assignment_list(self) -> dict:
        """Get list of available assignments"""
        try:
            response = self.session.post(f"{self.base_url}/assignment/list")
            if response.status_code == 200:
                return response.json()
            raise Exception(f"Failed to get assignments: {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get assignments: {str(e)}")

    def get_balance(self) -> dict:
        """Get wallet balance"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "eth_getBalance",
                "params": [self.wallet_address, "latest"]
            }
            response = requests.post("https://rpc-mainnet.taker.xyz/", json=payload)
            if response.status_code == 200:
                return response.json()
            raise Exception(f"Failed to get balance: {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get balance: {str(e)}")

    def check_mining_status(self) -> bool:
        """Check if mining is active"""
        try:
            # Step 1: Check mining status via eth_call
            payload = {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "eth_call",
                "params": [{
                    "data": "0x02fb0c5e",
                    "from": self.wallet_address,
                    "to": self.mining_contract
                }, "latest"]
            }
            response = requests.post("https://rpc-mainnet.taker.xyz/", json=payload)
            if response.status_code != 200:
                raise Exception("Failed to check mining status")

            # Also check API status
            mining_time = self.get_total_mining_time()
            last_mining_time = mining_time['data']['lastMiningTime']
            current_time = int(time.time())
            
            # Mining is active if last mining time is within 24 hours
            return (current_time - last_mining_time) < 24 * 60 * 60

        except Exception as e:
            raise Exception(f"Failed to check mining status: {str(e)}")

    def activate_mining(self) -> bool:
        """Activate mining process"""
        try:
            # Step 1: Build transaction
            nonce = self.web3.eth.get_transaction_count(self.wallet_address)
            transaction = {
                'nonce': nonce,
                'gasPrice': 1000000,  # 0xf4240 from the example
                'gas': 73000,  # 0x11d19 from the example
                'to': self.mining_contract,
                'value': 0,
                'data': '0x02fb0c5e',  # Function signature for activating mining
                'chainId': 1125  # 0x465 Taker chain ID
            }

            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt['status'] != 1:
                raise Exception("Transaction failed")

            # Step 2: Get block number
            block_number = self.web3.eth.block_number

            # Step 3: Get transaction details
            tx_details = self.web3.eth.get_transaction(tx_hash)
            tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)

            # Step 4: Start mining via API
            payload = {"status": False}
            response = self.session.post(f"{self.base_url}/assignment/startMining", json=payload)
            if response.status_code != 200:
                raise Exception("Failed to start mining on API")

            # Step 5: Verify mining started
            mining_time = self.get_total_mining_time()
            if not mining_time['data']['lastMiningTime']:
                raise Exception("Mining did not start properly")

            return True

        except Exception as e:
            raise Exception(f"Failed to activate mining: {str(e)}")

if __name__ == "__main__":
    print("This module should not be run directly. Please use main.py instead.") 