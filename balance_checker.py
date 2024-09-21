import random
import configparser
from web3 import Web3
import pandas as pd
from datetime import datetime

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
    config = configparser.ConfigParser(allow_no_value=True)
    config.read('config.ini', encoding='utf-8')
    return config

def export_to_xlsx(data, wallets, networks):
    # 創建一個字典來存儲每個錢包在每個網路的餘額
    wallet_balances = {wallet: {network: None for network in networks} for wallet in wallets}
    
    for item in data:
        wallet_balances[item['錢包地址']][item['網路']] = item['餘額 (ETH)']
    
    # 創建 DataFrame
    df = pd.DataFrame(wallet_balances).T  # 轉置 DataFrame
    df.insert(0, '錢包地址', df.index)  # 將錢包地址作為第一列
    df.index = [f'錢包{i+1}' for i in range(len(df))]  # 設置索引為 "錢包1", "錢包2" 等
    df.index.name = '#'  # 設置索引名稱為 "#"
    
    # 重新排序列，將 "錢包地址" 放在第一列
    columns = ['錢包地址'] + [col for col in df.columns if col != '錢包地址']
    df = df[columns]
    
    # 導出到 Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"balance_report_{timestamp}.xlsx"
    df.to_excel(filename)
    print(f"已導出報告至 {filename}")

def main():
    config = load_config()
    networks = [section for section in config.sections() if section not in ['VERSION', 'SETTINGS', 'wallets']]
    wallets = [address.strip() for address in config['wallets']['addresses'].split('\n') if address.strip()]
    
    export_xlsx = config['SETTINGS'].getboolean('export_xlsx', fallback=False)
    
    balance_data = []
    enabled_networks = []

    for network in networks:
        if config[network].getboolean('enabled', fallback=False):
            enabled_networks.append(network)
            print(f"\n檢查 {network} 網路:")
            rpc_urls = [config[network][key] for key in config[network] if key.startswith('rpc')]
            for i, wallet_address in enumerate(wallets, 1):
                try:
                    rpc_url = random.choice(rpc_urls)
                    balance = check_balance(rpc_url, wallet_address)
                    if balance is not None:
                        print(f"錢包 {i} ({wallet_address}) 的餘額是: {balance:.8f} ETH")
                        balance_data.append({
                            "網路": network,
                            "錢包地址": wallet_address,
                            "餘額 (ETH)": balance
                        })
                    else:
                        print(f"無法連接到 {network} 網路或檢查錢包 {i} 的餘額")
                except Exception as e:
                    print(f"檢查錢包 {i} 時發生錯誤: {e}")
        else:
            print(f"\n{network} 網路已禁用，跳過檢查。")
    
    if export_xlsx and balance_data:
        export_to_xlsx(balance_data, wallets, enabled_networks)

if __name__ == "__main__":
    main()