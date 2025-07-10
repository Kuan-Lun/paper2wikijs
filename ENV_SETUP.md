# 環境變數配置指南

## 為什麼使用環境變數？

### 安全性優勢

1. **避免意外洩漏**: 敏感資訊不會被提交到版本控制系統
2. **符合安全最佳實踐**: 將配置與程式碼分離
3. **適合 CI/CD**: 在不同環境中安全地管理機密

### 在 Codex 中的優勢

當你將程式碼部署到 GitHub Codex 或其他雲端平台時：

1. **平台支援**: 大多數平台都支援環境變數設定
2. **動態配置**: 可以在不修改程式碼的情況下更改配置
3. **環境隔離**: 開發、測試、生產環境可以使用不同的配置

## 設定步驟

### 1. 本地開發

```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 檔案
# 填入你的真實 API 金鑰
```

### 2. GitHub Codespaces

在 GitHub 倉庫設定中：

1. 前往 **Settings** > **Secrets and variables** > **Codespaces**
2. 新增以下環境變數：
   - `OPENAI_API_KEY`: 你的 OpenAI API 金鑰
   - `WIKIJS_GRAPHQL_URL`: 你的 Wiki.js GraphQL URL
   - `WIKIJS_API_TOKEN`: 你的 Wiki.js API 權杖
   - `WIKIJS_LOCALE`: 條目預設語言 (預設 `zh-tw`)

### 3. 其他雲端平台

#### Vercel

```bash
vercel env add OPENAI_API_KEY
vercel env add WIKIJS_GRAPHQL_URL
vercel env add WIKIJS_API_TOKEN
vercel env add WIKIJS_LOCALE
```

#### Heroku

```bash
heroku config:set OPENAI_API_KEY=your_key
heroku config:set WIKIJS_GRAPHQL_URL=your_url
heroku config:set WIKIJS_API_TOKEN=your_token
heroku config:set WIKIJS_LOCALE=zh-tw
```

#### Docker

```bash
docker run -e OPENAI_API_KEY=your_key \
           -e WIKIJS_GRAPHQL_URL=your_url \
           -e WIKIJS_API_TOKEN=your_token \
           -e WIKIJS_LOCALE=zh-tw \
           your_image
```

## 向後相容性

本專案同時支援環境變數和設定檔案：

1. **優先順序**: 環境變數 > config.json
2. **漸進遷移**: 你可以逐步將設定移到環境變數
3. **回退機制**: 如果環境變數不存在，會嘗試讀取 config.json

## 驗證配置

執行以下指令來驗證你的配置：

```bash
# 檢查環境變數
python -c "import os; print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
python -c "import os; print('WIKIJS_GRAPHQL_URL:', 'SET' if os.getenv('WIKIJS_GRAPHQL_URL') else 'NOT SET')"
python -c "import os; print('WIKIJS_API_TOKEN:', 'SET' if os.getenv('WIKIJS_API_TOKEN') else 'NOT SET')"
python -c "import os; print('WIKIJS_LOCALE:', os.getenv('WIKIJS_LOCALE', 'zh-tw'))"

# 測試基本功能
python test_basic.py
```

## 疑難排解

### 常見問題

1. **環境變數沒有載入**
   - 確認 `.env` 檔案在專案根目錄
   - 檢查檔案名稱是否正確（不是 `.env.txt`）

2. **在 IDE 中無法讀取**
   - 重新啟動 IDE
   - 確認 IDE 支援 `.env` 檔案

3. **在容器中無法讀取**
   - 確認在 `docker run` 或 `docker-compose` 中正確設定環境變數
   - 檢查容器內的環境變數：`docker exec container_name env`

### 除錯指令

```bash
# 列出所有環境變數
env | grep -E "(OPENAI|WIKIJS)"

# 測試 Python 中的環境變數載入
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY', 'NOT FOUND'))"
```
