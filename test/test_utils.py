import pytest
from sqlalchemy import select
from src.utils.validators import validate_classification, ValidationError
from src.utils.json_parser import parse_llm_json, JSONParseError
from src.utils.lookups import lookup_category_id, lookup_owner_id
from src.utils.error_logger import log_error_to_db
from src.models.error_log import ErrorLog
from src.database import init_db
from src.models.base import AsyncSessionLocal

@pytest.mark.asyncio
async def test_log_error_to_db():
    await init_db()
    async with AsyncSessionLocal() as session:
        try:
            raise ValueError("Test error for DB logging")
        except Exception as exc:
            entry = await log_error_to_db(exc, session=session, process_time_ms=123.4)
            assert entry is not None
            assert entry.id is not None
            assert entry.error_message == "Test error for DB logging"
            assert entry.process_time_ms == 123.4
            assert "test_utils.py" in entry.file_name
            assert "test_log_error_to_db" in entry.function_name
            assert entry.line_number > 0
            assert "ValueError: Test error for DB logging" in entry.stack_trace

@pytest.mark.asyncio
async def test_log_error_to_db_no_traceback_and_db_failure():
    from unittest.mock import patch, AsyncMock
    # Test when sys.exc_info() returns (None, None, None)
    err = RuntimeError("No traceback error")
    with patch("sys.exc_info", return_value=(None, None, None)):
        entry = await log_error_to_db(err)
        assert entry is not None
        assert entry.function_name == "RuntimeError"

    # Test DB failure inside log_error_to_db
    mock_session = AsyncMock()
    mock_session.commit.side_effect = RuntimeError("DB Commit Failure")
    result = await log_error_to_db(err, session=mock_session)
    assert result is None

@pytest.mark.asyncio
async def test_validators_exceptions():
    # Test non-dict input
    with pytest.raises(ValidationError, match="not a dictionary"):
        validate_classification("invalid_input")

    # Test invalid category
    with pytest.raises(ValidationError, match="Invalid category"):
        validate_classification({
            "category": "InvalidCategory",
            "priority": "Low",
            "owner": "Engineering",
            "summary": "Summary",
            "priority_reason": "Reason"
        })

    # Test invalid priority
    with pytest.raises(ValidationError, match="Invalid priority"):
        validate_classification({
            "category": "Sales",
            "priority": "ExtremeUrgent",
            "owner": "Engineering",
            "summary": "Summary",
            "priority_reason": "Reason"
        })

    # Test invalid owner
    with pytest.raises(ValidationError, match="Invalid owner"):
        validate_classification({
            "category": "Sales",
            "priority": "Low",
            "owner": "UnknownOwner",
            "summary": "Summary",
            "priority_reason": "Reason"
        })

    # Test missing summary
    with pytest.raises(ValidationError, match="Missing or invalid summary"):
        validate_classification({
            "category": "Sales",
            "priority": "Low",
            "owner": "Engineering",
            "summary": "",
            "priority_reason": "Reason"
        })

    # Test missing priority_reason
    with pytest.raises(ValidationError, match="Missing or invalid priority_reason"):
        validate_classification({
            "category": "Sales",
            "priority": "Low",
            "owner": "Engineering",
            "summary": "Summary",
            "priority_reason": ""
        })

def test_json_parser_edge_cases():
    # Empty or non-string input
    with pytest.raises(JSONParseError, match="Empty or invalid"):
        parse_llm_json(None)

    # Valid JSON string without markdown fence
    parsed = parse_llm_json('{"key": "value"}')
    assert parsed == {"key": "value"}

    # Plain text non-JSON input
    with pytest.raises(JSONParseError, match="Failed to parse JSON"):
        parse_llm_json("This is plain text with no brackets")

    # Non-dict JSON (e.g. JSON array)
    with pytest.raises(JSONParseError, match="Parsed JSON is not an object"):
        parse_llm_json('[1, 2, 3]')

@pytest.mark.asyncio
async def test_lookups_fallbacks():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Unknown category falls back to "Other"
        cat_id = await lookup_category_id(session, "NonExistentCategory")
        assert isinstance(cat_id, int)

        # Unknown owner falls back to "Client Success"
        own_id = await lookup_owner_id(session, "NonExistentOwner")
        assert isinstance(own_id, int)
