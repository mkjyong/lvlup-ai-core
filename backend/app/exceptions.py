"""애플리케이션 공통 예외 정의."""
from fastapi import status


class AIError(Exception):
    """LLM 호출 등 AI 관련 에러.

    Attributes
    ----------
    message : str
        오류 메시지
    status_code : int
        HTTP 상태 코드(기본 500)
    """

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:  # noqa: D401
        return {"detail": self.message} 