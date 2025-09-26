"""
Module de sanitisation des entrées utilisateur.
Contient des fonctions pour nettoyer et valider les données d'entrée.
"""

import re
from typing import Optional


def sanitize_input(user_input: str) -> str:
    """
    Sanitise l'entrée utilisateur pour éviter les injections.
    
    Args:
        user_input: L'entrée utilisateur à sanitiser
        
    Returns:
        str: L'entrée sanitisée
    """
    if not user_input:
        return ""
    
    # Échapper les caractères spéciaux
    sanitized = re.escape(user_input)
    
    # Limiter la longueur
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


def validate_email(email: str) -> bool:
    """
    Valide une adresse email.
    
    Args:
        email: Adresse email à valider
        
    Returns:
        bool: True si l'email est valide
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def clean_html(html_content: str) -> str:
    """
    Nettoie le contenu HTML en supprimant les balises dangereuses.
    
    Args:
        html_content: Contenu HTML à nettoyer
        
    Returns:
        str: Contenu HTML nettoyé
    """
    # Supprimer les balises script et style
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed']
    
    for tag in dangerous_tags:
        pattern = f'<{tag}[^>]*>.*?</{tag}>'
        html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    return html_content


def escape_sql(sql_string: str) -> str:
    """
    Échappe une chaîne pour l'utilisation dans SQL.
    
    Args:
        sql_string: Chaîne à échapper
        
    Returns:
        str: Chaîne échappée
    """
    # Échapper les caractères dangereux
    sql_string = sql_string.replace("'", "''")
    sql_string = sql_string.replace(";", "")
    sql_string = sql_string.replace("--", "")
    sql_string = sql_string.replace("/*", "")
    sql_string = sql_string.replace("*/", "")
    
    return sql_string
