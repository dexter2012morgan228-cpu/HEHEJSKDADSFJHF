from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class SessionStats:
    started_at: float = field(default_factory=time.time)
    submitted: int = 0
    accepted: int = 0
    declined: int = 0
    withdrawn: int = 0
    blocked_blacklist: int = 0
    blocked_age: int = 0
    blocked_cooldown: int = 0


@dataclass
class State:
    cooldowns: Dict[int, float] = field(default_factory=dict)
    pending_applicants: Set[int] = field(default_factory=set)
    pending_applicant_msg: Dict[int, int] = field(default_factory=dict)
    stats: SessionStats = field(default_factory=SessionStats)

    def get_cooldown(self, user_id: int) -> Optional[float]:
        ts = self.cooldowns.get(user_id)
        if ts and ts > time.time():
            return ts
        if ts:
            self.cooldowns.pop(user_id, None)
        return None

    def set_cooldown(self, user_id: int, hours: float) -> None:
        self.cooldowns[user_id] = time.time() + max(hours, 0) * 3600

    def clear_cooldown(self, user_id: int) -> None:
        self.cooldowns.pop(user_id, None)

    def mark_pending(self, user_id: int, applicant_dm_msg_id: int | None = None) -> None:
        self.pending_applicants.add(user_id)
        if applicant_dm_msg_id is not None:
            self.pending_applicant_msg[user_id] = applicant_dm_msg_id

    def clear_pending(self, user_id: int) -> None:
        self.pending_applicants.discard(user_id)
        self.pending_applicant_msg.pop(user_id, None)
