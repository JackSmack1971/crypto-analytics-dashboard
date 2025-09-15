
from redis.exceptions import RedisError

from app.rate_limiting import AdaptiveClamp, acquire, adjust_clamp, init


def _time_controller(start: float = 0.0):
    current = {"value": start}

    def now() -> float:
        return current["value"]

    def advance(seconds: float) -> None:
        current["value"] += seconds

    return now, advance


def test_token_bucket_acquire(fake_redis):
    now, advance = _time_controller()
    init(fake_redis, capacity=1, refill_rate=1, time_func=now)
    assert acquire("cg", "/foo")
    assert not acquire("cg", "/foo")
    advance(1)
    assert acquire("cg", "/foo")


def test_redis_failure_fallback():
    class FailingRedis:
        def get(self, key):  # pragma: no cover - trivial
            raise RedisError("boom")

        def set(self, *args, **kwargs):  # pragma: no cover - trivial
            raise RedisError("boom")

    now, advance = _time_controller()
    init(FailingRedis(), capacity=1, refill_rate=1, time_func=now)
    assert acquire("cg", "/bar")
    assert not acquire("cg", "/bar")
    advance(1)
    assert acquire("cg", "/bar")


def test_clamp_hysteresis(monkeypatch):
    now, advance = _time_controller()
    clamp = AdaptiveClamp(time_func=now)
    monkeypatch.setattr("app.rate_limiting._clamp", clamp)

    assert adjust_clamp("cg", success=False) == 0.9
    assert adjust_clamp("cg", success=True) == 0.9
    advance(60)
    assert adjust_clamp("cg", success=True) == 1.0
