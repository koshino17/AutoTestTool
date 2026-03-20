# AutoTestTool

這是一個自動化執行工具，旨在簡化特定專案的 MTP (Mass Production Test) 流程。

## 檔案說明

在開始使用之前，請確保你擁有以下核心檔案：
* `AutoRun_GUI_loop.py`: 主程式執行檔，提供 GUI 介面與迴圈執行功能。
* `project.csv`: 專案相關的參數設定檔。
* `criteria.json`: 測試判斷標準與規則定義檔。

## 使用方式

為了讓程式正常運作，請遵循以下步驟進行環境部署：

### 1. 下載專案
首先，將此儲存庫複製到你的本地端：
```bash
git clone [https://github.com/你的帳號/倉庫名.git](https://github.com/koshino17/AutoTestTool.git)
cd 倉庫名
```

### 2. 配置檔案 (重要)
本程式採用路徑對應機制，請務必將上述提到的三個核心檔案移動至你目標專案的 **MTP 資料夾** 內：

**路徑範例：**
`[你的專案路徑]/MTP/`
* `[你的專案路徑]/MTP/AutoRun_GUI_loop.py`
* `[你的專案路徑]/MTP/project.csv`
* `[你的專案路徑]/MTP/criteria.json`

> **注意：** 若檔案未放置於對應的 MTP 資料夾中，程式可能無法正確讀取路徑或發生執行錯誤。

### 3. 執行程式
進入該 MTP 資料夾後，執行主程式：
```bash
python AutoRun_GUI_loop.py
```

## 注意事項
* 執行前請確認已安裝必要的 Python 套件。
* 修改 `project.csv` 或 `criteria.json` 時，請確保格式符合專案規範，以免影響自動化判斷。

---

### 補充建議
如果你的專案還有用到其他的 Library（例如 `pandas` 或 `Tkinter`），建議可以在 README 裡面補上：
```markdown
## 安裝依賴項目
pip install -r requirements.txt
```
這樣其他開發者在使用時會更加清楚需要準備什麼環境。
