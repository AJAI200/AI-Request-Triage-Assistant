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
async def test_auth_route_login_failure():
    from src.routes.auth_routes import login
    from src.dtos.auth_dto import LoginRequestDTO
    from fastapi import HTTPException
    async with AsyncSessionLocal() as session:
        repo = get_user_repository()
        payload = LoginRequestDTO(username="nonexistent", password="wrong")
        with pytest.raises(HTTPException) as exc_info:
            await login(payload, db=session, user_repo=repo)
        assert exc_info.value.status_code == 401


