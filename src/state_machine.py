from dataclasses import dataclass


@dataclass
class TriggerStateMachine:
    death_confirm_frames: int
    alive_confirm_frames: int
    action_cooldown_ms: int
    state: str = "alive"
    _death_streak: int = 0
    _alive_streak: int = 0
    _last_trigger_ms: int | None = None

    def update(self, is_death_detected: bool, now_ms: int) -> bool:
        if is_death_detected:
            self._death_streak += 1
            self._alive_streak = 0
        else:
            self._alive_streak += 1
            self._death_streak = 0

        if self.state == "alive" and self._death_streak >= self.death_confirm_frames:
            self.state = "dead"
            if self._last_trigger_ms is None or now_ms - self._last_trigger_ms >= self.action_cooldown_ms:
                self._last_trigger_ms = now_ms
                return True
            return False

        if self.state == "dead" and self._alive_streak >= self.alive_confirm_frames:
            self.state = "alive"

        return False
