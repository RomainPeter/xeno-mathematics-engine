"""
Cas de démonstration: Sanitisation des entrées utilisateur.
Objectif: Implémenter une fonction de sanitisation sécurisée.
"""

def sanitize_input(user_input: str) -> str:
    """
    Sanitise l'entrée utilisateur pour éviter les injections.
    
    Args:
        user_input: L'entrée utilisateur à sanitiser
        
    Returns:
        str: L'entrée sanitisée
        
    Raises:
        ValueError: Si l'entrée est vide ou None
    """
    if not user_input:
        raise ValueError("L'entrée ne peut pas être vide")
    
    # Échapper les caractères spéciaux
    import re
    sanitized = re.escape(user_input)
    
    # Limiter la longueur
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


def test_sanitize_input():
    """Tests pour la fonction de sanitisation."""
    import pytest
    
    # Test avec entrée normale
    assert sanitize_input("hello world") == "hello\\ world"
    
    # Test avec caractères spéciaux
    assert sanitize_input("test@example.com") == "test\\@example\\.com"
    
    # Test avec entrée vide
    with pytest.raises(ValueError):
        sanitize_input("")
    
    # Test avec entrée None
    with pytest.raises(ValueError):
        sanitize_input(None)
    
    # Test avec entrée très longue
    long_input = "a" * 2000
    result = sanitize_input(long_input)
    assert len(result) <= 1000


if __name__ == "__main__":
    test_sanitize_input()
    print("✅ Tests de sanitisation réussis")
