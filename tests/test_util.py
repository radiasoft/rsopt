import sys
from rsopt import util


def test_run_path_as_module_imports_sibling_module(tmp_path, monkeypatch):
    # Run from a different directory so the sibling is only reachable through the module's own directory
    module_directory = tmp_path / "functions"
    module_directory.mkdir()
    (module_directory / "rsopt_test_sibling.py").write_text("VALUE = 42\n")
    (module_directory / "main.py").write_text(
        "from rsopt_test_sibling import VALUE\n"
        "def f():\n"
        "    return VALUE\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delitem(sys.modules, "rsopt_test_sibling", raising=False)
    path_before = list(sys.path)

    module = util.run_path_as_module(module_directory / "main.py")

    assert module.f() == 42
    assert sys.path == path_before


def test_run_path_as_module_restores_sys_path_on_error(tmp_path):
    (tmp_path / "bad.py").write_text("raise RuntimeError('boom')\n")
    path_before = list(sys.path)

    try:
        util.run_path_as_module(tmp_path / "bad.py")
    except RuntimeError:
        pass

    assert sys.path == path_before
