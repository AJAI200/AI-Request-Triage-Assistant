from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.category import Category
from src.models.owner import Owner
from src.utils.exceptions import ValidationError

async def lookup_category_id(session: AsyncSession, category_name: str) -> int:
    stmt = select(Category).where(Category.name == category_name)
    res = await session.execute(stmt)
    cat = res.scalar_one_or_none()
    if cat:
        return cat.id
    
    # Fallback to 'Other'
    stmt_other = select(Category).where(Category.name == "Other")
    res_other = await session.execute(stmt_other)
    other = res_other.scalar_one_or_none()
    if other:
        return other.id
    raise ValidationError("Category 'Other' fallback lookup row not found in database.")

async def lookup_owner_id(session: AsyncSession, owner_name: str) -> int:
    stmt = select(Owner).where(Owner.name == owner_name)
    res = await session.execute(stmt)
    own = res.scalar_one_or_none()
    if own:
        return own.id

    # Fallback to 'Client Success'
    stmt_cs = select(Owner).where(Owner.name == "Client Success")
    res_cs = await session.execute(stmt_cs)
    cs = res_cs.scalar_one_or_none()
    if cs:
        return cs.id
    raise ValidationError("Owner 'Client Success' fallback lookup row not found in database.")
