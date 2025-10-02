import json

from pefc.logging import clear_context, get_logger, init_logging, set_context


def test_json_logging_basic(capsys):
    """Test basic JSON logging."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info("hello world")

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "INFO"
    assert log_entry["logger"] == "test"
    assert log_entry["msg"] == "hello world"
    assert "ts" in log_entry
    assert "pid" in log_entry
    assert "thread" in log_entry


def test_json_logging_with_event_and_kv(capsys):
    """Test JSON logging with event and extra fields."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "processing data",
        extra={"event": "process.start", "kv": {"count": 42, "type": "batch"}},
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "INFO"
    assert log_entry["msg"] == "processing data"
    assert log_entry["event"] == "process.start"
    assert log_entry["kv"]["count"] == 42
    assert log_entry["kv"]["type"] == "batch"


def test_json_logging_with_context(capsys):
    """Test JSON logging with context."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    set_context(run_id="R123", step="ComputeMerkle")
    logger.info("computing merkle root")

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["msg"] == "computing merkle root"
    assert log_entry["context"]["run_id"] == "R123"
    assert log_entry["context"]["step"] == "ComputeMerkle"


def test_json_logging_exception(capsys):
    """Test JSON logging with exception info."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("boom", exc_info=True)

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["level"] == "ERROR"
    assert log_entry["msg"] == "boom"
    assert log_entry["err"]["type"] == "ValueError"
    assert log_entry["err"]["message"] == "test error"
    assert "stack" in log_entry["err"]


def test_json_logging_redaction(capsys):
    """Test that sensitive keys are redacted."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "api call",
        extra={"kv": {"api_key": "secret123", "user": "john", "password": "pass456"}},
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["kv"]["api_key"] == "***"
    assert log_entry["kv"]["password"] == "***"
    assert log_entry["kv"]["user"] == "john"  # Not redacted


def test_json_logging_context_update(capsys):
    """Test context updates."""
    from pefc.logging import clear_context

    clear_context()  # Clear any existing context

    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    set_context(run_id="R123")
    logger.info("step 1")

    from pefc.logging import update_context

    update_context(step="ComputeMerkle")
    logger.info("step 2")

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    # First log
    log1 = json.loads(lines[0])
    assert log1["context"]["run_id"] == "R123"
    assert "step" not in log1["context"]

    # Second log
    log2 = json.loads(lines[1])
    assert log2["context"]["run_id"] == "R123"
    assert log2["context"]["step"] == "ComputeMerkle"


def test_json_logging_context_clear(capsys):
    """Test context clearing."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    set_context(run_id="R123", step="ComputeMerkle")
    logger.info("with context")

    clear_context()
    logger.info("without context")

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    # First log
    log1 = json.loads(lines[0])
    assert "context" in log1

    # Second log
    log2 = json.loads(lines[1])
    assert "context" not in log2 or not log2["context"]


def test_json_logging_levels(capsys):
    """Test different log levels."""
    init_logging(level="DEBUG", json_mode=True)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    levels = [json.loads(line)["level"] for line in lines]
    assert levels == ["DEBUG", "INFO", "WARNING", "ERROR"]
