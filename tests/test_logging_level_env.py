from pefc.logging import get_logger, init_logging


def test_log_level_env_debug(capsys):
    """Test that DEBUG level shows debug messages."""
    init_logging(level="DEBUG", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" in output
    assert "INFO test — info message" in output
    assert "WARNING test — warning message" in output


def test_log_level_env_info(capsys):
    """Test that INFO level hides debug messages."""
    init_logging(level="INFO", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" not in output
    assert "INFO test — info message" in output
    assert "WARNING test — warning message" in output


def test_log_level_env_warning(capsys):
    """Test that WARNING level hides debug and info messages."""
    init_logging(level="WARNING", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" not in output
    assert "INFO test — info message" not in output
    assert "WARNING test — warning message" in output
    assert "ERROR test — error message" in output


def test_log_level_env_error(capsys):
    """Test that ERROR level only shows error and critical messages."""
    init_logging(level="ERROR", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" not in output
    assert "INFO test — info message" not in output
    assert "WARNING test — warning message" not in output
    assert "ERROR test — error message" in output
    assert "CRITICAL test — critical message" in output


def test_log_level_env_case_insensitive(capsys):
    """Test that log level is case insensitive."""
    init_logging(level="debug", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" in output
    assert "INFO test — info message" in output


def test_log_level_env_invalid_defaults_to_info(capsys):
    """Test that invalid log level defaults to INFO."""
    init_logging(level="INVALID", json_mode=False)
    logger = get_logger("test")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")

    captured = capsys.readouterr()
    output = captured.out

    assert "DEBUG test — debug message" not in output
    assert "INFO test — info message" in output
    assert "WARNING test — warning message" in output
