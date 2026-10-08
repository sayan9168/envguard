from envguard import Field, Schema, ValidationError

import pytest


@pytest.fixture()
def schema() -> Schema:
    return Schema({
        "PORT": Field.int(default=8000, min_value=1, max_value=65535),
        "DEBUG": Field.bool(default=False),
        "LOG_LEVEL": Field.enum(["DEBUG", "INFO", "ERROR"], default="INFO"),
        "API_KEY": Field.str(required=True, secret=True),
        "TAGS": Field.list_of("str", default=[]),
    })


def test_defaults_apply(schema):
    cfg = schema.load(env={}, overrides={"API_KEY": "x"})
    assert cfg.PORT == 8000
    assert cfg.DEBUG is False
    assert cfg.LOG_LEVEL == "INFO"


def test_type_coercion(schema):
    cfg = schema.load(env={"PORT": "9000", "DEBUG": "yes", "TAGS": "a, b ,c"},
                      overrides={"API_KEY": "x"})
    assert cfg.PORT == 9000
    assert cfg.DEBUG is True
    assert cfg.TAGS == ["a", "b", "c"]


def test_missing_required_raises(schema):
    with pytest.raises(ValidationError) as exc:
        schema.load(env={})
    assert any(v.name == "API_KEY" for v in exc.value.violations)


def test_invalid_enum_raises(schema):
    with pytest.raises(ValidationError):
        schema.load(env={"LOG_LEVEL": "VERBOSE"}, overrides={"API_KEY": "x"})


def test_int_bounds(schema):
    with pytest.raises(ValidationError):
        schema.load(env={"PORT": "99999"}, overrides={"API_KEY": "x"})


def test_secret_redaction(schema):
    cfg = schema.load(env={}, overrides={"API_KEY": "supersecret"})
    assert cfg.as_dict()["API_KEY"] == "****"
    assert cfg.as_dict(redact_secrets=False)["API_KEY"] == "supersecret"
    assert "supersecret" not in repr(cfg)


def test_config_immutable(schema):
    cfg = schema.load(env={}, overrides={"API_KEY": "x"})
    with pytest.raises(AttributeError):
        cfg.PORT = 1


def test_env_precedence_over_file(tmp_path, schema):
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=1111\nAPI_KEY=fromfile\n")
    cfg = schema.load(env={"PORT": "2222"}, env_file=str(env_file))
    assert cfg.PORT == 2222
    assert cfg.API_KEY == "fromfile"
