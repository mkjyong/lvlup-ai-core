from __future__ import annotations

"""StrategyWiki 크롤러 (단일 사이트)."""

import argparse

from .mediawiki import MediaWikiCrawler


class StrategyWikiCrawler(MediaWikiCrawler):
    source = "strategywiki"
    api_endpoint = "https://strategywiki.org/api.php"
    site_tag = "strategywiki"

    def __init__(self):
        super().__init__()


# CLI --------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="StrategyWiki crawler")
    p.add_argument(
        "--mode", choices=["initial", "incremental"], default="incremental", help="crawl mode"
    )
    return p


def main():
    args = _build_parser().parse_args()
    crawler = StrategyWikiCrawler()

    import asyncio

    if args.mode == "initial":
        asyncio.run(crawler.run_initial())
    else:
        asyncio.run(crawler.run_incremental())


if __name__ == "__main__":
    main() 