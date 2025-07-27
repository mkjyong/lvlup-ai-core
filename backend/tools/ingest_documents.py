#!/usr/bin/env python
"""문서 임베딩 삽입 CLI.

Usage:
    python tools/ingest_documents.py docs/ --game lol
"""
import asyncio
import sys
from pathlib import Path

from app.services.llm import embedding
from app.models.game_knowledge import GameKnowledge
from app.models.db import get_session


aSync = asyncio.run


async def ingest(dirpath: Path, game: str):
    async with get_session() as session:
        for file in dirpath.glob("*.txt"):
            content = file.read_text()
            emb = await embedding(content[:4096])
            doc = GameKnowledge(
                doc_id=file.stem,
                chunk_id=0,
                text=content,
                embedding=emb,
                score=0.5,
                metadata={"game": game},
            )
            session.add(doc)
        await session.commit()


if __name__ == "__main__":
    p = Path(sys.argv[1])
    game = sys.argv[2]
    aSync(ingest(p, game)) 