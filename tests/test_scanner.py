from envguard.scanner import scan_tree


def test_detects_aws_key(tmp_path):
    (tmp_path / "leak.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n')
    findings = scan_tree(tmp_path)
    assert any(f.pattern == "aws_access_key" for f in findings)


def test_detects_private_key(tmp_path):
    (tmp_path / "id.pem").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIB...\n")
    findings = scan_tree(tmp_path)
    assert any(f.pattern == "private_key" for f in findings)


def test_clean_tree(tmp_path):
    (tmp_path / "ok.py").write_text("x = 1\n")
    assert scan_tree(tmp_path) == []


def test_ignores_venv(tmp_path):
    d = tmp_path / ".venv"
    d.mkdir()
    (d / "leak.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n')
    assert scan_tree(tmp_path) == []
