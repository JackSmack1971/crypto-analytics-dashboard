import pytest
from app.config_env import Settings, load

pytestmark = pytest.mark.unit


def test_load_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defaults apply when optional vars unset."""
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    cfg = load()

    assert cfg == Settings(
        api_host="127.0.0.1",
        api_port=8000,
        redis_url="redis://127.0.0.1:6379/0",
        debug=False,
    )


def test_load_env_casts_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment values are cast to declared types."""
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/1")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("DEBUG", "1")

    cfg = load()

    assert cfg.api_host == "127.0.0.1"  # default unaffected
    assert cfg.api_port == 9000
    assert cfg.debug is True


def test_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Required variables raise RuntimeError when absent."""
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(RuntimeError):
        load()
