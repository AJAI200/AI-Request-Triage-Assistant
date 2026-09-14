import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from src.main import app, global_exception_handler, serve_ui
from src.database import init_db
from src.repositories.user_repository import get_user_repository
from src.models.base import AsyncSessionLocal
from src.migrations.runner import _hash_pwd, run_migrations
from src.utils import exceptions
import src.utils.exceptions as exceptions_file

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

def test_serve_ui_route():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_global_exception_handler_direct():
    # Test global exception handler directly
    fake_req = TestClient(app).build_request("GET", "http://testserver/fake-endpoint")
    exc = RuntimeError("Simulated internal error")

    res = await global_exception_handler(fake_req, exc)
    assert res.status_code == 500

def test_app_lifespan():
    with TestClient(app) as client:
        res = client.get("/docs")
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_user_repository_create_and_get():
    import uuid
    unique_uname = f"repo_user_{uuid.uuid4().hex[:8]}"
    repo = get_user_repository()
    async with AsyncSessionLocal() as session:
        user = await repo.create_user(session, unique_uname, "hashed_pwd_123", role="staff")
        await session.commit()

        fetched = await repo.get_by_username(session, unique_uname)
        assert fetched is not None
        assert fetched.username == unique_uname
        assert fetched.role == "staff"

def test_migrations_runner_hash_pwd():
    hashed = _hash_pwd("my_secret_pass")
    assert hashed is not None
    assert len(hashed) > 10

def test_exceptions_module_exports():
    err1 = exceptions.LLMClientError("msg")
    err2 = exceptions.ValidationError("msg")
    err3 = exceptions.JSONParseError("msg")
    err4 = exceptions.AuthenticationError("msg")
    err5 = exceptions.PermissionError("msg")
    assert str(err1) == "msg"
    assert str(err2) == "msg"
    assert str(err3) == "msg"
    assert str(err4) == "msg"
    assert str(err5) == "msg"

@pytest.mark.asyncio
async def test_repository_database_error_handling():
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.exc import SQLAlchemyError
    from src.repositories.user_repository import UserRepository
    from src.repositories.prompt_repository import PromptRepository
    from src.repositories.triage_repository import TriageRepository
    from src.utils.exceptions import DatabaseError

    mock_session = AsyncMock()
    mock_session.execute.side_effect = SQLAlchemyError("Connection failed")

    user_repo = UserRepository()
    with pytest.raises(DatabaseError, match="Failed to fetch user"):
        await user_repo.get_by_username(mock_session, "testuser")

    prompt_repo = PromptRepository()
    with pytest.raises(DatabaseError, match="Failed to fetch active prompt"):
        await prompt_repo.get_active_prompt(mock_session, "triage_classification")

@pytest.mark.asyncio
async def test_repository_constructor_dependency_injection():
    import uuid
    from src.repositories.user_repository import UserRepository
    from src.repositories.triage_repository import TriageRepository
    from src.repositories.prompt_repository import PromptRepository

    unique_uname = f"di_user_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as session:
        # Injected session via Constructor
        user_repo = UserRepository(session=session)
        assert user_repo.session == session
        user = await user_repo.create_user(unique_uname, "hashed_pwd_di", role="staff")
        await session.commit()

        fetched = await user_repo.get_by_username(unique_uname)
        assert fetched is not None
        assert fetched.username == unique_uname

        triage_repo = TriageRepository(session=session)
        assert triage_repo.session == session

        prompt_repo = PromptRepository(session=session)
        assert prompt_repo.session == session




