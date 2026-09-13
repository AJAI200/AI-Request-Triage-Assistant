import os
import sys
import traceback
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import AsyncSessionLocal
from src.models.error_log import ErrorLog

logger = logging.getLogger("triage_assistant.error_logger")

async def log_error_to_db(
    exc: Exception,
    session: Optional[AsyncSession] = None,
    process_time_ms: Optional[float] = None
) -> Optional[ErrorLog]:
    """
    Extracts frame details (file name, function name, line number, stack trace)
    from an exception, logs it via standard logger, and persists an ErrorLog entry to the database.
    """
    logger.debug("Entering log_error_to_db")
    exc_type, exc_value, exc_tb = sys.exc_info()
    
    file_name = "unknown_file"
    function_name = "unknown_function"
    line_number = 0
    stack_trace_text = ""

    if exc_tb is not None:
        tb_frame = traceback.extract_tb(exc_tb)[-1]
        file_name = os.path.basename(tb_frame.filename)
        function_name = tb_frame.name
        line_number = tb_frame.lineno
        stack_trace_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    else:
        file_name = exc.__class__.__module__
        function_name = exc.__class__.__name__
        stack_trace_text = str(exc)

    error_msg = str(exc) or exc.__class__.__name__

    # Standard Python logging
    logger.error(
        f"[{file_name}::{function_name}:L{line_number}] {error_msg}\n{stack_trace_text}"
    )

    # Database Persistence
    own_session = session is None
    db_session = session or AsyncSessionLocal()

    try:
        error_entry = ErrorLog(
            file_name=file_name,
            function_name=function_name,
            line_number=line_number,
            error_message=error_msg,
            stack_trace=stack_trace_text,
            process_time_ms=process_time_ms
        )
        db_session.add(error_entry)
        await db_session.commit()
        await db_session.refresh(error_entry)
        logger.debug("Exiting log_error_to_db successfully")
        return error_entry
    except Exception as db_exc:
        logger.critical(f"Failed to persist ErrorLog to database: {db_exc}")
        logger.debug("Exiting log_error_to_db on DB error")
        return None
    finally:
        if own_session:
            await db_session.close()
