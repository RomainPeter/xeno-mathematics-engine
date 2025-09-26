import pytest
from src.utils import sanitize_input, add

def test_sanitize_input_basic():
    assert sanitize_input("  hi  there  ") == "hi there"

def test_sanitize_input_none():
    assert sanitize_input(None) == ""

def test_add():
    assert add(2, 3) == 5
