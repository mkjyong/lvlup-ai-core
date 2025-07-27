from __future__ import annotations

"""Liquipedia 위키 크롤러.

예::
    python -m data_ingest.sources.liquipedia --game dota2 --mode initial
"""

import argparse

from .mediawiki import MediaWikiCrawler


class LiquipediaCrawler(MediaWikiCrawler):
    source = "liquipedia"

    def __init__(self, game: str):
        super().__init__()
        self.game = game
        self.api_endpoint = f"https://liquipedia.net/{game}/api.php"
        self.site_tag = f"liquipedia:{game}"


# ---------------------------------------------------------
# CLI entry
# ---------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="Liquipedia crawler")
    p.add_argument("--game", required=True, help="게임 서브도메인, 예: dota2, leagueoflegends")
    p.add_argument(
        "--mode", choices=["initial", "incremental"], default="incremental", help="crawl mode"
    )
    return p


def main():
    args = _build_parser().parse_args()
    crawler = LiquipediaCrawler(args.game)

    import asyncio

    if args.mode == "initial":
        asyncio.run(crawler.run_initial())
    else:
        asyncio.run(crawler.run_incremental())


if __name__ == "__main__":
    main() 