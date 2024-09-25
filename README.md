# 多鏈錢包餘額查詢工具 [v1.3.0]

這個專案是用於查詢多個區塊鏈網絡上的錢包餘額。從 Excel 文件導入錢包地址，並將結果導出為 Excel 檔。

## 功能

- 支持多個區塊鏈網路（如 Ethereum、Sepolia 測試網等，也可自行添加需要的網路）
- 從 Excel 文件導入錢包地址、自定義錢包名稱
- 使用隨機選擇的 RPC 節點進行查詢，提高穩定性 (可自行添加)
- 將查詢結果導出為 Excel檔
- 使用個人代理，隨機選擇去進行查詢，提高穩定性

## 安裝

1. 克隆此倉庫：
   ```
   git clone https://github.com/0xoshinoaj/Balance-checker.git
   ```

2. 創建並激活虛擬環境(Windows)：
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. 安裝所需的套件：
   ```
   pip install -r requirements.txt
   ```

## 配置

1. 編輯 `config.ini` 文件：
   ```ini
   [Ethereum主網] 設置需要查詢的區塊鏈和 公用/私人 RPC 節點
   enabled = True
   rpc1 = https://rpc.ankr.com/eth

   [SETTINGS] 設定是否導出excel，輸入True或False
   export_xlsx = True
   ```
2. 將 `wallets-Sample.xlsx` 改名為 `wallets.xlsx` ，填入要查詢的錢包地址與自定義名稱。
    - 首欄不可刪除
    - 第一列：錢包名稱(必填)
    - 第二列：錢包地址(必填)

3. 將 `proxy-Sample.txt` 改名為 `proxy.txt` ，填入代理IP，格式如下：
   ```
   IP:PORT:USER:PASS:TYPE
   ```

運行主程序：
   ```
   python balance_checker.py
   ```