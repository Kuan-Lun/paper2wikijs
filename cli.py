#!/usr/bin/env python3
"""
ScienceDaily 到 Wiki.js 的命令列工具
"""
import argparse
from src.paper2wikijs import ScienceDaily2WikiService


def main():
    parser = argparse.ArgumentParser(
        description="將 ScienceDaily 文章轉換為 Wiki.js 條目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:
  %(prog)s --preview https://www.sciencedaily.com/releases/2025/03/250324181544.htm
  %(prog)s --create --main-only https://www.sciencedaily.com/releases/2025/03/250324181544.htm
  %(prog)s --create https://www.sciencedaily.com/releases/2025/03/250324181544.htm
        """,
    )

    parser.add_argument("url", help="ScienceDaily 文章的 URL")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--preview", "-p", action="store_true", help="預覽分析結果，不建立頁面"
    )
    mode_group.add_argument(
        "--create", "-c", action="store_true", help="建立 Wiki 頁面"
    )

    parser.add_argument(
        "--main-only", "-m", action="store_true", help="只建立主條目，不拆分子條目"
    )

    args = parser.parse_args()

    # 檢查 URL 格式
    if not args.url.startswith("https://www.sciencedaily.com/"):
        print("警告: URL 似乎不是 ScienceDaily 的文章連結")
        response = input("是否繼續? (y/n): ")
        if response.lower() not in ["y", "yes", "是"]:
            return 0

    try:
        # 初始化服務
        service = ScienceDaily2WikiService(args.config)

        if args.preview:
            print("=== 預覽分析結果 ===")
            result = service.preview_analysis(args.url)

            if result.success:
                article_info = result.article_info
                analysis = result.analysis

                print(f"文章標題: {article_info['title']}")
                print(f"來源: {article_info['source']}")
                print(f"日期: {article_info['date']}")
                print(f"摘要: {article_info['summary'][:100]}...")
                print()
                print(f"主要話題: {result.get_main_topic()}")
                print(f"識別的概念: {result.get_concepts_count()} 個")
                if analysis["concepts"]:
                    for i, concept in enumerate(analysis["concepts"][:5], 1):
                        print(f"  {i}. {concept}")
                    if len(analysis["concepts"]) > 5:
                        print(f"  ... 還有 {len(analysis['concepts']) - 5} 個")

                print(f"識別的方法: {result.get_methods_count()} 個")
                if analysis["methods"]:
                    for i, method in enumerate(analysis["methods"][:3], 1):
                        print(f"  {i}. {method}")
                    if len(analysis["methods"]) > 3:
                        print(f"  ... 還有 {len(analysis['methods']) - 3} 個")

                print(f"建議標籤: {', '.join(analysis['suggested_tags'])}")

                if result.has_merge_suggestions():
                    print("\n=== 合併建議 ===")
                    for title, score in result.merge_suggestions:
                        print(f"- {title} (相似度: {score:.2f})")

                if result.existing_pages:
                    print(f"\n找到 {result.get_existing_pages_count()} 個相關現有頁面")

            else:
                print(f"預覽失敗: {result.error or '未知錯誤'}")
                return 1

        elif args.create:
            print("=== 建立 Wiki 頁面 ===")
            result = service.process_sciencedaily_url(args.url, args.main_only)

            if result.success:
                print("處理完成!")
                print(f"文章標題: {result.article_info['title']}")

                if result.created_pages:
                    print(f"\n建立了 {len(result.created_pages)} 個頁面:")
                    for page in result.created_pages:
                        status = "成功" if page.success else "失敗"
                        print(f"  {status} {page.title} ({page.type})")
                        if not page.success:
                            print(
                                f"    錯誤: {page.error or page.message or '未知錯誤'}"
                            )

                if result.updated_pages:
                    print(f"\n更新了 {len(result.updated_pages)} 個頁面:")
                    for page in result.updated_pages:
                        status = "成功" if page.success else "失敗"
                        print(f"  {status} {page.title} ({page.type})")
                        if not page.success:
                            print(
                                f"    錯誤: {page.error or page.message or '未知錯誤'}"
                            )

                if result.merge_suggestions:
                    print("\n=== 建議的合併機會 ===")
                    for title, score in result.merge_suggestions:
                        print(f"- {title} (相似度: {score:.2f})")

            else:
                print(f"處理失敗: {result.error or '未知錯誤'}")
                return 1

    except KeyboardInterrupt:
        print("\n操作被使用者取消")
        return 0
    except Exception as e:
        print(f"發生錯誤: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
