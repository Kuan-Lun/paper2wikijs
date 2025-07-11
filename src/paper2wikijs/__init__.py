"""
LangChain2WikiJS Package
用於將 ScienceDaily 內容轉換為 Wiki.js 條目的工具包
"""

from .service import ScienceDaily2WikiService
from .sciencedaily_extractor import ScienceDailyExtractor
from .wikijs_client import WikiJSClient
from .knowledge_processor import KnowledgeProcessor
from .translation_service import TranslationService

from .config import (
    OPENAI_API_KEY,
    WIKIJS_GRAPHQL_URL,
    WIKIJS_API_TOKEN,
    WIKIJS_LOCALE,
    WIKIJS_TIMEOUT,
)

__all__ = [
    "ScienceDaily2WikiService",
    "ScienceDailyExtractor",
    "WikiJSClient",
    "KnowledgeProcessor",
    "TranslationService",
    # Configuration variables
    "OPENAI_API_KEY",
    "WIKIJS_GRAPHQL_URL",
    "WIKIJS_API_TOKEN",
    "WIKIJS_LOCALE",
    "WIKIJS_TIMEOUT",
]
