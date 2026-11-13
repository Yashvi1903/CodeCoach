import re
import time
from dataclasses import dataclass
import requests


@dataclass
class GuardDecision:
    allowed: bool
    reason: str
    contest_id: int | None = None
    phase: str | None = None


# Simple in-memory cache (we will persist this to SQLite in Phase 7)
_PHASE_CACHE: dict[int, tuple[str, float]] = {}
_LAST_API_CALL: float = 0.0
CACHE_TTL_SECONDS = 300  # 5 minutes


def extract_contest_id(url: str) -> tuple[str, int | None]:
    """
    Returns (url_type, contest_id).
    Supported URL formats:
      - https://codeforces.com/problemset/problem/1950/A -> ("problemset", 1950)
      - https://codeforces.com/contest/1950/problem/A    -> ("contest", 1950)
      - https://codeforces.com/gym/104120/problem/A      -> ("gym", 104120)
    """
    clean_url = url.strip().lower()
    if "codeforces.com" not in clean_url:
        return ("unknown", None)

    if "/gym/" in clean_url:
        m = re.search(r"/gym/(\d+)", clean_url)
        return ("gym", int(m.group(1)) if m else None)

    if "/problemset/problem/" in clean_url:
        m = re.search(r"/problemset/problem/(\d+)", clean_url)
        return ("problemset", int(m.group(1)) if m else None)

    if "/contest/" in clean_url:
        m = re.search(r"/contest/(\d+)", clean_url)
        return ("contest", int(m.group(1)) if m else None)

    return ("unknown", None)


def fetch_contest_phase(contest_id: int) -> str | None:
    """
    Queries Codeforces public API politely (max 1 call per 2 seconds) with caching.
    Returns phase string (e.g. 'FINISHED', 'CODING', 'BEFORE') or None on error.
    """
    global _LAST_API_CALL
    now = time.time()

    if contest_id in _PHASE_CACHE:
        cached_phase, ts = _PHASE_CACHE[contest_id]
        if now - ts < CACHE_TTL_SECONDS:
            return cached_phase

    # Polite rate limit: 1 request per 2 seconds per plan rules
    elapsed = now - _LAST_API_CALL
    if elapsed < 2.0:
        time.sleep(2.0 - elapsed)

    try:
        _LAST_API_CALL = time.time()
        resp = requests.get(
            "https://codeforces.com/api/contest.standings",
            params={"contestId": contest_id, "from": 1, "count": 1},
            timeout=5.0,
        )
        data = resp.json()
        if data.get("status") == "OK":
            phase = data["result"]["contest"]["phase"]
            _PHASE_CACHE[contest_id] = (phase, time.time())
            return phase
    except Exception:
        return None

    return None


def check_contest_guard(url: str, phase_override: str | None = None) -> GuardDecision:
    """
    Fail-closed contest guard:
      - problemset URLs -> allowed
      - contest URLs with phase == 'FINISHED' -> allowed
      - everything else (CODING, BEFORE, SYSTEM_TEST, gym, API error) -> blocked
    """
    url_type, contest_id = extract_contest_id(url)

    if url_type == "problemset" and contest_id is not None:
        return GuardDecision(
            allowed=True,
            reason="Practice problemset URL allowed.",
            contest_id=contest_id,
            phase="FINISHED",
        )

    if url_type == "gym":
        return GuardDecision(
            allowed=False,
            reason="Gym contests are blocked (fail-closed policy).",
            contest_id=contest_id,
        )

    if url_type != "contest" or contest_id is None:
        return GuardDecision(
            allowed=False,
            reason="Unrecognized Codeforces problem URL (fail-closed).",
        )

    phase = phase_override if phase_override is not None else fetch_contest_phase(contest_id)

    if phase == "FINISHED":
        return GuardDecision(
            allowed=True,
            reason="Contest has finished.",
            contest_id=contest_id,
            phase=phase,
        )

    if phase is None:
        return GuardDecision(
            allowed=False,
            reason="Could not verify contest status from Codeforces API (fail-closed).",
            contest_id=contest_id,
        )

    return GuardDecision(
        allowed=False,
        reason=f"Contest is currently active or not finished (phase: {phase}).",
        contest_id=contest_id,
        phase=phase,
    )