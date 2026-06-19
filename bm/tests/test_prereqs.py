"""Tests for bm.prereqs module."""

from unittest.mock import patch

from bm.prereqs import PREREQS, Prereq, _get_package_manager_prereq, check_prereqs

# -- Prereq.is_installed() --


def test_is_installed_true() -> None:
    p = Prereq(name="Git", check_cmd="git", required=True)
    with patch("bm.prereqs.shutil.which", return_value="/usr/bin/git"):
        assert p.is_installed() is True


def test_is_installed_false() -> None:
    p = Prereq(name="Git", check_cmd="git", required=True)
    with patch("bm.prereqs.shutil.which", return_value=None):
        assert p.is_installed() is False


# -- Prereq.get_install_command() --


def test_get_install_command_darwin() -> None:
    p = Prereq(
        name="uv",
        check_cmd="uv",
        install_commands={
            "darwin": "brew install uv",
            "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        },
    )
    with patch("bm.prereqs.sys") as mock_sys:
        mock_sys.platform = "darwin"
        assert p.get_install_command() == "brew install uv"


def test_get_install_command_linux() -> None:
    p = Prereq(
        name="uv",
        check_cmd="uv",
        install_commands={
            "darwin": "brew install uv",
            "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        },
    )
    with patch("bm.prereqs.sys") as mock_sys:
        mock_sys.platform = "linux"
        assert p.get_install_command() == "curl -LsSf https://astral.sh/uv/install.sh | sh"


def test_get_install_command_unknown_platform() -> None:
    p = Prereq(
        name="uv",
        check_cmd="uv",
        install_commands={"darwin": "brew install uv"},
    )
    with patch("bm.prereqs.sys") as mock_sys:
        mock_sys.platform = "freebsd"
        assert p.get_install_command() is None


# -- check_prereqs() --


def test_check_prereqs_returns_list_of_tuples() -> None:
    result = check_prereqs()
    assert isinstance(result, list)
    assert len(result) == len(PREREQS)
    for prereq, installed in result:
        assert isinstance(prereq, Prereq)
        assert isinstance(installed, bool)


def test_check_prereqs_reflects_which() -> None:
    with patch("bm.prereqs.shutil.which", return_value=None):
        result = check_prereqs()
        for _prereq, installed in result:
            assert installed is False


def test_check_prereqs_all_installed() -> None:
    with patch("bm.prereqs.shutil.which", return_value="/usr/bin/something"):
        result = check_prereqs()
        for _prereq, installed in result:
            assert installed is True


# -- _get_package_manager_prereq() --


def test_package_manager_darwin() -> None:
    with patch("bm.prereqs.sys") as mock_sys:
        mock_sys.platform = "darwin"
        p = _get_package_manager_prereq()
        assert p.name == "Homebrew"
        assert p.check_cmd == "brew"
        assert "darwin" in p.install_commands
        assert p.required is False


def test_package_manager_linux() -> None:
    with patch("bm.prereqs.sys") as mock_sys:
        mock_sys.platform = "linux"
        p = _get_package_manager_prereq()
        assert p.name == "apt-get"
        assert p.check_cmd == "apt-get"
        assert p.required is False


def test_package_manager_win32() -> None:
    with patch("bm.prereqs.sys") as mock_sys:
        mock_sys.platform = "win32"
        p = _get_package_manager_prereq()
        assert p.name == "winget"
        assert p.check_cmd == "winget"
        assert p.required is False


# -- PREREQS list structure --


def test_prereqs_list_has_expected_names() -> None:
    names = {p.name for p in PREREQS}
    assert "Python 3.11+" in names
    assert "uv" in names
    assert "Claude Code CLI" in names
    assert "Git" in names


def test_prereqs_required_flags() -> None:
    by_name = {p.name: p for p in PREREQS}
    assert by_name["Python 3.11+"].required is True
    assert by_name["Git"].required is True
    assert by_name["uv"].required is False
    assert by_name["Claude Code CLI"].required is False
