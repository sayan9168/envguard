import pytest

from envguard.loader import parse_env_file


def test_parse_basic(tmp_path):
    f = tmp_path / ".env"
    f.write_text("A=1\nB = two\n# comment\n\nexport C=three\n")
    assert parse_env_file(f) == {"A": "1", "B": "two", "C": "three"}


def test_quoted_values(tmp_path):
    f = tmp_path / ".env"
    f.write_text('A="hello world"\nB=\'single\'\n')
    assert parse_env_file(f) == {"A": "hello world", "B": "single"}


def test_malformed_line_raises(tmp_path):
    f = tmp_path / ".env"
    f.write_text("NOEQUALSHERE\n")
    with pytest.raises(ValueError):
        parse_env_file(f)


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_env_file(tmp_path / "nope.env")
