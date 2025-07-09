"""
Wiki.js API 客戶端
負責與 Wiki.js 的 GraphQL API 互動
"""

import requests
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class WikiJSClient:
    """Wiki.js GraphQL API 客戶端"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化 Wiki.js 客戶端
        優先從環境變數取得設定，如果沒有則從配置檔案讀取

        Args:
            config_path: 配置檔案路徑（當環境變數不可用時使用）
        """
        # 優先從環境變數取得設定
        self.wiki_url = os.getenv("WIKIJS_GRAPHQL_URL")
        self.api_token = os.getenv("WIKIJS_API_TOKEN")
        self.locale = os.getenv("WIKIJS_LOCALE")

        # 如果環境變數中沒有，嘗試從配置檔案讀取
        if not self.wiki_url or not self.api_token:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                if not self.wiki_url:
                    self.wiki_url = config["wiki.js"]["graphql_url"]
                if not self.api_token:
                    self.api_token = config["wiki.js"]["api"]
                if not self.locale:
                    self.locale = config["wiki.js"].get("locale")
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                raise ValueError(
                    f"無法從環境變數或配置檔案取得 Wiki.js 設定。"
                    f"請設定 WIKIJS_GRAPHQL_URL 和 WIKIJS_API_TOKEN 環境變數，"
                    f"或確保 {config_path} 存在且格式正確。錯誤: {e}"
                )

        if not self.wiki_url or not self.api_token:
            raise ValueError(
                "Wiki.js 設定不完整。請確保設定了 WIKIJS_GRAPHQL_URL 和 WIKIJS_API_TOKEN"
            )
        if not self.locale:
            self.locale = "zh-TW"

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def search_pages(self, search_term: str) -> List[Dict]:
        """
        搜尋 Wiki 頁面

        Args:
            search_term: 搜尋關鍵字

        Returns:
            搜尋結果列表
        """
        query = """
        query SearchPages($term: String!) {
          pages {
            search(query: $term) {
              results {
                id
                title
                path
              }
            }
          }
        }
        """.strip()

        variables = {"term": search_term}

        response = requests.post(
            self.wiki_url,
            json={"query": query, "variables": variables},
            headers=self.headers,
        )

        if response.status_code == 200:
            response_data = response.json()
            if (
                "data" in response_data
                and response_data["data"]["pages"]["search"]["results"]
            ):
                return response_data["data"]["pages"]["search"]["results"]
            else:
                if "errors" in response_data:
                    raise Exception("GraphQL errors:" + str(response_data["errors"]))
                return []
        else:
            raise Exception(
                f"HTTP Error: {response.status_code}, Response: {response.text}"
            )

    def get_page_content(self, page_id: int) -> Optional[Dict]:
        """
        取得頁面內容

        Args:
            page_id: 頁面 ID

        Returns:
            頁面內容字典，如果未找到則回傳 None
        """
        query_content = """
        query PageContent($id: Int!) {
          pages {
            single(id: $id) {
              title
              content
            }
          }
        }
        """

        variables = {"id": page_id}

        response = requests.post(
            self.wiki_url,
            json={"query": query_content, "variables": variables},
            headers=self.headers,
        )

        response_data = response.json()
        if (
            "data" in response_data
            and response_data["data"]["pages"]
            and response_data["data"]["pages"]["single"]
        ):
            return response_data["data"]["pages"]["single"]
        else:
            if "errors" in response_data:
                print("GraphQL errors:", response_data["errors"])
            return None

    def create_page(
        self,
        title: str,
        content: str,
        path: str,
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> Dict:
        """
        建立新頁面

        Args:
            title: 頁面標題
            content: 頁面內容 (Markdown 格式)
            path: 頁面路徑
            tags: 標籤列表
            description: 頁面描述

        Returns:
            建立結果
        """
        create_query = """
        mutation CreatePage($title: String!, $content: String!, $path: String!, $tags: [String!]!, $description: String!) {{
          pages {{
            create(
              title: $title
              content: $content
              path: $path
              tags: $tags
              description: $description
              editor: "markdown"
              locale: "{locale}"
              isPublished: true
              isPrivate: false
            ) {{
              responseResult {{
                succeeded
                errorCode
                slug
                message
              }}
            }}
          }}
        }}
        """.format(locale=self.locale)

        variables = {
            "title": title,
            "content": content,
            "path": path,
            "tags": tags or [],
            "description": description or title,  # 使用標題作為預設描述
        }

        response = requests.post(
            self.wiki_url,
            json={"query": create_query, "variables": variables},
            headers=self.headers,
        )

        response_data = response.json()
        if "data" in response_data:
            return response_data["data"]["pages"]["create"]["responseResult"]
        else:
            if "errors" in response_data:
                raise Exception("GraphQL errors:" + str(response_data["errors"]))
            raise Exception("Unknown error occurred")

    def update_page(
        self, page_id: int, title: str, content: str, tags: List[str] = None
    ) -> Dict:
        """
        更新現有頁面

        Args:
            page_id: 頁面 ID
            title: 頁面標題
            content: 頁面內容 (Markdown 格式)
            tags: 標籤列表

        Returns:
            更新結果
        """
        update_query = """
        mutation UpdatePage($id: Int!, $title: String!, $content: String!, $tags: [String!]!) {{
          pages {{
            update(
              id: $id
              title: $title
              content: $content
              tags: $tags
              editor: "markdown"
              locale: "{locale}"
              isPublished: true
            ) {{
              responseResult {{
                succeeded
                errorCode
                slug
                message
              }}
            }}
          }}
        }}
        """.format(locale=self.locale)

        variables = {
            "id": page_id,
            "title": title,
            "content": content,
            "tags": tags or [],
        }

        response = requests.post(
            self.wiki_url,
            json={"query": update_query, "variables": variables},
            headers=self.headers,
        )

        response_data = response.json()
        if "data" in response_data:
            return response_data["data"]["pages"]["update"]["responseResult"]
        else:
            if "errors" in response_data:
                raise Exception("GraphQL errors:" + str(response_data["errors"]))
            raise Exception("Unknown error occurred")
