import os
import sys
from getpass import getpass
from wallet_storage import WalletStorage
from proxy_storage import ProxyStorage, format_proxy_url
from taker_bot import TakerBot
import time
import random

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def mining_menu(bot: TakerBot, wallet_name: str, wallet_address: str):
    """Submenu for mining operations"""
    while True:
        clear_screen()
        print(f"\n=== Mining Menu - {wallet_name} ===")
        print(f"Address: {wallet_address}")
        print("\n1. View User Information")
        print("2. View Mining Status")
        print("3. View Assignments")
        print("4. View Wallet Balance")
        print("5. Start/Stop Mining")
        print("6. Back to Main Menu")
        
        choice = input("\nSelect option (1-6): ")
        
        try:
            if choice == "1":
                print("\n=== User Information ===")
                info = bot.get_user_info()
                print(f"User ID: {info['data']['userId']}")
                print(f"Wallet: {info['data']['walletAddress']}")
                print(f"Invitation Code: {info['data']['invitationCode']}")
                print(f"Reward Amount: {info['data']['rewardAmount']} TAKER")
                print(f"Total Reward: {info['data']['totalReward']} TAKER")
                print(f"Invite Count: {info['data']['inviteCount']}")
                if info['data'].get('tgId'):
                    print(f"Telegram ID: {info['data']['tgId']}")
                if info['data'].get('dcId'):
                    print(f"Discord ID: {info['data']['dcId']}")
                if info['data'].get('twId'):
                    print(f"Twitter ID: {info['data']['twId']}")
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                print("\n=== Mining Status ===")
                mining_time = bot.get_total_mining_time()
                print(f"Last Mining Time: {mining_time['data']['lastMiningTime']}")
                print(f"Total Mining Time: {mining_time['data']['totalMiningTime']}")
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                print("\n=== Available Assignments ===")
                assignments = bot.get_assignment_list()
                for task in assignments['data']:
                    status = "✅ Done" if task['done'] else "❌ Not Done"
                    print(f"\n{task['title']}")
                    print(f"Status: {status}")
                    print(f"Reward: {task['reward']} points")
                    if task.get('url'):
                        print(f"URL: {task['url']}")
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                print("\n=== Wallet Balance ===")
                balance = bot.get_balance()
                wei_balance = int(balance['result'], 16)
                eth_balance = wei_balance / 10**18
                print(f"Balance: {eth_balance:.6f} ETH")
                input("\nPress Enter to continue...")
                
            elif choice == "5":
                try:
                    is_mining = bot.check_mining_status()
                    if is_mining:
                        print("\nMining is currently ACTIVE")
                        mining_time = bot.get_total_mining_time()
                        last_time = mining_time['data']['lastMiningTime']
                        total_time = mining_time['data']['totalMiningTime']
                        current_time = int(time.time())
                        time_left = (last_time + 24*60*60) - current_time
                        
                        if time_left > 0:
                            hours = time_left // 3600
                            minutes = (time_left % 3600) // 60
                            print(f"\nTime until next mining: {hours}h {minutes}m")
                        print(f"Total mining time: {total_time/3600:.1f}h")
                        input("\nPress Enter to continue...")
                        continue
                        
                    print("\nActivating mining process...")
                    print("This will require a transaction. Please wait...")
                    
                    bot.activate_mining()
                    print("\nMining activated successfully!")
                    print("Mining will continue for 24 hours.")
                    print("You can check mining status in option 2.")
                    
                except Exception as e:
                    print(f"\nError activating mining: {str(e)}")
                
                input("\nPress Enter to continue...")
                
            elif choice == "6":
                return
                
            else:
                print("\nInvalid option!")
                input("\nPress Enter to continue...")
                
        except Exception as e:
            print(f"\nError: {str(e)}")
            input("\nPress Enter to continue...")

