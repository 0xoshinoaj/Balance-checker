import random
import configparser
from web3 import Web3
import pandas as pd
from datetime import datetime
import os

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
    wallet_balances = {wallet[0]: {network: None for network in networks} for wallet in wallets}
    
    for item in data:
        wallet_name = next(wallet[0] for wallet in wallets if wallet[1] == item['錢包地址'])
        wallet_balances[wallet_name][item['網路']] = item['餘額 (ETH)']
    
    # 創建 DataFrame
    df = pd.DataFrame(wallet_balances).T  # 轉置 DataFrame
    df.insert(0, '錢包地址', [wallet[1] for wallet in wallets])  # 將錢包地址作為第一列
    df.index.name = '#'  # 設置索引名稱為 "#"
    
    # 重新排序列，將 "錢包地址" 放在第一列
    columns = ['錢包地址'] + [col for col in df.columns if col != '錢包地址']
    df = df[columns]
    
    # 導出到 Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"balance_report_{timestamp}.xlsx"
    df.to_excel(filename)
    print(f"已導出報告至 {filename}")

def import_from_xlsx(filename):
    if not os.path.exists(filename):
        print(f"錯誤：找不到文件 {filename}")
        return [], []

    try:
        df = pd.read_excel(filename)
        if '錢包地址' not in df.columns:
            print("錯誤：Excel 文件中沒有 '錢包地址' 列")
            return [], []
        
        wallet_names = df.iloc[:, 0].tolist()  # 讀取第一列作為錢包名稱
        wallets = df['錢包地址'].tolist()
        return [(name, str(wallet).strip()) for name, wallet in zip(wallet_names, wallets) if str(wallet).strip()]
    except Exception as e:
        print(f"導入 Excel 文件時出錯：{e}")
        return [], []

def main():
    config = load_config()
    networks = [section for section in config.sections() if section not in ['VERSION', 'SETTINGS']]
    
    # 從 Excel 文件導入錢包地址
    import_file = config['SETTINGS'].get('import_file', 'wallets.xlsx')
    wallets = import_from_xlsx(import_file)
    
    if not wallets:
        print("沒有找到有效的錢包地址，程序將退出。")
        return

    export_xlsx = config['SETTINGS'].getboolean('export_xlsx', fallback=False)
    
    balance_data = []
    enabled_networks = []

    for network in networks:
        if config[network].getboolean('enabled', fallback=False):
            enabled_networks.append(network)
            print(f"\n檢查 {network} 網路:")
            rpc_urls = [config[network][key] for key in config[network] if key.startswith('rpc')]
            for i, (wallet_name, wallet_address) in enumerate(wallets, 1):
                try:
                    rpc_url = random.choice(rpc_urls)
                    balance = check_balance(rpc_url, wallet_address)
                    if balance is not None:
                        print(f"{wallet_name} ({wallet_address}) 的餘額是: {balance:.8f} ETH")
                        balance_data.append({
                            "網路": network,
                            "錢包地址": wallet_address,
                            "餘額 (ETH)": balance
                        })
                    else:
                        print(f"無法連接到 {network} 網路或檢查 {wallet_name} 的餘額")
                except Exception as e:
                    print(f"檢查 {wallet_name} 時發生錯誤: {e}")
        else:
            print(f"\n{network} 網路已禁用，跳過檢查。")
    
    if export_xlsx and balance_data:
        export_to_xlsx(balance_data, wallets, enabled_networks)

if __name__ == "__main__":
    main()