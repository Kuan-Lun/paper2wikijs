"""
Wiki.js API 客戶端
負責與 Wiki.js 的 GraphQL API 互動
"""

import requests
import os
from typing import List, Dict, Optional

from .config import WIKIJS_GRAPHQL_URL, WIKIJS_API_TOKEN, WIKIJS_LOCALE, WIKIJS_TIMEOUT


class WikiJSClient:
    """Wiki.js GraphQL API 客戶端"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化 Wiki.js 客戶端
        優先從環境變數取得設定，如果沒有則從配置檔案讀取

        Args:
            config_path: 配置檔案路徑（當環境變數不可用時使用）
        """

        # 如果 timeout 仍然未設定，則使用預設值

        self.headers = {
            "Authorization": f"Bearer {WIKIJS_API_TOKEN}",
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
            WIKIJS_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=self.headers,
            timeout=WIKIJS_TIMEOUT,
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
            WIKIJS_GRAPHQL_URL,
            json={"query": query_content, "variables": variables},
            headers=self.headers,
            timeout=WIKIJS_TIMEOUT,
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
        """.format(
            locale=WIKIJS_LOCALE
        )

        variables = {
            "title": title,
            "content": content,
            "path": path,
            "tags": tags or [],
            "description": description or title,  # 使用標題作為預設描述
        }

        response = requests.post(
            WIKIJS_GRAPHQL_URL,
            json={"query": create_query, "variables": variables},
            headers=self.headers,
            timeout=WIKIJS_TIMEOUT,
        )

        response_data = response.json()
        if "data" in response_data:
            return response_data["data"]["pages"]["create"]["responseResult"]
        else:
            if "errors" in response_data:
                raise Exception("GraphQL errors:" + str(response_data["errors"]))
            raise Exception("Unknown error occurred")

    def update_page(
        self, page_id: int, title: str, content: str, tags: list[str] | None = None
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
        """.format(
            locale=WIKIJS_LOCALE
        )

        variables = {
            "id": page_id,
            "title": title,
            "content": content,
            "tags": tags or [],
        }

        response = requests.post(
            WIKIJS_GRAPHQL_URL,
            json={"query": update_query, "variables": variables},
            headers=self.headers,
            timeout=WIKIJS_TIMEOUT,
        )

        response_data = response.json()
        if "data" in response_data:
            return response_data["data"]["pages"]["update"]["responseResult"]
        else:
            if "errors" in response_data:
                raise Exception("GraphQL errors:" + str(response_data["errors"]))
            raise Exception("Unknown error occurred")
