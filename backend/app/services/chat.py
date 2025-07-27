from typing import List

from sqlmodel import select

from app.models.chat import ChatMessage
from app.models.db import get_session


async def save_chat(user_id: str, question: str, answer: str, game: str | None = None) -> None:
    cm = ChatMessage(
        user_google_sub=user_id,
        question=question,
        answer=answer,
        game=game or "generic",
    )
    async with get_session() as session:
        session.add(cm)
        await session.commit()


async def list_chat_history(user_id: str, limit: int = 20, game: str | None = None) -> List[ChatMessage]:
    async with get_session() as session:
        stmt = select(ChatMessage).where(ChatMessage.user_google_sub == user_id)
        if game:
            stmt = stmt.where(ChatMessage.game == game)
        stmt = stmt.order_by(ChatMessage.created_at.desc()).limit(limit)
        result = await session.exec(stmt)
        return list(result.all()) 