from .src.paper2wikijs import ScienceDaily2WikiService
from .src.paper2wikijs.config import WIKIJS_GRAPHQL_URL, WIKIJS_API_TOKEN


import requests
import re

from bs4 import BeautifulSoup


headers = {
    "Authorization": f"Bearer {WIKIJS_API_TOKEN}",
    "Content-Type": "application/json",
}


def fetch_sciencedaily_info(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Title
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

    # Date, Source, Summary - 新的格式是在列表項目中，格式為 "- **Date:** March 24, 2025"
    date, source, summary = "", "", ""

    # 尋找包含 Date:、Source:、Summary: 的文本
    text_content = soup.get_text()

    # 使用正則表達式來提取信息

    # 提取 Date
    date_match = re.search(r"-\s*\*\*Date:\*\*\s*([^\n\r-]+)", text_content)
    if date_match:
        date = date_match.group(1).strip()

    # 提取 Source
    source_match = re.search(r"-\s*\*\*Source:\*\*\s*([^\n\r-]+)", text_content)
    if source_match:
        source = source_match.group(1).strip()

    # 提取 Summary
    summary_match = re.search(r"-\s*\*\*Summary:\*\*\s*([^\n\r-]+)", text_content)
    if summary_match:
        summary = summary_match.group(1).strip()

    # 如果上述方法沒找到，嘗試尋找其他格式
    if not date:
        # 嘗試尋找純文本中的 Date:
        date_match = re.search(r"Date:\s*([^\n\r,]+)", text_content)
        if date_match:
            date = date_match.group(1).strip()

    if not source:
        # 嘗試尋找純文本中的 Source:
        source_match = re.search(r"Source:\s*([^\n\r,]+)", text_content)
        if source_match:
            source = source_match.group(1).strip()

    if not summary:
        # 嘗試尋找純文本中的 Summary:
        summary_match = re.search(r"Summary:\s*([^\n\r-]+)", text_content)
        if summary_match:
            summary = summary_match.group(1).strip()

    # FULL STORY - 尋找 "FULL STORY" 後的內容
    full_story = ""

    # 先嘗試找到 FULL STORY 文本的位置
    full_story_match = re.search(
        r"FULL STORY\s*\n\s*(.+?)(?=\n\s*RELATED|Story Source:|$)",
        text_content,
        re.DOTALL,
    )
    if full_story_match:
        full_story = full_story_match.group(1).strip()
        # 清理多餘的空白字符和換行
        full_story = re.sub(r"\s+", " ", full_story)
        # 移除不必要的文本
        full_story = re.sub(r"Co-authors.*?(?=\n|\.|$)", "", full_story)
        full_story = re.sub(r"Additional research.*?(?=\n|\.|$)", "", full_story)
    else:
        # 如果上述方法失敗，嘗試尋找段落
        full_story_header = soup.find(string=lambda t: t and "FULL STORY" in t)
        if full_story_header:
            # 找到包含 FULL STORY 的元素的父級
            parent = full_story_header.parent
            if parent:
                # 尋找後續的段落
                current = parent.find_next_sibling()
                story_parts = []
                while current and current.name in ["p", "div"]:
                    text = current.get_text(strip=True)
                    if (
                        text
                        and not text.startswith("RELATED")
                        and not text.startswith("Story Source")
                    ):
                        story_parts.append(text)
                        current = current.find_next_sibling()
                    else:
                        break
                full_story = " ".join(story_parts)

    return {
        "title": title,
        "date": date,
        "source": source,
        "summary": summary,
        "full_story": full_story,
        "url": url,
    }


def search_wiki_pages(search_term: str):
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
        headers=headers,
    )

    if response.status_code == 200:
        response_data = response.json()
        if (
            "data" in response_data
            and response_data["data"]["pages"]["search"]["results"]
        ):
            pages = response_data["data"]["pages"]["search"]["results"]
            return pages
        else:
            print("未找到頁面或回應有誤")
            if "errors" in response_data:
                raise Exception("GraphQL 錯誤:" + response_data["errors"])
    else:
        raise Exception(f"HTTP 錯誤: {response.status_code}, 回應: {response.text}")


