import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.prompt_template import PromptTemplate
from src.agents.prompts import CLASSIFY_ROUTE_PROMPT, DRAFT_RESPONSE_PROMPT

logger = logging.getLogger("triage_assistant.prompt_repository")

class PromptRepository:
    async def get_active_prompt(self, session: AsyncSession, prompt_name: str) -> str:
        stmt = select(PromptTemplate).where(
            PromptTemplate.name == prompt_name,
            PromptTemplate.is_active == True
        ).order_by(PromptTemplate.version.desc())
        
        result = await session.execute(stmt)
        template = result.scalars().first()
        if template and template.template_text:
            return template.template_text

        # Fallback to default in-memory prompt strings if DB template not found
        if prompt_name == "CLASSIFY_ROUTE_PROMPT":
            return CLASSIFY_ROUTE_PROMPT
        elif prompt_name == "DRAFT_RESPONSE_PROMPT":
            return DRAFT_RESPONSE_PROMPT
        
        raise ValueError(f"Unknown prompt template name: {prompt_name}")

_prompt_repository = PromptRepository()

def get_prompt_repository() -> PromptRepository:
    return _prompt_repository
