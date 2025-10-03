import json

from pefc.logging import get_logger, init_logging


def test_exception_logging_json(capsys):
    """Test exception logging in JSON mode."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    try:
        raise ValueError("test error message")
    except ValueError:
        logger.exception("boom", exc_info=True)

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "ERROR"
    assert log_entry["msg"] == "boom"
    assert log_entry["err"]["type"] == "ValueError"
    assert log_entry["err"]["message"] == "test error message"
    assert "stack" in log_entry["err"]
    assert "ValueError: test error message" in log_entry["err"]["stack"]


def test_exception_logging_text(capsys):
    """Test exception logging in text mode."""
    init_logging(level="INFO", json_mode=False)
    logger = get_logger("test")

    try:
        raise ValueError("test error message")
    except ValueError:
        logger.exception("boom")

    captured = capsys.readouterr()
    output = captured.out

    assert "ERROR test — boom" in output
    assert "ValueError: test error message" in output


def test_exception_logging_with_context(capsys):
    """Test exception logging with context."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    from pefc.logging import set_context

    set_context(run_id="R123", step="ComputeMerkle")

    try:
        raise RuntimeError("runtime error")
    except RuntimeError:
        logger.exception("failed", exc_info=True)

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "ERROR"
    assert log_entry["msg"] == "failed"
    assert log_entry["err"]["type"] == "RuntimeError"
    assert log_entry["err"]["message"] == "runtime error"
    assert log_entry["context"]["run_id"] == "R123"
    assert log_entry["context"]["step"] == "ComputeMerkle"


def test_exception_logging_nested(capsys):
    """Test exception logging with nested exceptions."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    try:
        try:
            raise ValueError("inner error")
        except ValueError as e:
            raise RuntimeError("outer error") from e
    except RuntimeError:
        logger.exception("nested error", exc_info=True)

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "ERROR"
    assert log_entry["err"]["type"] == "RuntimeError"
    assert log_entry["err"]["message"] == "outer error"
    assert "ValueError: inner error" in log_entry["err"]["stack"]


def test_exception_logging_no_exc_info(capsys):
    """Test exception logging without exc_info."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    try:
        raise ValueError("test error")
    except ValueError:
        logger.error("boom")  # No exc_info=True

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "ERROR"
    assert log_entry["msg"] == "boom"
    assert "err" not in log_entry
