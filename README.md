# Taker Protocol Bot v1.0

Automated bot for interacting with Taker Protocol's Lite Mining platform. This bot provides a secure and convenient way to manage your Taker Protocol mining activities.

## Features

- 🔐 Secure wallet storage with encryption
- 🤖 Automated login with EVM wallet signatures
- 📊 Real-time mining status monitoring
- 📋 Task management and tracking
- 💰 Wallet balance checking
- 👥 User information display

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RAGOD666/Takerv1.0.git
cd Takerv1.0
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Initial Setup

1. Run the wallet setup script:
```bash
python setup_wallet.py
```

2. Follow the prompts to:
   - Enter a strong storage password
   - Input your wallet's private key (without 0x)
   - Input your wallet address (with 0x)

## Usage

Run the main bot interface:
```bash
python main.py
```

### Available Commands

1. Login to Taker Protocol
2. Show User Information
3. Check Mining Status
4. View Available Assignments
5. Check Wallet Balance

## Security

- Private keys are encrypted using Fernet (AES)
- Password protection with PBKDF2 and salt
- Secure storage of credentials
- No plaintext storage of sensitive data

## File Structure

- `main.py` - Main bot interface
- `taker_bot.py` - Core bot functionality
- `wallet_storage.py` - Secure wallet storage
- `setup_wallet.py` - Initial wallet setup
- `requirements.txt` - Python dependencies

## Contributing

Feel free to submit issues and enhancement requests!

## Security Warning

⚠️ Never share your:
- Private keys
- Storage password
- Wallet data files
- Salt key file

## License

MIT License - see LICENSE file for details

## Disclaimer

This is an unofficial bot. Use at your own risk. Always verify transactions before signing. 