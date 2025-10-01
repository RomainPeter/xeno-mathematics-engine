import importlib


def test_import():
    assert importlib.import_module("xme")


def test_smoke():
    assert True