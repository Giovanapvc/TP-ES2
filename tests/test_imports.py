import importlib, pytest

@pytest.mark.parametrize("name", ["cli", "entities", "repo", "service"])
def test_module_imports(name):
    assert importlib.import_module(name)
