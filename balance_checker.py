import random
import configparser
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from web3 import Web3
import pandas as pd
from datetime import datetime
import os
import logging

version = "1.3.0"

async def check_balance(session, rpc_url, wallet_address):
    try:
        async with session.post(rpc_url, json={
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [wallet_address, "latest"],
            "id": 1
        }, timeout=10) as response:
            if response.status != 200:
                return None
            result = await response.json()
            if 'result' not in result:
                return None
            balance = int(result['result'], 16)
            return Web3.from_wei(balance, 'ether')
    except aiohttp.ClientError as e:
        logging.error(f"網絡錯誤: {e}")
    except ValueError as e:
        logging.error(f"JSON 解析錯誤: {e}")
    except Exception as e:
        logging.error(f"未知錯誤: {e}")
    return None

async def check_balances(session, wallets, rpc_urls, network):
    results = []
    for wallet_name, wallet_address in wallets:
        rpc_url = random.choice(rpc_urls)
        balance = await check_balance(session, rpc_url, wallet_address)
        
        if balance is not None:
            print(f"{wallet_name} ({wallet_address}) 的 {network} 餘額是: {balance:.8f} ETH")
            results.append({
                "網路": network,
                "錢包地址": wallet_address,
                "餘額 (ETH)": balance
            })
        else:
            print(f"無法檢查 {wallet_name} ({wallet_address}) 的{network}餘額")
        
        await asyncio.sleep(0.2)
    
    return results

def load_proxies(file_path):
    proxies = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(':')
                if len(parts) == 5:
                    ip, port, user, password, proxy_type = parts
                    proxy = {
                        'host': ip,
                        'port': int(port),
                        'username': user,
                        'password': password,
                        'proxy_type': proxy_type.lower()
                    }
                    proxies.append(proxy)
    except IOError as e:
        logging.error(f"無法讀取代理文件: {e}")
    return proxies

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

async def create_session(proxy):
    if proxy['proxy_type'] == 'socks5':
        connector = ProxyConnector.from_url(
            f"socks5://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        )
    else:  # http or https
        connector = aiohttp.TCPConnector()
        auth = aiohttp.BasicAuth(proxy['username'], proxy['password'])
        return aiohttp.ClientSession(connector=connector, auth=auth,
                                     proxy=f"http://{proxy['host']}:{proxy['port']}")
    
    return aiohttp.ClientSession(connector=connector)

async def main():
    config = load_config()
    networks = [section for section in config.sections() if section not in ['VERSION', 'SETTINGS']]
    
    proxy_file = config['SETTINGS'].get('proxy_file', 'proxy.txt')
    proxies = load_proxies(proxy_file)
    
    if not proxies:
        print("警告：沒有找到有效的代理，將不使用代理進行檢查。")
    
    import_file = config['SETTINGS'].get('import_file', 'wallets.xlsx')
    wallets = import_from_xlsx(import_file)
    
    if not wallets:
        print("沒有找到有效的錢包地址，程序將退出。")
        return

    export_xlsx = config['SETTINGS'].getboolean('export_xlsx', fallback=False)
    
    balance_data = []
    enabled_networks = []

    for proxy in proxies:
        async with await create_session(proxy) as session:
            for network in networks:
                if config[network].getboolean('enabled', fallback=False):
                    enabled_networks.append(network)
                    print(f"\n檢查 {network} 網路:")
                    rpc_urls = [config[network][key] for key in config[network] if key.startswith('rpc')]
                    results = await check_balances(session, wallets, rpc_urls, network)
                    balance_data.extend(results)
                else:
                    print(f"\n{network} 網路已禁用，跳過檢查。")
        
        if balance_data:
            break  # 如果成功获取了数据，就跳出代理循环

    if export_xlsx and balance_data:
        export_to_xlsx(balance_data, wallets, enabled_networks)

if __name__ == "__main__":
    asyncio.run(main())