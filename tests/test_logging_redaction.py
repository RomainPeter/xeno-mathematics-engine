import json
from pefc.logging import init_logging, get_logger


def test_redaction_sensitive_keys(capsys):
    """Test that sensitive keys are redacted."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "api call",
        extra={
            "kv": {
                "api_key": "secret123",
                "password": "mypassword",
                "token": "bearer_token",
                "authorization": "Basic auth",
                "user": "john",
                "count": 42,
            }
        },
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["kv"]["api_key"] == "***"
    assert log_entry["kv"]["password"] == "***"
    assert log_entry["kv"]["token"] == "***"
    assert log_entry["kv"]["authorization"] == "***"
    assert log_entry["kv"]["user"] == "john"  # Not redacted
    assert log_entry["kv"]["count"] == 42  # Not redacted


def test_redaction_case_insensitive(capsys):
    """Test that redaction is case insensitive."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "api call",
        extra={
            "kv": {
                "API_KEY": "secret123",
                "Password": "mypassword",
                "TOKEN": "bearer_token",
                "Authorization": "Basic auth",
            }
        },
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["kv"]["API_KEY"] == "***"
    assert log_entry["kv"]["Password"] == "***"
    assert log_entry["kv"]["TOKEN"] == "***"
    assert log_entry["kv"]["Authorization"] == "***"


def test_redaction_nested_dict(capsys):
    """Test redaction in nested dictionaries."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "api call",
        extra={
            "kv": {
                "config": {"api_key": "secret123", "user": "john"},
                "auth": {"password": "mypassword", "token": "bearer_token"},
                "count": 42,
            }
        },
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["kv"]["config"]["api_key"] == "***"
    assert log_entry["kv"]["config"]["user"] == "john"
    # Check that auth dict was properly redacted
    auth_dict = log_entry["kv"]["auth"]
    assert auth_dict["password"] == "***"
    assert auth_dict["token"] == "***"
    assert log_entry["kv"]["count"] == 42


def test_redaction_partial_matches(capsys):
    """Test redaction with partial key matches."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "api call",
        extra={
            "kv": {
                "my_api_key": "secret123",
                "user_password": "mypassword",
                "bearer_token": "token123",
                "auth_credential": "cred123",
                "private_key": "key123",
                "sensitive_data": "data123",
            }
        },
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["kv"]["my_api_key"] == "***"
    assert log_entry["kv"]["user_password"] == "***"
    assert log_entry["kv"]["bearer_token"] == "***"
    assert log_entry["kv"]["auth_credential"] == "***"
    assert log_entry["kv"]["private_key"] == "***"
    assert log_entry["kv"]["sensitive_data"] == "***"


def test_redaction_no_sensitive_keys(capsys):
    """Test that non-sensitive keys are not redacted."""
    init_logging(level="INFO", json_mode=True)
    logger = get_logger("test")

    logger.info(
        "api call",
        extra={
            "kv": {
                "user": "john",
                "count": 42,
                "status": "success",
                "duration": 1.5,
                "enabled": True,
            }
        },
    )

    captured = capsys.readouterr()
    log_entry = json.loads(captured.out.strip())

    assert log_entry["kv"]["user"] == "john"
    assert log_entry["kv"]["count"] == 42
    assert log_entry["kv"]["status"] == "success"
    assert log_entry["kv"]["duration"] == 1.5
    assert log_entry["kv"]["enabled"] is True
