"""Adaptive rate clamp logic.

The clamp controls the percentage of the provider budget that may be used.
It adjusts in 10%% steps between 50%% and 100%% with a 60 second cooldown
between adjustments. Failures have twice the weight of successes (2x
hysteresis) meaning it takes two successful adjustments to offset one
failure.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict

MIN_CLAMP = 0.5
MAX_CLAMP = 1.0
STEP = 0.1
COOLDOWN = 60
HYSTERESIS = 2  # two successes required to offset one failure


@dataclass
class State:
    clamp: float
    last_adjust: float
    counter: int


class AdaptiveClamp:
    """Adaptive clamp manager per provider."""

    def __init__(self, *, time_func: Callable[[], float] | None = None) -> None:
        self.time = time_func or time.time
        self.states: Dict[str, State] = {}

    # Security: No external input is trusted; provider names are assumed internal.
    def adjust(self, provider: str, success: bool) -> float:
        """Adjust clamp for a provider based on success/failure outcome.

        Parameters
        ----------
        provider:
            Provider name.
        success:
            ``True`` if the last call succeeded, ``False`` for failures.

        Returns
        -------
        float
            The new clamp value for the provider.
        """

        now = self.time()
        state = self.states.get(provider)
        if state is None:
            state = State(clamp=MAX_CLAMP, last_adjust=now - COOLDOWN, counter=0)
            self.states[provider] = state

        state.counter += 1 if success else -2

        if now - state.last_adjust < COOLDOWN:
            return state.clamp

        if state.counter <= -HYSTERESIS:
            state.clamp = max(MIN_CLAMP, state.clamp - STEP)
            state.counter = 0
            state.last_adjust = now
        elif state.counter >= HYSTERESIS:
            state.clamp = min(MAX_CLAMP, state.clamp + STEP)
            state.counter = 0
            state.last_adjust = now

        return state.clamp
