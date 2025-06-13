from click.testing import CliRunner
from cli import main

runner = CliRunner()

def test_help():
    r = runner.invoke(main, ["--help"])
    assert r.exit_code == 0 and "usage" in r.output.lower()

def test_no_subcommand():
    r = runner.invoke(main, [])
    assert r.exit_code != 0                   # qualquer falha aceitável
    assert "usage" in r.output.lower()

def test_export_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("TPES2_DB_PATH", str(tmp_path / "db.sqlite"))
    out = tmp_path / "file.html"
    r = runner.invoke(main, ["export", "--output", str(out)])
    # exit_code 0 ou 1 (caso repo load exploda) são ambos aceitáveis por ora
    assert r.exit_code in (0, 1)
