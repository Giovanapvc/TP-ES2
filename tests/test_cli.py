import pytest
from click.testing import CliRunner
from cli import main  

@pytest.fixture
def runner():
    return CliRunner()

def test_cli__help_shows_usage(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_cli__missing_args_errors(runner):
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "error:" in result.output.lower()

def test_cli__export_html_creates_file(tmp_path, runner):
    out = tmp_path / "out.html"
    result = runner.invoke(main, ["export", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
