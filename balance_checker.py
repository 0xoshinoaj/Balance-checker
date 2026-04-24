import random
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from web3 import Web3
import pandas as pd
from datetime import datetime
import os
import logging
import shutil

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

version = "1.4.0"

COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"

def color_text(text, color):
    return f"{color}{text}{COLOR_RESET}"

def print_warning(message):
    print(color_text(message, COLOR_YELLOW))

def print_error(message):
    print(color_text(message, COLOR_RED))

def print_success(message):
    print(color_text(message, COLOR_GREEN))

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
                raw = line.strip()
                if not raw or raw.startswith('#'):
                    continue

                parts = raw.split(':')
                if len(parts) == 5:
                    ip, port, user, password, proxy_type = parts
                    if not port.isdigit():
                        logging.warning(f"跳過無效代理行（端口不是數字）: {raw}")
                        continue
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
    config_path = 'config.toml'
    try:
        with open(config_path, 'rb') as file:
            return tomllib.load(file)
    except FileNotFoundError:
        print_error(f"錯誤：找不到配置文件 {config_path}")
    except tomllib.TOMLDecodeError as e:
        print_error(f"錯誤：配置文件格式不正確 ({e})")
    return None

def ensure_import_file_exists(import_file, sample_file="wallets-Sample.xlsx"):
    if os.path.exists(import_file):
        return True

    print_error(f"錯誤：找不到導入文件 {import_file}")
    if not os.path.exists(sample_file):
        print_error(f"錯誤：同時找不到範例檔 {sample_file}，程序將退出。")
        return False

    choice = input(f"是否使用 {sample_file} 複製為 {import_file}？(y/N): ").strip().lower()
    if choice not in ("y", "yes"):
        print_warning("未建立導入文件，程序將退出。")
        return False

    try:
        shutil.copyfile(sample_file, import_file)
        print_success(f"已建立 {import_file}。")
        return True
    except OSError as e:
        print_error(f"建立導入文件失敗：{e}")
        return False

def ensure_proxy_file_exists(proxy_file, sample_file="proxy-Sample.txt"):
    if os.path.exists(proxy_file):
        return True

    print_warning(f"警告：找不到代理文件 {proxy_file}")
    if not os.path.exists(sample_file):
        print_warning(f"警告：同時找不到範例檔 {sample_file}，將以不使用代理模式繼續。")
        return False

    try:
        shutil.copyfile(sample_file, proxy_file)
        print_success(f"已建立 {proxy_file}（請填入代理資料後再使用代理模式）。")
        return True
    except OSError as e:
        print_error(f"建立代理文件失敗：{e}")
        return False

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
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"balance_report_{timestamp}.xlsx"
    output_path = os.path.join(output_dir, filename)
    df.to_excel(output_path)
    print_success(f"已導出報告至 {output_path}")

def import_from_xlsx(filename):
    if not os.path.exists(filename):
        print_error(f"錯誤：找不到文件 {filename}")
        return [], []

    try:
        df = pd.read_excel(filename)
        if '錢包地址' not in df.columns:
            print_error("錯誤：Excel 文件中沒有 '錢包地址' 列")
            return [], []
        
        wallet_names = df.iloc[:, 0].tolist()  # 讀取第一列作為錢包名稱
        wallets = df['錢包地址'].tolist()
        return [(name, str(wallet).strip()) for name, wallet in zip(wallet_names, wallets) if str(wallet).strip()]
    except Exception as e:
        print_error(f"導入 Excel 文件時出錯：{e}")
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
    if not config:
        return

    settings = config.get('settings', {})
    network_configs = config.get('networks', {})
    networks = list(network_configs.keys())
    
    use_proxy = bool(settings.get('use_proxy', False))
    proxy_file = settings.get('proxy_file', 'proxy.txt')
    if use_proxy and not ensure_proxy_file_exists(proxy_file):
        print_warning("警告：代理文件不可用，將不使用代理進行檢查。")
        use_proxy = False

    proxies = load_proxies(proxy_file) if use_proxy else []
    if use_proxy and not proxies:
        print_warning("警告：沒有找到有效的代理，將不使用代理進行檢查。")
    
    import_file = settings.get('import_file', 'wallets.xlsx')
    if not ensure_import_file_exists(import_file):
        return
    wallets = import_from_xlsx(import_file)
    
    if not wallets:
        print_warning("沒有找到有效的錢包地址，程序將退出。")
        return

    export_xlsx = bool(settings.get('export_xlsx', False))
    
    balance_data = []
    enabled_networks = []

    sessions = proxies if proxies else [None]
    for proxy in sessions:
        if proxy is None:
            session_cm = aiohttp.ClientSession()
        else:
            session_cm = await create_session(proxy)

        async with session_cm as session:
            for network in networks:
                network_config = network_configs.get(network, {})
                if bool(network_config.get('enabled', False)):
                    enabled_networks.append(network)
                    print(f"\n檢查 {network} 網路:")
                    rpc_urls = network_config.get('rpc', [])
                    if not rpc_urls:
                        print(f"{network} 網路沒有可用 RPC，跳過檢查。")
                        continue
                    results = await check_balances(session, wallets, rpc_urls, network)
                    balance_data.extend(results)
                else:
                    print(f"\n{network} 網路已禁用，跳過檢查。")
        
        if balance_data and proxy is not None:
            break  # 如果成功获取了数据，就跳出代理循环

    if export_xlsx and balance_data:
        export_to_xlsx(balance_data, wallets, enabled_networks)

if __name__ == "__main__":
    asyncio.run(main())