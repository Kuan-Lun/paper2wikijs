# ScienceDaily to Wiki.js 使用指南

## 功能概述

這個工具可以將 ScienceDaily 的科學文章自動轉換為結構化的 Wiki.js 條目，基於 `paper2wiki.md` 中定義的知識管理原則。

## 主要特性

1. **智能內容提取**: 從 ScienceDaily URL 自動提取文章資訊
2. **知識結構分析**: 使用 LangChain 分析文章，識別關鍵概念、方法、應用等
3. **避免知識碎片化**: 智能檢測現有相關條目，建議合併而非重複建立
4. **符合 APA 8 引用格式**: 自動產生符合學術標準的引用
5. **模組化設計**: 遵循 SOLID 原則，程式碼易於維護和擴充
6. **繁體中文支援**: 建立 Wiki.js 條目時使用繁體中文，References 保持原文

## 快速開始

### 1. 環境配置

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，新增 OpenAI API 金鑰
# OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 安裝依賴

```bash
pip install -e .
```

### 3. 基礎使用

```python
from src.langchain2wikijs import ScienceDaily2WikiService

# 初始化服務
service = ScienceDaily2WikiService()

# 預覽分析（不建立頁面）
url = "https://www.sciencedaily.com/releases/2025/03/250324181544.htm"
preview = service.preview_analysis(url)

# 建立 Wiki 條目
result = service.process_sciencedaily_url(url, main_entry_only=True)
```

### 4. 命令列使用

```bash
python main.py
```

## API 參考

### ScienceDaily2WikiService

主要服務類，整合所有功能。

#### `preview_analysis(url: str) -> Dict`

預覽分析結果，不實際建立頁面。

**參數:**

- `url`: ScienceDaily 文章 URL

**回傳:**

- 包含文章資訊、知識結構分析、現有頁面和合併建議的字典

#### `process_sciencedaily_url(url: str, create_main_entry_only: bool = False) -> Dict`

處理 ScienceDaily URL，建立相應的 Wiki 條目。

**參數:**

- `url`: ScienceDaily 文章 URL
- `create_main_entry_only`: 是否只建立主條目，不拆分子條目

**回傳:**

- 包含處理結果、建立和更新頁面列表的字典

## 知識管理原則

基於 `paper2wiki.md` 的約定：

### 1. 概念拆解

- 每個關鍵概念、定義、模型各成一頁
- 獨立建立新理論、新定義、新分類方法的頁面

### 2. 內容類型

- **概念 (concepts)**: 關鍵理論、定義
- **方法 (methods)**: 實驗方法、技術工具
- **應用 (applications)**: 具體應用場景、實證數據
- **問題 (problems)**: 研究背景和動機

### 3. 避免碎片化

- 優先合併到已有條目
- 檢查相似主題條目
- 智能建議合併機會

### 4. 引用規範

- 所有條目包含 APA 8 格式引用
- 標註每段內容的出處
- 維護完整的參考文獻列表
- 參考文獻維持原文語言

## 配置設定

本專案支援兩種配置方式，**強烈建議使用環境變數方式**以確保安全性：

### 方式 1: 環境變數 (.env) - **推薦**

1. 複製 `.env.example` 為 `.env`:

  ```bash
  cp .env.example .env
  ```

1. 編輯 `.env` 檔案，填入你的 API 金鑰:

  ```bash
  # OpenAI API Configuration
  OPENAI_API_KEY=your_openai_api_key_here

  # Wiki.js Configuration  
  WIKIJS_GRAPHQL_URL=https://your-wiki.domain/graphql
  WIKIJS_API_TOKEN=your_jwt_token_here
  WIKIJS_LOCALE=zh-TW

  # Optional: Configure base URL for other providers
  # OPENAI_BASE_URL=https://api.openai.com/v1
  ```

### 方式 2: 配置檔案 (config.json) - **不推薦用於生產環境**

如果你不使用環境變數，可以使用配置檔案：

```json
{
    "wiki.js": {
        "graphql_url": "https://your-wiki.domain/graphql",
        "api": "your_jwt_token_here"
    },
    "openai": {
        "api_key": "your_openai_api_key_here"
    }
}
```

**注意**: config.json 包含敏感資訊，請勿提交到版本控制！

## 架構設計

```text
├── ScienceDailyExtractor     # 內容提取器
├── WikiJSClient             # Wiki.js API 客戶端  
├── KnowledgeProcessor       # LangChain 知識處理器
└── ScienceDaily2WikiService # 主要服務類
```

### 設計原則 (SOLID)

1. **單一職責**: 每個類只負責一個功能領域
2. **開閉原則**: 易於擴充新的內容來源或 Wiki 平台
3. **里氏替換**: 各元件可獨立替換
4. **介面隔離**: 明確的介面定義
5. **依賴倒置**: 透過抽象降低耦合

## 範例輸出

### 分析結果範例

```json
{
  "success": true,
  "analysis": {
    "main_topic": "機器學習在醫學診斷中的應用",
    "concepts": ["深度學習", "神經網路", "醫學影像分析"],
    "methods": ["卷積神經網路", "資料增強", "交叉驗證"],
    "applications": ["X光診斷", "MRI分析", "早期癌症檢測"],
    "suggested_tags": ["機器學習", "醫學", "人工智慧"]
  },
  "merge_suggestions": [
    ("機器學習", 0.85),
    ("醫學影像", 0.72)
  ]
}
```

## 故障排除

### 常見問題

1. **OpenAI API 錯誤**: 檢查 `.env` 檔案中的 API 金鑰
2. **Wiki.js 連線失敗**: 驗證 `config.json` 中的 URL 和令牌
3. **內容提取失敗**: 確認 ScienceDaily URL 格式正確

### 除錯模式

設定環境變數啟用詳細日誌：

```bash
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_TRACING_V2=true
```

## 擴充開發

### 新增內容來源

1. 建立新的提取器類別（繼承基礎介面）
2. 在 `KnowledgeProcessor` 中新增特定處理邏輯
3. 在 `ScienceDaily2WikiService` 中整合新功能

### 支援其他 Wiki 平台

1. 實作新的客戶端類別
2. 保持相同的介面規範
3. 在服務類中替換客戶端實例

## 授權條款

GNU Affero General Public License v3
