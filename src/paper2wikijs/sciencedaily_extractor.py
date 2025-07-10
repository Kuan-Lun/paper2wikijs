"""
ScienceDaily 內容抓取器
負責從 ScienceDaily URL 抓取和解析內容
"""

import re

import requests
from bs4.element import Tag
from bs4 import BeautifulSoup


class ScienceDailyExtractor:
    """從 ScienceDaily 網站提取內容的類"""

    def extract_article_info(self, url: str) -> dict[str, str]:
        """
        從 ScienceDaily URL 提取文章資訊

        Args:
            url: ScienceDaily 文章的 URL

        Returns:
            包含文章資訊的字典
        """
        resp = requests.get(url)
        if resp.status_code != 200:
            raise ValueError(f"無法訪問 URL: {url}，狀態碼: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        if not soup:
            raise ValueError(f"無法解析 URL: {url} 的內容")

        # Title
        h1_tag = soup.find("h1")
        if not h1_tag:
            raise ValueError(f"無法找到文章標題，請檢查 URL: {url}")
        title = h1_tag.get_text(strip=True)

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

                    while (
                        current
                        and isinstance(current, Tag)
                        and current.name in ["p", "div"]
                    ):
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

    def _extract_field(self, text_content: str, field_name: str) -> str:
        """提取特定欄位的內容"""
        # 提取格式化的欄位（如 **Date:**）
        field_match = re.search(
            rf"-\s*\*\*{field_name}:\*\*\s*([^\n\r-]+)", text_content
        )
        if field_match:
            return field_match.group(1).strip()

        # 提取純文本格式的欄位
        field_match = re.search(rf"{field_name}:\s*([^\n\r,]+)", text_content)
        if field_match:
            return field_match.group(1).strip()

        return ""

    def _extract_full_story(self, soup: BeautifulSoup, text_content: str) -> str:
        """提取完整故事內容"""
        # 先嘗試找到 FULL STORY 文本的位置
        full_story_match = re.search(
            r"FULL STORY\s*\n\s*(.+?)(?=\n\s*RELATED|Story Source:|$)",
            text_content,
            re.DOTALL,
        )
        if full_story_match:
            full_story = full_story_match.group(1).strip()
            # 清理多餘的空白字元和換行
            full_story = re.sub(r"\s+", " ", full_story)
            # 移除不必要的文本
            full_story = re.sub(r"Co-authors.*?(?=\n|\.|$)", "", full_story)
            full_story = re.sub(r"Additional research.*?(?=\n|\.|$)", "", full_story)
            return full_story

        # 如果上述方法失敗，嘗試尋找段落
        full_story_header = soup.find(string=lambda t: t and "FULL STORY" in t)
        if full_story_header:
            # 找到包含 FULL STORY 的元素的父級
            parent = full_story_header.parent
            if parent:
                # 尋找後續的段落
                current = parent.find_next_sibling()
                story_parts = []
                while (
                    current
                    and isinstance(current, Tag)
                    and current.name in ["p", "div"]
                ):
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
                return " ".join(story_parts)

        return ""
