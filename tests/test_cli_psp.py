from typer.testing import CliRunner

from xme.cli.main import app


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "XME — Xeno-Math Engine CLI" in result.output


def test_psp_validate_help():
    """Test PSP validate command help."""
    runner = CliRunner()
    result = runner.invoke(app, ["psp", "--help"])
    assert result.exit_code == 0
    assert "PSP commands" in result.output


def test_pcap_log_help():
    """Test PCAP log command help."""
    runner = CliRunner()
    result = runner.invoke(app, ["pcap", "--help"])
    assert result.exit_code == 0
    assert "PCAP journal" in result.output


def test_engine_help():
    """Test Engine commands help."""
    runner = CliRunner()
    result = runner.invoke(app, ["engine", "--help"])
    assert result.exit_code == 0
    assert "Engine ops" in result.output


def test_psp_validate_example():
    """Test PSP validate with example file."""
    runner = CliRunner()

    # Test with mock_yoneda.json if it exists
    yoneda_path = "examples/psp/mock_yoneda.json"
    result = runner.invoke(app, ["psp", "validate", yoneda_path])

    if result.exit_code == 0:
        assert "PSP valid" in result.output
        assert "Yoneda Lemma" in result.output
    else:
        # If file doesn't exist, that's expected in some test environments
        assert "No such file" in result.output or "FileNotFoundError" in result.output


def test_pcap_log_command():
    """Test PCAP log command."""
    runner = CliRunner()
    result = runner.invoke(app, ["pcap", "log", "test_action", "--actor", "test_actor"])

    assert result.exit_code == 0
    assert "Logged" in result.output
    assert "run_id=" in result.output


def test_pcap_log_with_psp_ref():
    """Test PCAP log with PSP reference."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["pcap", "log", "test_action", "--actor", "test_actor", "--psp-ref", "psp_123"]
    )

    assert result.exit_code == 0
    assert "Logged" in result.output


def test_engine_verify_2cat_missing_script():
    """Test engine verify-2cat with missing script."""
    runner = CliRunner()
    result = runner.invoke(app, ["engine", "verify-2cat"])

    # Should fail because script doesn't exist
    assert result.exit_code == 2
    assert "Missing scripts/verify_2cat_pack.sh" in result.output
