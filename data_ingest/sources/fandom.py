from __future__ import annotations

"""Fandom 위키 크롤러.

사용 예::
    python -m data_ingest.sources.fandom --wiki leagueoflegends --mode initial
"""

import argparse
from datetime import datetime

from .mediawiki import MediaWikiCrawler


class FandomCrawler(MediaWikiCrawler):
    source = "fandom"

    def __init__(self, wiki: str):
        super().__init__()
        self.wiki = wiki
        self.api_endpoint = f"https://{wiki}.fandom.com/api.php"
        self.site_tag = f"fandom:{wiki}"


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="Fandom crawler")
    p.add_argument("--wiki", required=True, help="subdomain, e.g. leagueoflegends")
    p.add_argument(
        "--mode",
        choices=["initial", "incremental"],
        default="incremental",
        help="crawl mode",
    )
    return p


def main():
    args = _build_parser().parse_args()
    crawler = FandomCrawler(args.wiki)

    if args.mode == "initial":
        import asyncio

        asyncio.run(crawler.run_initial())
    else:
        import asyncio

        asyncio.run(crawler.run_incremental())


if __name__ == "__main__":
    main() 