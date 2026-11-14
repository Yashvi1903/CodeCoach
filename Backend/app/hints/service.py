import re

from app.db.store import Store
from app.editorial.cleaner import confirm_title, split_editorial_round
from app.hints.build import build_hint_set
from app.hints.schema import HintResponse, HintSet
from app.llm.call import LLMCall
from app.reader.schema import Problem

_PROBLEM_ID = re.compile(r"^\s*(\d+)\s*([A-Za-z]\d?)\s*$")


def parse_problem_id(problem_id: str) -> tuple[int, str]:
    m = _PROBLEM_ID.match(problem_id)
    if not m:
        raise ValueError(f"Not a problem id like 980B: {problem_id!r}")
    return int(m.group(1)), m.group(2).upper()


def needs_editorial(store: Store, contest_id: int) -> bool:
    return store.needs_editorial(contest_id)


def ingest_editorial(store: Store, contest_id: int, editorial_html: str) -> int:
    sections = split_editorial_round(editorial_html, contest_id)
    store.save_round(contest_id, sections)
    return len(sections)


def ensure_hint_set(
    store: Store, problem: Problem, contest_id: int, index: str, llm: LLMCall | None = None
) -> HintSet:
    cached = store.get_hint_set(contest_id, index)
    if cached is not None:
        return cached

    section = store.get_section(contest_id, index)
    if section is not None:
        section.title_confirmed = confirm_title(section, problem.title)

    hint_set = build_hint_set(problem, contest_id, index, section=section, llm=llm)
    if hint_set.status == "ok":
        store.save_hint_set(hint_set)
    return hint_set


def next_hint(
    store: Store,
    user_id: str,
    problem: Problem,
    contest_id: int,
    index: str,
    llm: LLMCall | None = None,
) -> HintResponse:
    hint_set = ensure_hint_set(store, problem, contest_id, index, llm)
    if hint_set.status != "ok" or not hint_set.hints:
        return HintResponse(
            status="unavailable",
            message="I couldn't build hints for this problem right now. Please try again in a moment.",
        )

    unlocked = store.get_unlocked(user_id, contest_id, index)
    total = len(hint_set.hints)
    if unlocked >= total:
        return HintResponse(
            status="done",
            level=unlocked,
            total=total,
            message="You have seen every hint for this problem.",
        )

    level = unlocked + 1
    store.set_unlocked(user_id, contest_id, index, level)
    return HintResponse(
        status="ok", level=level, total=total, text=hint_set.hints[level - 1], label=hint_set.label
    )