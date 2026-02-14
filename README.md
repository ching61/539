# 今彩539 智慧統計與 AI 預測助手 (Smart 539 AI Assistant)

## 專案簡介
此專案旨在開發一個基於 Python 的自動化系統，用於爬取「今彩539」歷史開獎數據，進行科學統計分析（和值、奇偶、冷熱門、連號、尾數），並整合 Google Gemini AI 提供互動式分析與選號建議。透過 Streamlit 框架提供直觀易用的網頁介面。

## 核心模組與功能

### 1. 資料獲取與存儲 (Data Engine)
*   **功能**：自動從台灣彩券官方 API 爬取今彩539歷史開獎資料。支援增量更新，只爬取最新的數據。
*   **技術**：`requests`, `pandas`。
*   **輸出**：`lottery_data/lottery_data.csv`。

### 2. 科學統計引擎 (Stats Engine)
*   **功能**：對今彩539歷史數據進行多維度統計分析。
*   **分析項目**：
    *   **頻率分析**：計算各號碼的出現頻率（所有期數及近30期）。
    *   **和值規律**：分析每期開獎號碼總和的平均值、中位數、標準差及範圍。
    *   **奇偶/大小比**：分析開獎號碼中奇數/偶數、大數/小數（1-19為小，20-39為大）的比例分佈。
    *   **連號/尾數**：識別連號模式及其出現頻率，分析各尾數的出現頻率。
*   **技術**：`pandas`。

### 3. Gemini AI 互動層 (AI Interaction Layer)
*   **功能**：整合 Google Gemini AI 模型，將統計結果轉換為 Prompt 進行智能分析，並支援多輪互動對話。
*   **API 整合**：支援使用者手動輸入 `GOOGLE_API_KEY`。
*   **智能分析**：根據統計數據，AI 提供近期趨勢總結、選號建議及解釋理由。
*   **對話功能**：支援與 AI 進行問答，保持上下文的對話體驗。
*   **技術**：`google-generativeai`。

### 4. 使用者介面 (Frontend/UI)
*   **框架**：`Streamlit` (Python Web Framework)。
*   **介面功能**：
    *   **資料更新按鈕**：一鍵更新今彩539歷史數據。
    *   **統計圖表**：以長條圖、直方圖等形式視覺化展示各項統計分析結果。
    *   **API Key 設定**：側邊欄提供 API Key 輸入欄位。
    *   **AI 對話視窗**：顯示 AI 分析結果，並提供多輪對話互動介面。
*   **技術**：`streamlit`, `matplotlib`。

## 技術棧 (Tech Stack)
*   **語言**: Python 3.10+
*   **主要套件**: `pandas`, `requests`, `google-generativeai`, `streamlit`, `matplotlib`

## 如何啟動專案

### 1. 環境準備
*   確保您已安裝 Python 3.10 或更高版本。
*   建議使用虛擬環境：
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # Windows
    source venv/bin/activate  # macOS/Linux
    ```

### 2. 安裝依賴
在激活的虛擬環境中，安裝 `requirements.txt` 中列出的所有套件：
```bash
pip install -r requirements.txt
```

### 3. Google Gemini API Key 設定
1.  前往 [Google AI Studio](https://aistudio.google.com/) 取得您的 `GOOGLE_API_KEY`。
2.  在啟動 Streamlit 應用程式後，將您的 API Key 輸入到應用程式左側的「設定」側邊欄中。

### 4. 啟動應用程式
在專案根目錄下，執行以下命令啟動 Streamlit 應用程式：
```bash
streamlit run app.py
```
應用程式將會在您的預設瀏覽器中打開。

### 5. 功能使用
*   **資料更新**：點擊側邊欄的「更新今彩539資料」按鈕，獲取最新開獎數據。
*   **AI 分析與對話**：
    1.  輸入 API Key。
    2.  點擊「獲取 AI 分析與選號建議」按鈕，AI 會基於最新數據提供初步分析和選號建議。
    3.  在下方的對話框中輸入您的問題，與 AI 進行多輪互動。

## 部署到 Streamlit Community Cloud (免費)

1.  **確保程式碼在 GitHub 儲存庫中**：
    將整個專案資料夾推送到一個公開的 GitHub 儲存庫。
    **重要**：請確保您的 `GOOGLE_API_KEY` **沒有**直接寫死在任何程式碼檔案中。
2.  **設定 `secrets.toml`**：
    在您的 GitHub 儲存庫中，建立一個 `.streamlit` 資料夾，並在其中建立一個 `secrets.toml` 檔案，內容如下：
    ```toml
    GOOGLE_API_KEY="您的 Google API 金鑰"
    ```
    Streamlit Cloud 會自動讀取這個檔案作為環境變數。
3.  **前往 Streamlit Community Cloud**：
    前往 [share.streamlit.io](https://share.streamlit.io/) 並使用 GitHub 帳戶登入。
4.  **部署新應用程式**：
    點擊 "New app"，選擇您的 GitHub 儲存庫，並將 "Main file path" 設定為 `app.py`。
5.  **部署**：點擊 "Deploy!"。

## ⚠️ 免責聲明
本專案僅供數據科學研究使用。彩券具隨機性，統計分析無法保證中獎，請理性投注。
