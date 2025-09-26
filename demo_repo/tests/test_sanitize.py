"""
Tests pour le module de sanitisation.
"""

import pytest
from src.sanitize import sanitize_input, validate_email, clean_html, escape_sql


class TestSanitizeInput:
    """Tests pour la fonction sanitize_input."""
    
    def test_sanitize_normal_input(self):
        """Test avec une entrée normale."""
        result = sanitize_input("hello world")
        assert result == "hello\\ world"
    
    def test_sanitize_special_characters(self):
        """Test avec des caractères spéciaux."""
        result = sanitize_input("test@example.com")
        assert result == "test\\@example\\.com"
    
    def test_sanitize_empty_input(self):
        """Test avec une entrée vide."""
        result = sanitize_input("")
        assert result == ""
    
    def test_sanitize_long_input(self):
        """Test avec une entrée très longue."""
        long_input = "a" * 2000
        result = sanitize_input(long_input)
        assert len(result) <= 1000
    
    def test_sanitize_sql_injection(self):
        """Test avec une tentative d'injection SQL."""
        malicious_input = "'; DROP TABLE users; --"
        result = sanitize_input(malicious_input)
        assert "DROP" not in result
        assert "TABLE" not in result


class TestValidateEmail:
    """Tests pour la fonction validate_email."""
    
    def test_valid_email(self):
        """Test avec un email valide."""
        assert validate_email("test@example.com") == True
        assert validate_email("user.name@domain.co.uk") == True
    
    def test_invalid_email(self):
        """Test avec des emails invalides."""
        assert validate_email("invalid-email") == False
        assert validate_email("@domain.com") == False
        assert validate_email("user@") == False
        assert validate_email("") == False


class TestCleanHtml:
    """Tests pour la fonction clean_html."""
    
    def test_clean_normal_html(self):
        """Test avec du HTML normal."""
        html = "<p>Hello <strong>world</strong></p>"
        result = clean_html(html)
        assert result == html
    
    def test_clean_dangerous_script(self):
        """Test avec un script dangereux."""
        html = "<p>Hello</p><script>alert('xss')</script><p>World</p>"
        result = clean_html(html)
        assert "<script>" not in result
        assert "alert" not in result
    
    def test_clean_style_tag(self):
        """Test avec une balise style."""
        html = "<p>Hello</p><style>body { color: red; }</style><p>World</p>"
        result = clean_html(html)
        assert "<style>" not in result


class TestEscapeSql:
    """Tests pour la fonction escape_sql."""
    
    def test_escape_single_quotes(self):
        """Test avec des guillemets simples."""
        sql = "O'Connor"
        result = escape_sql(sql)
        assert result == "O''Connor"
    
    def test_escape_semicolon(self):
        """Test avec des points-virgules."""
        sql = "SELECT * FROM users;"
        result = escape_sql(sql)
        assert ";" not in result
    
    def test_escape_comments(self):
        """Test avec des commentaires SQL."""
        sql = "SELECT * FROM users -- comment"
        result = escape_sql(sql)
        assert "--" not in result
    
    def test_escape_block_comments(self):
        """Test avec des commentaires de bloc."""
        sql = "SELECT * FROM users /* comment */"
        result = escape_sql(sql)
        assert "/*" not in result
        assert "*/" not in result


if __name__ == "__main__":
    pytest.main([__file__])
