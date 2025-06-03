import os
import sys
import time
from taker_bot import TakerBot
from wallet_storage import WalletStorage
import getpass

class TakerBotMenu:
    def __init__(self):
        self.bot = None
        self.is_logged_in = False

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        self.clear_screen()
        print("=" * 50)
        print("           TAKER PROTOCOL BOT v1.0")
        print("=" * 50)
        if self.is_logged_in:
            print(f"Status: Connected to {self.bot.wallet_address[:6]}...{self.bot.wallet_address[-4:]}")
        else:
            print("Status: Not Connected")
        print("=" * 50)

    def login(self):
        if not os.path.exists("wallet_data.enc"):
            print("\nNo wallet found! Please run setup_wallet.py first.")
            input("\nPress Enter to continue...")
            return False

        try:
            storage_password = getpass.getpass("\nEnter your wallet storage password: ")
            self.bot = TakerBot(storage_password)
            print("\nLogging in to Taker Protocol...")
            self.bot.login()
            self.is_logged_in = True
            print("\nSuccessfully logged in!")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"\nError logging in: {str(e)}")
            input("\nPress Enter to continue...")
            return False

    def show_user_info(self):
        if not self.is_logged_in:
            print("\nPlease login first!")
            input("\nPress Enter to continue...")
            return

        try:
            info = self.bot.get_user_info()
            print("\n=== User Information ===")
            print(f"User ID: {info['data']['userId']}")
            print(f"Wallet: {info['data']['walletAddress']}")
            print(f"Invitation Code: {info['data']['invitationCode']}")
            print(f"Reward Amount: {info['data']['rewardAmount']} TAKER")
            print(f"Total Reward: {info['data']['totalReward']} TAKER")
            print(f"Invite Count: {info['data']['inviteCount']}")
            if info['data']['tgId']:
                print(f"Telegram ID: {info['data']['tgId']}")
            if info['data']['dcId']:
                print(f"Discord ID: {info['data']['dcId']}")
            if info['data']['twId']:
                print(f"Twitter ID: {info['data']['twId']}")
        except Exception as e:
            print(f"\nError getting user info: {str(e)}")
        
        input("\nPress Enter to continue...")

    def show_mining_status(self):
        if not self.is_logged_in:
            print("\nPlease login first!")
            input("\nPress Enter to continue...")
            return

        try:
            mining_time = self.bot.get_total_mining_time()
            print("\n=== Mining Status ===")
            print(f"Total Mining Time: {mining_time['data'] if 'data' in mining_time else 'Not available'}")
        except Exception as e:
            print(f"\nError getting mining status: {str(e)}")
        
        input("\nPress Enter to continue...")

    def show_assignments(self):
        if not self.is_logged_in:
            print("\nPlease login first!")
            input("\nPress Enter to continue...")
            return

        try:
            assignments = self.bot.get_assignment_list()
            print("\n=== Available Assignments ===")
            for task in assignments['data']:
                status = "✅ Done" if task['done'] else "❌ Not Done"
                print(f"\n{task['title']}")
                print(f"Status: {status}")
                print(f"Reward: {task['reward']} points")
                if task['url']:
                    print(f"URL: {task['url']}")
        except Exception as e:
            print(f"\nError getting assignments: {str(e)}")
        
        input("\nPress Enter to continue...")

    def check_wallet_balance(self):
        if not self.is_logged_in:
            print("\nPlease login first!")
            input("\nPress Enter to continue...")
            return

        try:
            balance = self.bot.get_balance()
            wei_balance = int(balance['result'], 16)
            eth_balance = wei_balance / 10**18
            print("\n=== Wallet Balance ===")
            print(f"Balance: {eth_balance:.6f} ETH")
        except Exception as e:
            print(f"\nError checking balance: {str(e)}")
        
        input("\nPress Enter to continue...")

    def show_menu(self):
        while True:
            self.print_header()
            print("\nMenu Options:")
            print("1. Login to Taker Protocol")
            print("2. Show User Information")
            print("3. Check Mining Status")
            print("4. View Available Assignments")
            print("5. Check Wallet Balance")
            print("6. Exit")

            choice = input("\nEnter your choice (1-6): ")

            if choice == "1":
                self.login()
            elif choice == "2":
                self.show_user_info()
            elif choice == "3":
                self.show_mining_status()
            elif choice == "4":
                self.show_assignments()
            elif choice == "5":
                self.check_wallet_balance()
            elif choice == "6":
                print("\nThank you for using Taker Protocol Bot!")
                sys.exit(0)
            else:
                print("\nInvalid choice! Please try again.")
                time.sleep(2)

def main():
    menu = TakerBotMenu()
    menu.show_menu()

if __name__ == "__main__":
    main() 