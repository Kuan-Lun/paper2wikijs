"""
ScienceDaily 到 Wiki 的主要服務類
整合所有功能，實現從 ScienceDaily URL 到 Wiki 條目的完整流程
"""

from typing import Optional, Any
from dataclasses import dataclass, field

from .sciencedaily_extractor import ScienceDailyExtractor
from .wikijs_client import WikiJSClient
from .knowledge_processor import KnowledgeProcessor


@dataclass
class PageProcessingResult:
    """單一頁面處理結果"""

    action: str  # "created", "updated", "failed", "skipped"
    title: str
    path: Optional[str] = None
    type: Optional[str] = None
    success: bool = False
    message: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PreviewResult:
    """預覽分析結果類別"""

    success: bool
    article_info: Optional[dict[str, str]] = None
    analysis: Optional[dict[str, Any]] = None
    existing_pages: Optional[list[dict]] = None
    merge_suggestions: Optional[list[tuple]] = None
    error: Optional[str] = None

    def get_concepts_count(self) -> int:
        """取得概念數量"""
        if not self.analysis:
            return 0
        return len(self.analysis.get("concepts", []))

    def get_methods_count(self) -> int:
        """取得方法數量"""
        if not self.analysis:
            return 0
        return len(self.analysis.get("methods", []))

    def get_applications_count(self) -> int:
        """取得應用數量"""
        if not self.analysis:
            return 0
        return len(self.analysis.get("applications", []))

    def get_main_topic(self) -> str:
        """取得主要主題"""
        if not self.analysis:
            return "未知"
        return self.analysis.get("main_topic", "未知")

    def has_merge_suggestions(self) -> bool:
        """檢查是否有合併建議"""
        return bool(self.merge_suggestions)

    def get_existing_pages_count(self) -> int:
        """取得現有相關頁面數量"""
        if not self.existing_pages:
            return 0
        return len(self.existing_pages)


@dataclass
class ProcessingResult:
    """處理結果類別，封裝所有處理結果資訊"""

    success: bool
    article_info: Optional[dict[str, str]] = None
    analysis: Optional[dict[str, Any]] = None
    merge_suggestions: Optional[list[tuple]] = None
    created_pages: list[PageProcessingResult] = field(default_factory=list)
    updated_pages: list[PageProcessingResult] = field(default_factory=list)
    error: Optional[str] = None

    def add_created_page(self, page_result: PageProcessingResult):
        """新增建立的頁面結果"""
        self.created_pages.append(page_result)

    def add_updated_page(self, page_result: PageProcessingResult):
        """新增更新的頁面結果"""
        self.updated_pages.append(page_result)

    def get_total_pages_count(self) -> int:
        """取得總頁面處理數量"""
        return len(self.created_pages) + len(self.updated_pages)

    def get_successful_pages_count(self) -> int:
        """取得成功處理的頁面數量"""
        successful_created = sum(1 for page in self.created_pages if page.success)
        successful_updated = sum(1 for page in self.updated_pages if page.success)
        return successful_created + successful_updated

    def has_errors(self) -> bool:
        """檢查是否有錯誤"""
        if self.error:
            return True
        failed_created = any(not page.success for page in self.created_pages)
        failed_updated = any(not page.success for page in self.updated_pages)
        return failed_created or failed_updated


