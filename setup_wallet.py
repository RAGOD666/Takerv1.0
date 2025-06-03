from wallet_storage import setup_new_wallet

if __name__ == "__main__":
    print("=== Taker Bot Wallet Setup ===")
    print("\nThis script will help you securely store your wallet credentials.")
    print("Your private key will be encrypted with a password of your choice.")
    print("\nWARNING: Keep your storage password safe. If you lose it, you'll need to set up your wallet again.")
    
    try:
        setup_new_wallet()
    except Exception as e:
        print(f"\nError during setup: {str(e)}")
    else:
        print("\nSetup completed successfully!")
        print("You can now run taker_bot.py to start the bot.") 