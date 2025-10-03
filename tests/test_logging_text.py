from pefc.logging import get_logger, init_logging, set_context


def test_text_logging_basic(capsys):
    """Test basic text logging."""
    init_logging(level="INFO", json_mode=False)
    logger = get_logger("test")

    logger.info("hello world")

    captured = capsys.readouterr()
    assert "INFO test — hello world" in captured.out


def test_text_logging_with_context(capsys):
    """Test text logging with context."""
    init_logging(level="INFO", json_mode=False)
    logger = get_logger("test")

    set_context(run_id="R123", step="ComputeMerkle")
    logger.info("computing merkle root")

    captured = capsys.readouterr()
    assert "INFO test — computing merkle root [run_id=R123 step=ComputeMerkle]" in captured.out


def test_text_logging_levels(capsys):
    """Test different log levels in text mode."""
    init_logging(level="DEBUG", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" in output
    assert "INFO test — info message" in output
    assert "WARNING test — warning message" in output
    assert "ERROR test — error message" in output


def test_text_logging_exception(capsys):
    """Test text logging with exception."""
    init_logging(level="INFO", json_mode=False)
    logger = get_logger("test")

    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("boom")

    captured = capsys.readouterr()
    assert "ERROR test — boom" in captured.out
    assert "ValueError: test error" in captured.out


def test_text_logging_no_context(capsys):
    """Test text logging without context."""
    from pefc.logging import clear_context

    clear_context()  # Clear any existing context

    init_logging(level="INFO", json_mode=False)
    logger = get_logger("test")

    logger.info("simple message")

    captured = capsys.readouterr()
    assert "INFO test — simple message" in captured.out
    assert "[" not in captured.out  # No context brackets
