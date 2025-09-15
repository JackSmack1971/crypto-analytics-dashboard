import httpx
import pytest

from app.main import app, rate_limiter
from app.rate_limiting import CircuitBreaker, CircuitState, register_breaker

pytestmark = pytest.mark.unit


class Resp:
    status_code = 403


class ForbiddenError(Exception):
    def __init__(self) -> None:
        self.response = Resp()


@pytest.mark.asyncio
async def test_operator_reset_endpoint():
    breaker = CircuitBreaker(failure_threshold=1, probe_interval=1)
    register_breaker("testprov", breaker)

    async def forbidden():
        raise ForbiddenError()

    with pytest.raises(ForbiddenError):
        await breaker.call(forbidden, trace_id="tid")
    assert breaker.state is CircuitState.OPEN

    app.dependency_overrides[rate_limiter] = lambda request: None
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post(
            "/operator/breaker/testprov/reset",
            headers={"Authorization": "Bearer operator", "X-Trace-Id": "tid"},
        )
    app.dependency_overrides.clear()

    assert res.status_code == 200
    assert breaker.state is CircuitState.CLOSED


@pytest.mark.asyncio
async def test_operator_reset_auth_required():
    breaker = CircuitBreaker(failure_threshold=1, probe_interval=1)
    register_breaker("unauth", breaker)

    app.dependency_overrides[rate_limiter] = lambda request: None
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/operator/breaker/unauth/reset")
    app.dependency_overrides.clear()

    assert res.status_code == 401
