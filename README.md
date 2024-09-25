# 多鏈錢包餘額查詢工具

這個專案是一個 Python 腳本，用於查詢多個區塊鏈網絡上的錢包餘額。它支持從 Excel 文件導入錢包地址，並可以將結果導出為 Excel 檔案。

## 功能

- 支持多個區塊鏈網路（如 Ethereum、Sepolia 測試網、BSC 等）
- 從 Excel 文件導入錢包地址
- 使用隨機選擇的 RPC 節點進行查詢，提高穩定性
- 將查詢結果導出為 Excel 報告
- 可配置的網絡啟用/禁用選項

## 安裝

1. 克隆此倉庫：
   ```
   git clone https://github.com/您的用戶名/您的倉庫名稱.git
   cd 您的倉庫名稱
   ```

2. 創建並激活虛擬環境：
   ```
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
   ```

3. 安裝所需的套件：
   ```
   pip install -r requirements.txt
   ```

## 配置

1. 編輯 `config.ini` 文件，設置需要查詢的區塊鏈網絡和 RPC 節點：
   ```ini
   [Ethereum主網]
   enabled = True
   rpc1 = https://rpc.ankr.com/eth
   rpc2 = https://1rpc.io/eth

   [Sepolia測試網]
   enabled = True
   rpc1 = https://ethereum-sepolia-rpc.publicnode.com
   rpc2 = https://1rpc.io/sepolia

   [SETTINGS]
   export_xlsx = True
   import_file = wallets.xlsx
   ```

2. 準備一個名為 將 `wallets-Sample.xlsx` 改名為 `wallets.xlsx` 的 Excel 文件，包含要查詢的錢包地址。文件格式如下：
   - 第一列：錢包名稱(必填)
   - 必須包含一列標題為 "錢包地址"

運行主程序：