# 多鏈錢包餘額查詢工具

這個專案是用於查詢多個區塊鏈網絡上的錢包餘額。從 Excel 文件導入錢包地址，並將結果導出為 Excel 檔。

## 功能

- 支持多個區塊鏈網路（如 Ethereum、Sepolia 測試網等，也可自行添加需要的網路）
- 從 Excel 文件導入錢包地址、自定義錢包名稱
- 使用隨機選擇的 RPC 節點進行查詢，提高穩定性 (可自行添加)
- 可選擇是否使用代理查詢（`use_proxy = true/false`）
- 將查詢結果導出為 Excel 檔（輸出到 `output/` 目錄）

## 安裝（macOS）

1. 克隆此倉庫：
   ```
   git clone https://github.com/0xoshinoaj/Balance-checker.git
   cd Balance-checker
   ```

2. （選擇性）指定 Python 版本（若你使用 pyenv）：
   ```
   pyenv local 3.14.4
   ```

3. 創建並啟用虛擬環境：
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

4. 安裝所需套件：
   ```
   python -m pip install -r requirements.txt
   ```

## 配置

1. 編輯 `config.toml` 文件（節錄）：
   ```toml
   [networks."Ethereum主網"]
   enabled = false
   rpc = [
     "https://rpc.ankr.com/eth",
     "https://1rpc.io/eth",
   ]

   [settings]
   import_file = "wallets.xlsx"
   export_xlsx = true
   use_proxy = false
   proxy_file = "proxy.txt"
   ```

2. 將 `wallets-Sample.xlsx` 改名為 `wallets.xlsx`，填入要查詢的錢包地址與自定義名稱。
    - 首欄不可刪除
    - 第一列：錢包名稱(必填)
    - 第二列：錢包地址(必填)

3. 若你要使用代理，將 `proxy-Sample.txt` 改名為 `proxy.txt`，並在 `config.toml` 設定 `use_proxy = true`。代理格式如下：
   ```
   IP:PORT:USER:PASS:TYPE
   ```

## 執行

運行主程式：
   ```
   python balance_checker.py
   ```

查詢完成後，若有成功取得餘額且 `export_xlsx = true`，報表會輸出到 `output/` 目錄。