class ScienceDaily2WikiService:
    """ScienceDaily 到 Wiki 的主要服務類"""

    def __init__(self):
        """
        初始化服務

        Args:
            config_path: Wiki.js 配置檔案路徑
        """
        self.extractor = ScienceDailyExtractor()
        self.wiki_client = WikiJSClient()
        self.knowledge_processor = KnowledgeProcessor()

    def process_sciencedaily_url(
        self, url: str, create_main_entry_only: bool = False
    ) -> ProcessingResult:
        """
        處理 ScienceDaily URL，建立相應的 Wiki 條目

        Args:
            url: ScienceDaily 文章 URL
            create_main_entry_only: 是否只建立主條目（不拆分子條目）

        Returns:
            處理結果字典
        """
        # 提取文章資訊
        print("正在提取文章資訊...")
        article_info = self.extractor.extract_article_info(url)

        if not article_info["title"]:
            return ProcessingResult(success=False, error="無法提取文章標題")

        # 分析知識結構
        print("正在分析知識結構...")
        analysis_result = self.knowledge_processor.analyze_content_for_wiki_structure(
            article_info
        )

        main_topic = analysis_result.get("main_topic", article_info["title"])

        # 檢查是否有現有相關頁面
        print("正在搜尋相關頁面...")
        existing_pages = self.wiki_client.search_pages(main_topic)

        # 建議合併機會
        print("正在建議合併機會...")
        merge_suggestions = self.knowledge_processor.suggest_merge_opportunities(
            main_topic, existing_pages
        )

        results = ProcessingResult(
            success=True,
            article_info=article_info,
            analysis=analysis_result,
            merge_suggestions=merge_suggestions,
        )

        # 處理主條目
        print("正在處理主條目...")
        main_page_result = self._process_main_entry(
            article_info,
            main_topic,
            analysis_result.get("suggested_tags", []),
            existing_pages,
            merge_suggestions,
        )

        if main_page_result.action == "created":
            results.add_created_page(main_page_result)
        elif main_page_result.action == "updated":
            results.add_updated_page(main_page_result)

        # 如果不只建立主條目，則建立子條目
        print("正在處理子條目...")
        if not create_main_entry_only:
            sub_entries_result = self._process_sub_entries(
                article_info, analysis_result
            )
            for page in sub_entries_result["created"]:
                results.add_created_page(page)
            for page in sub_entries_result["updated"]:
                results.add_updated_page(page)

        return results

    def _process_main_entry(
        self,
        article_info: dict[str, str],
        main_topic: str,
        tags: list[str],
        existing_pages: list[dict],
        merge_suggestions: list[tuple],
    ) -> PageProcessingResult:
        """處理主條目"""

        # 檢查是否應該合併到現有頁面
        best_merge_candidate = None
        if merge_suggestions:
            # 選擇相似度最高的候選
            best_merge_candidate = max(merge_suggestions, key=lambda x: x[1])
            if best_merge_candidate[1] >= 0.8:  # 高相似度，建議合併
                # 找到對應的頁面
                target_page = next(
                    (
                        page
                        for page in existing_pages
                        if page["title"] == best_merge_candidate[0]
                    ),
                    None,
                )
                if target_page:
                    return self._update_existing_page(
                        target_page, article_info, "main", main_topic
                    )

        # 建立新的主條目
        return self._create_new_page(article_info, "main", main_topic, tags)

    def _process_sub_entries(
        self, article_info: dict[str, str], analysis_result: dict[str, Any]
    ) -> dict[str, list[PageProcessingResult]]:
        """處理子條目"""
        created_pages = []
        updated_pages = []

        # 處理概念條目
        concepts: list = analysis_result.get("concepts", [])
        print(f"正在處理 {len(concepts)} 個概念條目...")
        for i, concept in enumerate(concepts, 1):
            print(f"  - 概念 {i}/{len(concepts)}: {concept}")
            result = self._create_or_update_entry(article_info, "concept", concept)
            if result.action == "created":
                created_pages.append(result)
            elif result.action == "updated":
                updated_pages.append(result)

        # 處理方法條目
        methods: list = analysis_result.get("methods", [])
        print(f"正在處理 {len(methods)} 個方法條目...")
        for i, method in enumerate(methods, 1):
            print(f"  - 方法 {i}/{len(methods)}: {method}")
            result = self._create_or_update_entry(article_info, "method", method)
            if result.action == "created":
                created_pages.append(result)
            elif result.action == "updated":
                updated_pages.append(result)

        # 處理應用條目
        applications: list = analysis_result.get("applications", [])
        print(f"正在處理 {len(applications)} 個應用條目...")
        for i, application in enumerate(applications, 1):
            print(f"  - 應用 {i}/{len(applications)}: {application}")
            result = self._create_or_update_entry(
                article_info, "application", application
            )
            if result.action == "created":
                created_pages.append(result)
            elif result.action == "updated":
                updated_pages.append(result)

        return {"created": created_pages, "updated": updated_pages}

    def _create_or_update_entry(
        self, article_info: dict[str, str], content_type: str, topic: str
    ) -> PageProcessingResult:
        """建立或更新條目"""
        if not topic:
            return PageProcessingResult(
                action="skipped",
                title=topic,
                type=content_type,
                success=False,
                error="Topic is empty, skipping.",
            )
        # 搜尋現有相關頁面
        print(f"    正在為 '{topic}' 搜尋現有頁面...")
        existing_pages = self.wiki_client.search_pages(topic)

        # 檢查是否有高度匹配的頁面
        for page in existing_pages:
            if page["title"].lower() == topic.lower():
                return self._update_existing_page(
                    page, article_info, content_type, topic
                )

        # 建立新頁面
        return self._create_new_page(article_info, content_type, topic)

    def _create_new_page(
        self,
        article_info: dict[str, str],
        content_type: str,
        topic: str,
        tags: Optional[list[str]] = None,
    ) -> PageProcessingResult:
        """建立新頁面"""
        try:
            # 生成內容
            content = self.knowledge_processor.generate_wiki_content(
                article_info, content_type, topic
            )

            # 生成路徑
            safe_topic = topic.replace(" ", "-").replace("/", "-")
            path = f"science/{content_type}/{safe_topic}"

            # 建立頁面
            description = f"基於 ScienceDaily 文章《{article_info.get('title', '未知標題')}》的{content_type}條目"
            result = self.wiki_client.create_page(
                title=topic,
                content=content,
                path=path,
                tags=tags or ["科學研究", content_type],
                description=description,
            )

            return PageProcessingResult(
                action="created",
                title=topic,
                path=path,
                type=content_type,
                success=result["succeeded"],
                message=result.get("message", ""),
            )

        except Exception as e:
            return PageProcessingResult(
                action="failed",
                title=topic,
                type=content_type,
                success=False,
                error=str(e),
            )

    def _update_existing_page(
        self, page: dict, article_info: dict[str, str], content_type: str, topic: str
    ) -> PageProcessingResult:
        """更新現有頁面"""
        try:
            # 取得現有內容
            existing_content_data = self.wiki_client.get_page_content(int(page["id"]))
            existing_content = (
                existing_content_data["content"] if existing_content_data else ""
            )

            # 生成更新後的內容
            updated_content = self.knowledge_processor.generate_wiki_content(
                article_info, content_type, topic, existing_content
            )

            # 更新頁面
            result = self.wiki_client.update_page(
                page_id=int(page["id"]), title=page["title"], content=updated_content
            )

            return PageProcessingResult(
                action="updated",
                title=page["title"],
                path=page["path"],
                type=content_type,
                success=result["succeeded"],
                message=result.get("message", ""),
            )

        except Exception as e:
            return PageProcessingResult(
                action="failed",
                title=page["title"],
                type=content_type,
                success=False,
                error=str(e),
            )

    def preview_analysis(self, url: str) -> PreviewResult:
        """
        預覽分析結果，不實際建立頁面

        Args:
            url: ScienceDaily 文章 URL

        Returns:
            分析結果預覽
        """
        # 提取文章資訊
        article_info = self.extractor.extract_article_info(url)

        if not article_info["title"]:
            return PreviewResult(success=False, error="無法提取文章標題")

        # 分析知識結構
        analysis_result = self.knowledge_processor.analyze_content_for_wiki_structure(
            article_info
        )

        # 搜尋相關頁面
        main_topic = analysis_result.get("main_topic", article_info["title"])
        existing_pages = self.wiki_client.search_pages(main_topic)

        # 建議合併機會
        merge_suggestions = self.knowledge_processor.suggest_merge_opportunities(
            main_topic, existing_pages
        )

        return PreviewResult(
            success=True,
            article_info=article_info,
            analysis=analysis_result,
            existing_pages=existing_pages,
            merge_suggestions=merge_suggestions,
        )
