#!/usr/bin/env python3
"""
Tests simples pour PEFC CLI.
"""
from typer.testing import CliRunner

from pefc.cli import app


class TestCLIBasic:
    """Test CLI basique."""

    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_help_command(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "PEFC CLI" in result.stdout

    def test_pack_help(self):
        """Test pack help."""
        runner = CliRunner()
        result = runner.invoke(app, ["pack", "--help"])

        assert result.exit_code == 0
        assert "Pack operations" in result.stdout
