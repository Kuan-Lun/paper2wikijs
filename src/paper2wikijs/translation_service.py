"""
翻譯服務
專門處理文本翻譯的獨立服務類
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from textwrap import dedent

from .config import OPENAI_API_KEY


class TranslationService:
    """專門處理文本翻譯的服務類"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        初始化翻譯服務

        Args:
            model_name: 使用的 LLM 模型名稱
        """
        self.llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=OPENAI_API_KEY)

    def translate_to_traditional_chinese(self, text: str) -> str:
        """
        將文本翻譯成繁體中文

        Args:
            text: 需要翻譯的文本

        Returns:
            翻譯後的繁體中文文本
        """
        if not self.llm or not text.strip():
            return text

        system_prompt = dedent(
            """
            請將提供的文本翻譯成繁體中文。

            要求：
            1. 保持原文的意思和結構
            2. 使用繁體中文字符
            3. 保持專業術語的準確性。
               若原文包含專有名詞或術語，第一次出現時請以「譯文 (原文)」格式呈現，例如「共整合 (cointegration)」。後續出現同一術語時，僅使用譯文。
            4. 只回傳翻譯結果，不要包含其他說明文字
        """
        )

        human_prompt = dedent(
            f"""
            請將以下文本翻譯成繁體中文：

            {text}
        """
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, list):
                return "\n".join(str(item) for item in content).strip()
            else:
                return str(content).strip()
        except Exception as e:
            print(f"翻譯失敗，使用原文: {e}")
            return text

    def translate_to_language(self, text: str, target_language: str) -> str:
        """
        將文本翻譯成指定語言

        Args:
            text: 需要翻譯的文本
            target_language: 目標語言

        Returns:
            翻譯後的文本
        """
        if not self.llm or not text.strip():
            return text

        system_prompt = dedent(
            f"""
            請將提供的文本翻譯成{target_language}。

            要求：
            1. 保持原文的意思和結構
            2. 使用正確的目標語言字符和語法
            3. 保持專業術語的準確性
            4. 只回傳翻譯結果，不要包含其他說明文字
        """
        )

        human_prompt = dedent(
            f"""
            請將以下文本翻譯成{target_language}：

            {text}
        """
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, list):
                return "\n".join(str(item) for item in content).strip()
            else:
                return str(content).strip()
        except Exception as e:
            print(f"翻譯失敗，使用原文: {e}")
            return text
