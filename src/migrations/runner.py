import logging
import bcrypt
from sqlalchemy import select, text, inspect
from src.models.base import Base, engine, AsyncSessionLocal
from src.models.category import Category
from src.models.owner import Owner
from src.models.user import User
from src.models.prompt_template import PromptTemplate
from src.agents.prompts import CLASSIFY_ROUTE_PROMPT, DRAFT_RESPONSE_PROMPT

logger = logging.getLogger("triage_assistant.migrations")

def _hash_pwd(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

async def run_migrations():
    """
    Dedicated database migration runner.
    Executes table creation, schema alters for missing columns, and seeds initial data.
    """
    logger.info("Executing database migration schema creation...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        def migrate_columns(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            if "request" in tables:
                req_cols = [c['name'] for c in inspector.get_columns('request')]
                if 'process_time_ms' not in req_cols:
                    logger.info("Adding process_time_ms column to request table...")
                    sync_conn.execute(text("ALTER TABLE request ADD COLUMN process_time_ms FLOAT"))
                if 'prompt_tokens' not in req_cols:
                    logger.info("Adding token tracking columns to request table...")
                    sync_conn.execute(text("ALTER TABLE request ADD COLUMN prompt_tokens INTEGER"))
                    sync_conn.execute(text("ALTER TABLE request ADD COLUMN completion_tokens INTEGER"))
                    sync_conn.execute(text("ALTER TABLE request ADD COLUMN total_tokens INTEGER"))

            if "error_log" in tables:
                err_cols = [c['name'] for c in inspector.get_columns('error_log')]
                if 'process_time_ms' not in err_cols:
                    logger.info("Adding process_time_ms column to error_log table...")
                    sync_conn.execute(text("ALTER TABLE error_log ADD COLUMN process_time_ms FLOAT"))

        await conn.run_sync(migrate_columns)

    await seed_initial_data()

async def seed_initial_data():
    async with AsyncSessionLocal() as session:
        # Seed Categories
        cat_stmt = select(Category)
        cat_res = await session.execute(cat_stmt)
        if len(cat_res.scalars().all()) == 0:
            session.add_all([
                Category(name=c) for c in ["Sales", "Support", "Billing", "Technical", "Other"]
            ])

        # Seed Owners
        own_stmt = select(Owner)
        own_res = await session.execute(own_stmt)
        if len(own_res.scalars().all()) == 0:
            session.add_all([
                Owner(name=o) for o in ["Sales Team", "Client Success", "Finance", "Engineering"]
            ])

        # Seed Demo Admin User (username: admin, password: password123)
        user_stmt = select(User).where(User.username == "admin")
        user_res = await session.execute(user_stmt)
        if user_res.scalar_one_or_none() is None:
            hashed = _hash_pwd("password123")
            session.add(User(username="admin", hashed_password=hashed, role="admin"))

        # Seed Prompt Templates
        p1_stmt = select(PromptTemplate).where(PromptTemplate.name == "CLASSIFY_ROUTE_PROMPT")
        p1_res = await session.execute(p1_stmt)
        if p1_res.scalar_one_or_none() is None:
            session.add(PromptTemplate(
                name="CLASSIFY_ROUTE_PROMPT",
                template_text=CLASSIFY_ROUTE_PROMPT,
                version=1,
                is_active=True
            ))

        p2_stmt = select(PromptTemplate).where(PromptTemplate.name == "DRAFT_RESPONSE_PROMPT")
        p2_res = await session.execute(p2_stmt)
        if p2_res.scalar_one_or_none() is None:
            session.add(PromptTemplate(
                name="DRAFT_RESPONSE_PROMPT",
                template_text=DRAFT_RESPONSE_PROMPT,
                version=1,
                is_active=True
            ))

        await session.commit()
        logger.info("Database migration & initial data seeding completed successfully.")
