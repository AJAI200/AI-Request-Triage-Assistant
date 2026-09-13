from src.migrations.runner import run_migrations

async def init_db():
    await run_migrations()
