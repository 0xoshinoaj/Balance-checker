import random
import configparser
from web3 import Web3

def check_balance(rpc_url, wallet_address):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        return None
    
    checksum_address = web3.to_checksum_address(wallet_address)
    
    try:
        balance_wei = web3.eth.get_balance(checksum_address)
        balance_eth = web3.from_wei(balance_wei, 'ether')
        return balance_eth
    except Exception as e:
        print(f"檢查餘額時出錯: {e}")
        return None

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def main():
    config = load_config()
    networks = [section for section in config.sections() if section != 'wallets']
    wallets = [address.strip() for address in config['wallets']['addresses'].split('\n') if address.strip()]

    for network in networks:
        if config[network].getboolean('enabled', fallback=False):
            print(f"\n檢查 {network} 網路:")
            rpc_urls = [config[network][key] for key in config[network] if key.startswith('rpc')]
            for i, wallet_address in enumerate(wallets, 1):
                try:
                    rpc_url = random.choice(rpc_urls)
                    balance = check_balance(rpc_url, wallet_address)
                    if balance is not None:
                        print(f"錢包 {i} ({wallet_address}) 的餘額是: {balance:.8f} ETH")
                    else:
                        print(f"無法連接到 {network} 網路或檢查錢包 {i} 的餘額")
                except Exception as e:
                    print(f"檢查錢包 {i} 時發生錯誤: {e}")
        else:
            print(f"\n{network} 網路已禁用，跳過檢查。")

if __name__ == "__main__":
    main()