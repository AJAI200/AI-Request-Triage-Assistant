from pydantic import BaseModel
from typing import Optional

class TriageResponseDTO(BaseModel):
    id: int
    status: str  # "classified" | "needs_review"
    raw_text: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    priority_reason: Optional[str] = None
    owner: Optional[str] = None
    draft_response: Optional[str] = None
    message: Optional[str] = None  # Populated only when status == "needs_review"
    process_time_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