def add_proxy_menu(storage: ProxyStorage):
    """Menu for adding proxy settings"""
    print("\n=== Add Proxy Settings ===")
    print("\nEnter proxy URLs separated by commas")
    print("\nFormats supported:")
    print("- protocol://username:password@host:port")
    print("- protocol://host:port")
    print("\nExamples:")
    print("- socks5://user:pass@proxy1.com:1080,http://proxy2.com:8080")
    print("- socks5://user1:pass1@proxy1.com:1080,socks5://user2:pass2@proxy2.com:1080")
    
    try:
        proxy_urls = input("\nEnter proxy URL(s): ").strip()
        if not proxy_urls:
            print("Proxy URL cannot be empty!")
            return
            
        success, failed, errors = storage.bulk_add_proxies_from_urls(proxy_urls)
        print(f"\nImport completed:")
        print(f"Successfully added: {success}")
        print(f"Failed to add: {failed}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"- {error}")
                
    except Exception as e:
        print(f"\nError adding proxies: {str(e)}")

def proxy_management_menu(proxy_storage: ProxyStorage, wallet_storage: WalletStorage):
    """Submenu for proxy management"""
    while True:
        clear_screen()
        print("\n=== Proxy Management ===")
        
        # Show proxy statistics
        stats = proxy_storage.get_proxy_stats()
        print(f"\nProxy Status:")
        print(f"Total unique proxies: {stats['total_proxies']}")
        print(f"Unassigned proxies: {stats['unassigned_proxies']}")
        print(f"Wallets with proxy: {stats['assigned_wallets']}")
        if stats['proxy_usage']:
            print("\nProxy Usage:")
            for proxy, count in stats['proxy_usage'].items():
                print(f"- {proxy}: {count} wallet(s)")
        
        print("\n1. Add Proxy(s)")
        print("2. Import Proxies from CSV")
        print("3. Import Proxies from JSON")
        print("4. Auto-Assign Proxies to Wallets")
        print("5. List All Proxies")
        print("6. Remove Proxy")
        print("7. Back to Main Menu")
        
        choice = input("\nSelect option (1-7): ")
        
        if choice == "1":
            add_proxy_menu(proxy_storage)
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            print("\n=== Import Proxies from CSV ===")
            print("\nCSV file should have headers: wallet_address,protocol,host,port,username,password")
            print("username and password are optional")
            file_path = input("\nEnter CSV file path: ")
            
            if os.path.exists(file_path):
                success, failed, errors = proxy_storage.import_proxies_from_csv(file_path)
                print(f"\nImport completed:")
                print(f"Successfully added: {success}")
                print(f"Failed to add: {failed}")
                if errors:
                    print("\nErrors:")
                    for error in errors:
                        print(f"- {error}")
            else:
                print("\nFile not found!")
            input("\nPress Enter to continue...")
            
        elif choice == "3":
            print("\n=== Import Proxies from JSON ===")
            print("\nJSON file should contain an array of objects with fields:")
            print("wallet_address, protocol, host, port, username (optional), password (optional)")
            file_path = input("\nEnter JSON file path: ")
            
            if os.path.exists(file_path):
                success, failed, errors = proxy_storage.import_proxies_from_json(file_path)
                print(f"\nImport completed:")
                print(f"Successfully added: {success}")
                print(f"Failed to add: {failed}")
                if errors:
                    print("\nErrors:")
                    for error in errors:
                        print(f"- {error}")
            else:
                print("\nFile not found!")
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            print("\n=== Auto-Assign Proxies to Wallets ===")
            wallets = wallet_storage.list_wallets()
            if not wallets:
                print("\nNo wallets found!")
                input("\nPress Enter to continue...")
                continue
                
            # Get confirmation
            print("\nThis will reassign all proxies to wallets in sequence.")
            print("Current proxy assignments will be cleared.")
            print(f"Number of wallets: {len(wallets)}")
            print(f"Number of unique proxies: {stats['total_proxies']}")
            print(f"Number of unassigned proxies: {stats['unassigned_proxies']}")
            
            if stats['total_proxies'] == 0:
                print("\nNo proxies available! Please add proxies first.")
                input("\nPress Enter to continue...")
                continue
                
            confirm = input("\nProceed with auto-assignment? (y/n): ").lower()
            if confirm != 'y':
                continue
                
            # Get wallet addresses in order
            wallet_addresses = [addr for _, addr in wallets]
            
            # Perform auto-assignment
            success, failed, errors = proxy_storage.auto_assign_proxies(wallet_addresses)
            
            print(f"\nAuto-assignment completed:")
            print(f"Successfully assigned: {success}")
            print(f"Failed to assign: {failed}")
            if errors:
                print("\nErrors:")
                for error in errors:
                    print(f"- {error}")
                    
            # Show current assignments
            print("\nCurrent Proxy Assignments:")
            for name, address in wallets:
                proxy_info = proxy_storage.get_proxy(address)
                if proxy_info:
                    print(f"{name}: {format_proxy_url(proxy_info)}")
                else:
                    print(f"{name}: No Proxy")
                    
            input("\nPress Enter to continue...")
            
        elif choice == "5":
            proxies = proxy_storage.list_proxies()
            if not proxies:
                print("\nNo proxies found!")
            else:
                print("\nConfigured Proxies:")
                for addr, data in proxies:
                    if addr.startswith('proxy_'):
                        print(f"\nUnassigned: {format_proxy_url(data)}")
                    else:
                        print(f"\nWallet: {addr}")
                        print(f"Proxy: {format_proxy_url(data)}")
            input("\nPress Enter to continue...")
            
        elif choice == "6":
            proxies = proxy_storage.list_proxies()
            if not proxies:
                print("\nNo proxies found!")
                input("\nPress Enter to continue...")
                continue
                
            print("\nSelect proxy to remove:")
            for i, (addr, data) in enumerate(proxies, 1):
                if addr.startswith('proxy_'):
                    print(f"{i}. Unassigned: {format_proxy_url(data)}")
                else:
                    print(f"{i}. {addr} - {format_proxy_url(data)}")
            
            try:
                idx = int(input("\nEnter number (or 0 to cancel): ")) - 1
                if idx == -1:
                    continue
                if 0 <= idx < len(proxies):
                    proxy_storage.remove_proxy(proxies[idx][0])
                    input("\nPress Enter to continue...")
                else:
                    print("\nInvalid selection!")
                    input("\nPress Enter to continue...")
            except ValueError:
                print("\nInvalid input!")
                input("\nPress Enter to continue...")
                
        elif choice == "7":
            return
            
        else:
            print("\nInvalid option!")
            input("\nPress Enter to continue...")

def start_multi_mining(wallet_storage: WalletStorage, proxy_storage: ProxyStorage, selected_wallets: list):
    """Start mining for multiple wallets with random delays"""
    results = []
    total_reward = 0
    
    # Shuffle wallets for random order
    random_wallets = selected_wallets.copy()
    random.shuffle(random_wallets)
    
    print(f"\n=== Starting Mining for {len(random_wallets)} Wallets ===")
    print("Note: Processing in random order with random delays")
    
    for wallet_name, address in random_wallets:
        try:
            # Random delay between operations (1-20 seconds)
            delay = random.randint(1, 20)
            print(f"\nProcessing {wallet_name} ({address})...")
            print(f"Waiting {delay} seconds before proceeding...")
            time.sleep(delay)
            
            private_key, _ = wallet_storage.get_wallet(wallet_name)
            proxy_settings = proxy_storage.get_proxy(address)
            
            if not proxy_settings:
                print("Warning: No proxy configured for this wallet!")
                proxy_url = "No proxy"
            else:
                proxy_url = format_proxy_url(proxy_settings)
                print(f"Using proxy: {proxy_url}")
            
            print(f"Connecting wallet {wallet_name}...")
            bot = TakerBot(private_key, proxy_settings)
            print("Logging in to Taker Protocol...")
            bot.login()
            
            # Get initial user info and rewards
            initial_info = bot.get_user_info()
            initial_reward = float(initial_info['data']['totalReward'])
            print(f"Initial Total Reward: {initial_reward} TAKER")
            
            # Check if already mining
            is_mining = bot.check_mining_status()
            if is_mining:
                print("Wallet is already mining, skipping activation...")
                mining_time = bot.get_total_mining_time()
                last_time = mining_time['data']['lastMiningTime']
                total_time = mining_time['data']['totalMiningTime']
                current_time = int(time.time())
                time_left = (last_time + 24*60*60) - current_time
                
                # Get updated user info
                final_info = bot.get_user_info()
                final_reward = float(final_info['data']['totalReward'])
                reward_change = final_reward - initial_reward
                
                status = {
                    'wallet': wallet_name,
                    'address': address,
                    'proxy': proxy_url,
                    'status': 'Already Mining',
                    'time_left': f"{time_left//3600}h {(time_left%3600)//60}m" if time_left > 0 else "Ready",
                    'total_time': f"{total_time/3600:.1f}h",
                    'initial_reward': initial_reward,
                    'final_reward': final_reward,
                    'reward_change': reward_change
                }
            else:
                print("Activating mining process...")
                bot.activate_mining()
                
                # Get updated user info after activation
                time.sleep(2)  # Wait briefly for update
                final_info = bot.get_user_info()
                final_reward = float(final_info['data']['totalReward'])
                reward_change = final_reward - initial_reward
                
                status = {
                    'wallet': wallet_name,
                    'address': address,
                    'proxy': proxy_url,
                    'status': 'Mining Started',
                    'time_left': '24h 0m',
                    'total_time': '0h',
                    'initial_reward': initial_reward,
                    'final_reward': final_reward,
                    'reward_change': reward_change
                }
            
            results.append(status)
            total_reward += final_reward
            print(f"Success: {status['status']}")
            print(f"Final Total Reward: {final_reward} TAKER")
            print(f"Reward Change: {'+' if reward_change >= 0 else ''}{reward_change} TAKER")
            
        except Exception as e:
            results.append({
                'wallet': wallet_name,
                'address': address,
                'proxy': proxy_url if 'proxy_url' in locals() else "Unknown",
                'status': f'Error: {str(e)}',
                'time_left': '-',
                'total_time': '-',
                'initial_reward': 0,
                'final_reward': 0,
                'reward_change': 0
            })
            print(f"Error: {str(e)}")
    
    # Display summary
    print("\n=== Mining Summary ===")
    print(f"\nTotal Wallets Processed: {len(random_wallets)}")
    print(f"Total Combined Reward: {total_reward} TAKER")
    
    print("\nWallet Status:")
    active_count = sum(1 for r in results if r['status'] in ['Mining Started', 'Already Mining'])
    skipped_count = sum(1 for r in results if r['status'] == 'Already Mining')
    error_count = sum(1 for r in results if 'Error' in r['status'])
    
    print(f"Successfully Activated: {active_count - skipped_count}")
    print(f"Already Mining (Skipped): {skipped_count}")
    print(f"Failed/Error: {error_count}")
    
    for result in results:
        print(f"\n{result['wallet']} ({result['address']})")
        print(f"Proxy: {result['proxy']}")
        print(f"Status: {result['status']}")
        if result['time_left'] != '-':
            print(f"Time Left: {result['time_left']}")
            print(f"Total Mining Time: {result['total_time']}")
        if isinstance(result.get('initial_reward'), (int, float)):
            print(f"Initial Reward: {result['initial_reward']} TAKER")
            print(f"Final Reward: {result['final_reward']} TAKER")
            print(f"Reward Change: {'+' if result['reward_change'] >= 0 else ''}{result['reward_change']} TAKER")

def parse_wallet_selection(selection: str, total_wallets: int) -> list:
    """Parse wallet selection string into list of wallet numbers"""
    selected = set()
    
    # Split by comma
    parts = [p.strip() for p in selection.split(',')]
    
    for part in parts:
        if '-' in part:
            # Handle range (e.g. "1-5")
            try:
                start, end = map(int, part.split('-'))
                if 1 <= start <= end <= total_wallets:
                    selected.update(range(start, end + 1))
                else:
                    raise ValueError(f"Invalid range: {part}")
            except:
                raise ValueError(f"Invalid range format: {part}")
        else:
            # Handle single number
            try:
                num = int(part)
                if 1 <= num <= total_wallets:
                    selected.add(num)
                else:
                    raise ValueError(f"Invalid wallet number: {num}")
            except:
                raise ValueError(f"Invalid number format: {part}")
    
    return sorted(list(selected))

def check_all_accounts_status(wallet_storage: WalletStorage, proxy_storage: ProxyStorage):
    """Check mining status and rewards for all accounts"""
    wallets = wallet_storage.list_wallets()
    if not wallets:
        print("\nNo wallets found!")
        return
        
    results = []
    total_reward = 0
    active_mining = 0
    
    print(f"\n=== Checking Status for {len(wallets)} Accounts ===\n")
    
    for wallet_name, address in wallets:
        try:
            print(f"Processing {wallet_name} ({address})...")
            private_key, _ = wallet_storage.get_wallet(wallet_name)
            proxy_settings = proxy_storage.get_proxy(address)
            
            if not proxy_settings:
                proxy_url = "No proxy"
            else:
                proxy_url = format_proxy_url(proxy_settings)
            
            bot = TakerBot(private_key, proxy_settings)
            bot.login()
            
            # Get user info and mining status
            user_info = bot.get_user_info()
            is_mining = bot.check_mining_status()
            
            if is_mining:
                active_mining += 1
                mining_time = bot.get_total_mining_time()
                last_time = mining_time['data']['lastMiningTime']
                total_time = mining_time['data']['totalMiningTime']
                current_time = int(time.time())
                time_left = (last_time + 24*60*60) - current_time
                
                mining_status = {
                    'status': 'Active',
                    'time_left': f"{time_left//3600}h {(time_left%3600)//60}m" if time_left > 0 else "Ready",
                    'total_time': f"{total_time/3600:.1f}h"
                }
            else:
                mining_status = {
                    'status': 'Inactive',
                    'time_left': '-',
                    'total_time': '-'
                }
            
            reward = float(user_info['data']['totalReward'])
            total_reward += reward
            
            result = {
                'wallet': wallet_name,
                'address': address,
                'proxy': proxy_url,
                'mining': mining_status,
                'reward': reward,
                'user_info': {
                    'userId': user_info['data']['userId'],
                    'invitationCode': user_info['data']['invitationCode'],
                    'rewardAmount': user_info['data']['rewardAmount'],
                    'inviteCount': user_info['data']['inviteCount']
                }
            }
            
            results.append(result)
            print(f"Success: Mining {mining_status['status']}, Reward: {reward} TAKER")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            results.append({
                'wallet': wallet_name,
                'address': address,
                'proxy': proxy_url if 'proxy_url' in locals() else "Unknown",
                'mining': {'status': 'Error', 'time_left': '-', 'total_time': '-'},
                'reward': 0,
                'user_info': None
            })
    
    # Display summary
    print("\n=== Account Status Summary ===")
    print(f"\nTotal Accounts: {len(wallets)}")
    print(f"Active Mining: {active_mining}")
    print(f"Inactive/Error: {len(wallets) - active_mining}")
    print(f"Total Reward: {total_reward} TAKER")
    
    print("\nDetailed Status:")
    for result in results:
        print(f"\n{result['wallet']} ({result['address']})")
        print(f"Proxy: {result['proxy']}")
        print(f"Mining Status: {result['mining']['status']}")
        if result['mining']['status'] == 'Active':
            print(f"Time Left: {result['mining']['time_left']}")
            print(f"Total Mining Time: {result['mining']['total_time']}")
        print(f"Reward: {result['reward']} TAKER")
        if result['user_info']:
            print(f"User ID: {result['user_info']['userId']}")
            print(f"Invitation Code: {result['user_info']['invitationCode']}")
            print(f"Reward Amount: {result['user_info']['rewardAmount']} TAKER")
            print(f"Invite Count: {result['user_info']['inviteCount']}")

def main_menu(wallet_storage: WalletStorage, proxy_storage: ProxyStorage):
    while True:
        clear_screen()
        print("\n=== Taker Protocol Bot ===")
        print("\n1. Add Single Wallet")
        print("2. Add Multiple Wallets")
        print("3. List Wallets")
        print("4. Remove Wallet")
        print("5. Manage Proxies")
        print("6. Start Mining")
        print("7. Check All Accounts Status")
        print("8. Exit")
        
        choice = input("\nSelect option (1-8): ")
        
        if choice == "1":
            try:
                private_key = input("\nEnter Private Key: ").strip()
                if private_key:
                    wallet_name = wallet_storage.add_wallet(private_key)
                    input("\nPress Enter to continue...")
            except ValueError as e:
                print(f"\nError: {str(e)}")
                input("\nPress Enter to continue...")
                
        elif choice == "2":
            print("\n=== Add Multiple Wallets ===")
            print("Enter private keys separated by commas")
            print("Example: key1,key2,key3")
            print("Keys can optionally start with '0x'")
            
            try:
                private_keys = input("\nEnter Private Keys: ").strip()
                if private_keys:
                    success, failed, errors = wallet_storage.bulk_add_wallets(private_keys)
                    print(f"\nImport completed:")
                    print(f"Successfully added: {success}")
                    print(f"Failed to add: {failed}")
                    if errors:
                        print("\nErrors:")
                        for error in errors:
                            print(f"- {error}")
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"\nError: {str(e)}")
                input("\nPress Enter to continue...")
                
        elif choice == "3":
            wallets = wallet_storage.list_wallets()
            if not wallets:
                print("\nNo wallets found!")
            else:
                print("\nStored Wallets:")
                for name, address in wallets:
                    proxy_info = proxy_storage.get_proxy(address)
                    proxy_status = "With Proxy" if proxy_info else "No Proxy"
                    print(f"{name}: {address} ({proxy_status})")
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            wallets = wallet_storage.list_wallets()
            if not wallets:
                print("\nNo wallets found!")
                input("\nPress Enter to continue...")
                continue
                
            print("\n=== Remove Wallets ===")
            print("\nCurrent Wallets:")
            for name, address in wallets:
                try:
                    wallet_num = int(name.split('_')[1])
                    print(f"{wallet_num}. {name}: {address}")
                except (IndexError, ValueError):
                    print(f"*. {name}: {address}")
            
            print("\nRemoval Options:")
            print("1. Single wallet (enter the number)")
            print("2. Range of wallets (e.g., 1-5)")
            print("3. Specific wallets (e.g., 1,3,5)")
            print("4. Mixed selection (e.g., 1-3,5,7-9)")
            print("0. Cancel")
            
            try:
                option = input("\nSelect option (0-4): ").strip()
                
                if option == "0":
                    continue
                    
                if option == "1":
                    num = input("\nEnter wallet number to remove: ").strip()
                    if num.isdigit():
                        success, failed, errors = wallet_storage.bulk_remove_wallets(num)
                else:
                    print("\nEnter wallet selection:")
                    if option == "2":
                        print("Format: start-end (e.g., 1-5)")
                    elif option == "3":
                        print("Format: num1,num2,num3 (e.g., 1,3,5)")
                    elif option == "4":
                        print("Format: range,numbers (e.g., 1-3,5,7-9)")
                    else:
                        print("\nInvalid option!")
                        input("\nPress Enter to continue...")
                        continue
                        
                    selection = input("\nEnter selection: ").strip()
                    success, failed, errors = wallet_storage.bulk_remove_wallets(selection)
                
                print(f"\nRemoval completed:")
                print(f"Successfully removed: {success}")
                print(f"Failed to remove: {failed}")
                if errors:
                    print("\nErrors:")
                    for error in errors:
                        print(f"- {error}")
                        
                input("\nPress Enter to continue...")
                
            except ValueError as e:
                print(f"\nError: {str(e)}")
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"\nError: {str(e)}")
                input("\nPress Enter to continue...")
                
        elif choice == "5":
            proxy_management_menu(proxy_storage, wallet_storage)
            
        elif choice == "6":
            wallets = wallet_storage.list_wallets()
            if not wallets:
                print("\nNo wallets found! Please add a wallet first.")
                input("\nPress Enter to continue...")
                continue
            
            print("\n=== Start Mining ===")
            print("\nCurrent Wallets:")
            for i, (name, address) in enumerate(wallets, 1):
                proxy_info = proxy_storage.get_proxy(address)
                proxy_status = "With Proxy" if proxy_info else "No Proxy"
                print(f"{i}. {name}: {address} ({proxy_status})")
            
            print("\nSelection Options:")
            print("1. Single wallet (enter the number)")
            print("2. Range of wallets (e.g., 1-5)")
            print("3. Specific wallets (e.g., 1,3,5)")
            print("4. Mixed selection (e.g., 1-3,5,7-9)")
            print("0. Cancel")
            
            try:
                option = input("\nSelect option (0-4): ").strip()
                
                if option == "0":
                    continue
                    
                selected_numbers = []
                if option == "1":
                    num = input("\nEnter wallet number: ").strip()
                    if num.isdigit():
                        selected_numbers = [int(num)]
                    else:
                        raise ValueError("Invalid wallet number")
                else:
                    print("\nEnter wallet selection:")
                    if option == "2":
                        print("Format: start-end (e.g., 1-5)")
                    elif option == "3":
                        print("Format: num1,num2,num3 (e.g., 1,3,5)")
                    elif option == "4":
                        print("Format: range,numbers (e.g., 1-3,5,7-9)")
                    else:
                        print("\nInvalid option!")
                        input("\nPress Enter to continue...")
                        continue
                        
                    selection = input("\nEnter selection: ").strip()
                    selected_numbers = parse_wallet_selection(selection, len(wallets))
                
                # Get selected wallets
                selected_wallets = [wallets[i-1] for i in selected_numbers]
                
                # Start mining for selected wallets
                start_multi_mining(wallet_storage, proxy_storage, selected_wallets)
                input("\nPress Enter to continue...")
                
            except ValueError as e:
                print(f"\nError: {str(e)}")
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"\nError: {str(e)}")
                input("\nPress Enter to continue...")
                
        elif choice == "7":
            check_all_accounts_status(wallet_storage, proxy_storage)
            input("\nPress Enter to continue...")
            
        elif choice == "8":
            print("\nExiting...")
            sys.exit(0)
        
        else:
            print("\nInvalid option!")
            input("\nPress Enter to continue...")

def main():
    clear_screen()
    print("=== Taker Protocol Bot ===")
    
    while True:
        try:
            password = getpass("\nEnter storage password: ")
            wallet_storage = WalletStorage(password)
            proxy_storage = ProxyStorage(password)
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            retry = input("\nRetry? (y/n): ").lower()
            if retry != 'y':
                sys.exit(1)
    
    main_menu(wallet_storage, proxy_storage)

if __name__ == "__main__":
    main() 