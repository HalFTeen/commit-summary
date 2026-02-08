"""CLI interface for the TikTok comment scraper."""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import List

from tiktok_comment_scraper.config.settings import settings
from tiktok_comment_scraper.llm.client import LLMClient
from tiktok_comment_scraper.models.comment import VideoSummary
from tiktok_comment_scraper.scraper.tiktok import TikTokAPIScraper, TikTokScraper


async def scrape_and_analyze(
    video_url: str,
    max_comments: int = None,
    use_api: bool = True,
    output_dir: str = None,
) -> VideoSummary:
    """Main workflow: scrape comments and analyze with LLM.

    Args:
        video_url: TikTok video URL
        max_comments: Maximum comments to scrape
        use_api: Use API scraper (True) or browser scraper (False)
        output_dir: Output directory for results

    Returns:
        VideoSummary with scraped and analyzed data
    """
    output_dir = output_dir or settings.OUTPUT_DIR
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"Scraping comments from: {video_url}")

    if use_api:
        scraper = TikTokAPIScraper()
        comments = await scraper.scrape_video_comments(video_url, max_comments)
    else:
        async with TikTokScraper(headless=True) as scraper:
            comments = await scraper.scrape_video_comments(video_url, max_comments)

    print(f"Scraped {len(comments)} comments")

    video_id = scraper._extract_video_id(video_url)
    summary = VideoSummary(video_id=video_id, total_comments=len(comments), comments=comments)

    print("Analyzing comments with LLM...")

    llm_client = LLMClient()

    analysis_results = llm_client.batch_analyze(comments)
    summary.analysis_results = analysis_results

    print("Generating summary...")

    overall_summary = llm_client.summarize_comments(comments)
    summary.overall_summary = overall_summary

    summary.calculate_sentiment_distribution()

    print(f"Sentiment distribution: {summary.sentiment_distribution}")

    output_file = Path(output_dir) / f"{video_id}_summary.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    print(f"Results saved to: {output_file}")

    return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TikTok/Douyin Comment Scraper with AI Analysis"
    )

    parser.add_argument("video_url", help="TikTok/Douyin video URL")
    parser.add_argument(
        "--max-comments",
        type=int,
        help="Maximum number of comments to scrape",
    )
    parser.add_argument(
        "--use-browser",
        action="store_true",
        help="Use browser-based scraping (slower but more reliable)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help=f"Output directory (default: {settings.OUTPUT_DIR})",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Z.ai API key (overrides environment variable)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.ZAI_MODEL,
        help=f"LLM model to use (default: {settings.ZAI_MODEL})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.BATCH_SIZE,
        help=f"Batch size for LLM processing (default: {settings.BATCH_SIZE})",
    )

    args = parser.parse_args()

    if args.api_key:
        os.environ["ZAI_API_KEY"] = args.api_key

    if args.model:
        settings.ZAI_MODEL = args.model

    if args.batch_size:
        settings.BATCH_SIZE = args.batch_size

    try:
        summary = asyncio.run(
            scrape_and_analyze(
                video_url=args.video_url,
                max_comments=args.max_comments,
                use_api=not args.use_browser,
                output_dir=args.output_dir,
            )
        )

        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Video ID: {summary.video_id}")
        print(f"Total Comments: {summary.total_comments}")
        print(f"Sentiment Distribution: {summary.sentiment_distribution}")
        print(f"\nOverall Summary:\n{summary.overall_summary}")
        print("=" * 50)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
