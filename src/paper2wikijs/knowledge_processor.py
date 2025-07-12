"""
知識處理器
使用 LangChain 進行內容分析和知識提取
"""

import json
from typing import Any
from textwrap import dedent

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .config import OPENAI_API_KEY
from .translation_service import TranslationService


class KnowledgeProcessor:
    """使用 LangChain 處理知識內容的類"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        初始化知識處理器
        優先從環境變數取得 API 金鑰，如果沒有則從配置檔案讀取

        Args:
            model_name: 使用的 LLM 模型名稱
            config_path: 配置檔案路徑（當環境變數不可用時使用）
        """
        # 優先從環境變數取得 API 金鑰

        self.llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=OPENAI_API_KEY)
        self.translation_service = TranslationService(model_name)

    def analyze_content_for_wiki_structure(
        self, article_info: dict[str, str]
    ) -> dict[str, Any]:
        """
        分析文章內容，根據 paper2wiki.md 的約定提取知識結構

        Args:
            article_info: 從 ScienceDaily 提取的文章資訊

        Returns:
            包含不同類型條目的字典
        """
        if not self.llm:
            # 如果沒有 LLM，回傳基本分析結果
            raise ValueError(
                "LLM 未初始化，無法進行內容分析。請檢查 API 金鑰或模型名稱。"
            )
        system_prompt = dedent(
            """
            你是一個專業的知識管理專家。請根據以下規則分析科學文章，並提取適合建立 Wiki 條目的知識點：

            ## 分析規則：

            1. **概念拆解**：識別文章中的關鍵概念、定義、模型、理論
            2. **技術方法**：提取實驗方法、技術工具、研究方法
            3. **應用案例**：識別具體的應用場景、實證數據
            4. **背景問題**：分析研究解決的問題和動機
            5. **引用關係**：識別與其他研究的關聯

            請以 JSON 格式回傳分析結果，包含以下欄位：
            - concepts: 關鍵概念列表
            - methods: 技術方法列表
            - applications: 應用案例列表
            - problems: 背景問題列表
            - main_topic: 主要話題（用於建立主條目）
            - suggested_tags: 建議的標籤列表

            只回傳 JSON，不要包含其他文字。
        """
        )

        # 先將完整內容翻譯成繁體中文
        translated_content = self.translation_service.translate_to_traditional_chinese(
            article_info["full_story"]
        )

        human_prompt = dedent(
            f"""
            請分析以下科學文章：

            標題：{article_info['title']}
            來源：{article_info['source']}
            日期：{article_info['date']}
            摘要：{article_info['summary']}
            完整內容：{translated_content}
            URL：{article_info['url']}
        """
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        response = self.llm.invoke(messages)

        try:
            # 嘗試提取 JSON 部分
            content = response.content
            if isinstance(content, str):
                content = content.strip()

                # 如果回應被包裹在程式碼區塊中，提取 JSON 部分
                if content.startswith("```json"):
                    content = content[7:]

                if content.startswith("```"):
                    content = content[3:]

                if content.endswith("```"):
                    content = content[:-3]

                # 嘗試找到 JSON 物件的開始和結束
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1

                if start_idx != -1 and end_idx > start_idx:
                    json_content = content[start_idx:end_idx]
                    analysis_result = json.loads(json_content)
                    return analysis_result
                else:
                    raise json.JSONDecodeError("No valid JSON found", content, 0)
            elif isinstance(content, list):
                # 將列表轉為字符串再嘗試解析
                content_str = "\n".join(
                    (
                        json.dumps(item, ensure_ascii=False)
                        if isinstance(item, dict)
                        else str(item)
                    )
                    for item in content
                )
                start_idx = content_str.find("{")
                end_idx = content_str.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_content = content_str[start_idx:end_idx]
                    analysis_result = json.loads(json_content)
                    return analysis_result
                else:
                    raise json.JSONDecodeError("No valid JSON found", content_str, 0)
            elif isinstance(content, dict):
                return content
            else:
                raise json.JSONDecodeError("No valid JSON found", str(content), 0)

        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗，使用基本結構: {e}")
            # 如果解析失敗，回傳基本結構
            return {
                "concepts": [],
                "methods": [],
                "applications": [],
                "problems": [],
                "main_topic": article_info["title"],
                "suggested_tags": ["科學研究"],
            }

    def generate_wiki_content(
        self,
        article_info: dict[str, str],
        content_type: str,
        topic: str,
        existing_content: str = "",
    ) -> str:
        """
        產生 Wiki 條目內容

        Args:
            article_info: 文章資訊
            content_type: 內容類型 (concept, method, application, problem, main)
            topic: 條目主題
            existing_content: 現有內容（用於更新現有條目）

        Returns:
            產生的 Markdown 內容
        """
        if not self.llm:
            raise ValueError("LLM 未初始化，無法生成內容。請檢查 API 金鑰或模型名稱。")

        translated_content = self.translation_service.translate_to_traditional_chinese(
            article_info["full_story"]
        )

        if existing_content:
            system_prompt = dedent(
                f"""
                請根據新提供的科學文章資訊，更新現有的 Wiki 條目內容。

                ## 更新要求：
                1. 保留現有內容的有價值部分
                2. 整合新資訊，避免重複
                3. 確保內容的連貫性和完整性
                4. 每一句話都必須有精確的來源標註（如 [1]），並且來源需在 References 部分以 APA 8 格式列出。
                5. 在頁面底部的 References 部分新增新的引用，並確保每個標註都能對應到正確的來源。

                ## 內容類型：{content_type}
                ## 條目主題：{topic}

                請回傳完整的更新後 Markdown 內容，並確保每一句話都有來源標註。
            """
            )

            human_prompt = dedent(
                f"""
                現有條目內容：
                {existing_content}

                ---

                新增資訊來源：
                標題：{article_info['title']}
                來源：{article_info['source']}
                日期：{article_info['date']}
                摘要：{article_info['summary']}
                完整內容：{translated_content}
                URL：{article_info['url']}

                請更新現有條目，整合新資訊。
            """
            )
        else:
            system_prompt = dedent(
                f"""
                請根據科學文章資訊建立 Wiki 條目內容。

                ## 建立要求：
                1. 使用清晰的 Markdown 格式
                2. 內容應該準確、簡潔、易於理解
                3. 每一句話都必須有精確的來源標註（如 [1]），並且來源需在 References 部分以 APA 8 格式列出。
                4. 在頁面底部新增 References 部分，並確保每個標註都能對應到正確的來源。
                5. 根據內容類型調整結構和重點

                ## 內容類型：{content_type}
                ## 條目主題：{topic}

                請回傳完整的 Markdown 內容，並確保每一句話都有來源標註。
            """
            )

            human_prompt = dedent(
                f"""
                請根據以下科學文章資訊建立 Wiki 條目：

                標題：{article_info['title']}
                來源：{article_info['source']}
                日期：{article_info['date']}
                摘要：{article_info['summary']}
                完整內容：{translated_content}
                URL：{article_info['url']}
            """
            )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Join list elements as strings, converting dicts to JSON
            return "\n".join(
                (
                    json.dumps(item, ensure_ascii=False)
                    if isinstance(item, dict)
                    else str(item)
                )
                for item in content
            )
        elif isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False)
        else:
            return str(content)

    def suggest_merge_opportunities(
        self, new_topic: str, existing_pages: list[dict]
    ) -> list[tuple[str, float]]:
        """
        建議合併機會，避免知識碎片化

        Args:
            new_topic: 新條目主題
            existing_pages: 現有頁面列表

        Returns:
            建議合併的頁面列表，包含頁面標題和相似度分數
        """
        if not self.llm or not existing_pages:
            return []

        system_prompt = dedent(
            """
            請分析新主題與現有頁面的相關性，判斷是否應該合併到現有頁面而不是建立新頁面。

            請評估每個現有頁面與新主題的相關性，回傳 0-1 之間的分數：
            - 0.8-1.0: 高度相關，建議合併
            - 0.5-0.8: 中等相關，可考慮合併
            - 0-0.5: 低相關性，建議獨立建立

            只回傳 JSON 格式的結果，包含 page_title 和 similarity_score 欄位的陣列。
        """
        )
        existing_titles = [
            page["title"] for page in existing_pages[:10]
        ]  # 限制數量避免過長

        human_prompt = dedent(
            f"""
            新主題：{new_topic}

            現有頁面標題：
            {chr(10).join(existing_titles)}

            請評估相關性並回傳 JSON 結果。
        """
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        response = self.llm.invoke(messages)

        try:
            content = response.content
            if isinstance(content, str):
                similarity_results = json.loads(content)
            elif isinstance(content, list):
                similarity_results = content
            else:
                raise ValueError("LLM 回應內容格式無法解析")
            return [
                (item["page_title"], item["similarity_score"])
                for item in similarity_results
                if item["similarity_score"] > 0.5
            ]
        except (json.JSONDecodeError, KeyError, ValueError):
            return []

    def _generate_basic_content(
        self,
        article_info: dict[str, str],
        topic: str,
        existing_content: str = "",
    ) -> str:
        """
        產生基本的 Markdown 內容（不使用 LLM）

        Args:
            article_info: 文章資訊
            topic: 條目主題
            existing_content: 現有內容

        Returns:
            基本的 Markdown 內容
        """
        if existing_content:
            # 如果有現有內容，簡單追加新資訊
            new_section = dedent(
                f"""
                
                ## 新增資訊 ({article_info.get('date', '未知日期')})

                基於 ScienceDaily 文章《{article_info.get('title', '未知標題')}》的資訊：

                ### 摘要
                {article_info.get('summary', '無摘要資訊')}

                ### 詳細內容
                {article_info.get('full_story', '無詳細內容')}
                
            """
            )
            # 檢查是否已有 References 部分
            if (
                "## References" in existing_content
                or "### References" in existing_content
            ):
                # 在 References 之前插入新內容
                parts = existing_content.split("## References")
                if len(parts) == 1:
                    parts = existing_content.split("### References")
                    separator = "### References"
                else:
                    separator = "## References"

                if len(parts) > 1:
                    return parts[0] + new_section + separator + parts[1]
                else:
                    return existing_content + new_section
            else:
                # 直接追加
                return (
                    existing_content
                    + new_section
                    + self._generate_references_section(article_info)
                )
        else:
            # 建立新內容
            content = dedent(
                f"""
                # {topic}

                ## 概述

                {article_info.get('summary', '無摘要資訊')}

                ## 詳細資訊

                {article_info.get('full_story', '無詳細內容')}

                ## 來源資訊

                - **來源**: {article_info.get('source', '未知來源')}
                - **發佈日期**: {article_info.get('date', '未知日期')}
                - **原文連結**: {article_info.get('url', '無連結')}

                {self._generate_references_section(article_info)}
            """
            )
            return content

    def _generate_references_section(self, article_info: dict[str, str]) -> str:
        """
        產生參考文獻部分

        Args:
            article_info: 文章資訊

        Returns:
            參考文獻部分的 Markdown
        """
        source = article_info.get("source", "ScienceDaily")
        date = article_info.get("date", "未知日期")
        title = article_info.get("title", "未知標題")
        url = article_info.get("url", "")

        # 嘗試產生 APA 格式的引用
        # 注意：這是簡化版本，真正的 APA 格式需要更多資訊
        if url:
            citation = f"{source}. ({date}). *{title}*. Retrieved from {url}"
        else:
            citation = f"{source}. ({date}). *{title}*."

        return dedent(
            f"""
            ## References

            {citation}
        """
        )