def get_page_content(page_id: int):
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
        headers=headers,
    )
    response_data = response.json()
    if (
        "data" in response_data
        and response_data["data"]["pages"]
        and response_data["data"]["pages"]["single"]
    ):
        page = response_data["data"]["pages"]["single"]
        return page
    else:
        print("未找到頁面內容或回應有誤。")
        if "errors" in response_data:
            print("GraphQL 錯誤:", response_data["errors"])


def sciencedaily_to_wiki(
    url: str, preview_only: bool = False, main_entry_only: bool = False
) -> dict:
    """
    將 ScienceDaily 文章轉換為 Wiki 條目的主要函數

    Args:
        url: ScienceDaily 文章的 URL
        preview_only: 是否只預覽分析結果，不實際創建頁面
        main_entry_only: 是否只創建主條目，不拆分子條目

    Returns:
        處理結果字典
    """
    service = ScienceDaily2WikiService()

    if preview_only:
        return service.preview_analysis(url)
    else:
        return service.process_sciencedaily_url(url, main_entry_only)


if __name__ == "__main__":
    # 範例：預覽分析
    url = "https://www.sciencedaily.com/releases/2025/03/250324181544.htm"

    print("=== 預覽分析結果 ===")
    preview_result = sciencedaily_to_wiki(url, preview_only=True)

    if preview_result["success"]:
        print(f"文章標題: {preview_result['article_info']['title']}")
        print(f"主要話題: {preview_result['analysis']['main_topic']}")
        print(f"識別的概念: {preview_result['analysis']['concepts']}")
        print(f"識別的方法: {preview_result['analysis']['methods']}")
        print(f"識別的應用: {preview_result['analysis']['applications']}")
        print(f"建議標籤: {preview_result['analysis']['suggested_tags']}")

        if preview_result["merge_suggestions"]:
            print("\n=== 合併建議 ===")
            for title, score in preview_result["merge_suggestions"]:
                print(f"- {title} (相似度: {score:.2f})")

        # 詢問是否繼續創建頁面
        user_input = input("\n是否繼續創建 Wiki 頁面? (y/n): ")
        if user_input.lower() in ["y", "yes", "是"]:
            print("\n=== 創建 Wiki 頁面 ===")
            result = sciencedaily_to_wiki(url, main_entry_only=True)  # 先只創建主條目

            if result["success"]:
                print("處理完成!")
                if result["created_pages"]:
                    print("創建的頁面:")
                    for page in result["created_pages"]:
                        print(f"- {page['title']} ({page['type']})")

                if result["updated_pages"]:
                    print("更新的頁面:")
                    for page in result["updated_pages"]:
                        print(f"- {page['title']} ({page['type']})")
            else:
                print(f"處理失敗: {result.get('error', '未知錯誤')}")
    else:
        print(f"預覽失敗: {preview_result.get('error', '未知錯誤')}")

    # 保留原有的測試代碼
    print("\n=== 原有功能測試 ===")
    search_term = "價格指數"
    try:
        pages = search_wiki_pages(search_term)
        if pages:
            for page in pages:
                print(f"Title: {page['title']}, Path: {page['path']}")
        else:
            print("未找到頁面。")
    except Exception as e:
        print(f"錯誤: {e}")

    if pages:
        page_id = int(pages[0]["id"])
        try:
            page = get_page_content(page_id)
            print("取得到頁面內容")
            # print(f"Title: {page['title']}")
            # print("Markdown content:")
            # print(page["content"])
        except Exception as e:
            print(f"錯誤: {e}")

    # 測試原有的 ScienceDaily 提取功能
    info = fetch_sciencedaily_info(url)
    print(f"\n原始提取結果: {info['title']}")
