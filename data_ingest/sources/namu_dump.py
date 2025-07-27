from __future__ import annotations

"""나무위키 JSON 덤프 파서 → raw_data.

사용 예::
    python -m data_ingest.sources.namu_dump dump.json --mode initial

덤프 구조(예시)::
    {
      "title": "리그 오브 레전드",
      "text": "...",
      "document_id": 12345,
      "revision": 67890,
      ...
    }

필요 항목만 골라 텍스트를 raw_data 로 적재한다.
"""

import argparse
import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from .base import BaseCrawler, RawDoc


class NamuwikiDumpCrawler(BaseCrawler):
    source = "namuwiki_dump"

    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    # 덤프는 스냅샷이므로 initial 만 구현, incremental 은 새 덤프 파일 처리로 대체

    async def crawl_initial(self) -> AsyncIterator[RawDoc]:
        open_fn = gzip.open if self.path.suffix == ".gz" else open
        with open_fn(self.path, "rt", encoding="utf-8") as fp:
            for line in fp:
                obj = json.loads(line)
                title = obj.get("title")
                text = obj.get("text")
                doc_id = f"namu:{obj.get('document_id')}:{obj.get('revision')}"
                if not text:
                    continue
                yield RawDoc(doc_id=doc_id, text=text)

    async def crawl_incremental(self, since: datetime):  # noqa: D401 – not used
        # dump 기반은 증분이 아닌 새 파일 ingest 로 처리.
        return
        yield  # type: ignore


# CLI -------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="Namuwiki dump parser")
    p.add_argument("dump_path", type=Path, help="덤프 JSON(.gz) 파일 경로")
    p.add_argument(
        "--mode", choices=["initial"], default="initial", help="only initial supported"
    )
    return p


def main():
    args = _build_parser().parse_args()
    crawler = NamuwikiDumpCrawler(args.dump_path)

    import asyncio

    asyncio.run(crawler.run_initial())


if __name__ == "__main__":
    main() 