import re
from bs4 import BeautifulSoup, Tag
from app.editorial.schema import EditorialSection


_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = [*_HEADING_TAGS, "p", "li", "pre", "blockquote"]
_MAX_HEADING_LEN = 120
_MAX_PLAIN_HEADER_LEN = 80

_ID_HEADER = re.compile(
    r"^\s*(?i:(?:problem|tutorial|solution)\s+(?:of\s+)?)?(\d{3,5})\s*([A-Z]\d?)\b"
)

_PROBLEM_HREF = re.compile(r"(?:contest|problemset/problem)/(\d+)/(?:problem/)?([A-Z]\d?)\b")

_LETTER_HEADER = re.compile(r"^\s*(?i:problem\s+)?([A-Z]\d?)\s*[\.\-:–—)]\s*\S")
_PROBLEM_LETTER = re.compile(r"^\s*(?i:problem)\s+([A-Z]\d?)\s*$")


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


def _content_root(soup: BeautifulSoup) -> Tag:
    return soup.select_one("div.ttypography") or soup.body or soup


def _blocks(root: Tag):
    for el in root.find_all(_BLOCK_TAGS):
        if el.find_parent(_BLOCK_TAGS) is None:
            yield el


def _header_index(el: Tag, text: str, contest_id: int) -> str | None:
    if el.name == "pre" or len(text) > _MAX_HEADING_LEN:
        return None
    is_heading = el.name in _HEADING_TAGS
    if not is_heading and len(text) > _MAX_PLAIN_HEADER_LEN:
        return None
    m = _ID_HEADER.match(text)
    if m and int(m.group(1)) == contest_id:
        return m.group(2)
    for a in el.find_all("a", href=True):
        hm = _PROBLEM_HREF.search(a["href"])
        if hm and int(hm.group(1)) == contest_id:
            if is_heading or len(a.get_text(strip=True)) >= 0.5 * len(text):
                return hm.group(2)
    if is_heading:
        m = _LETTER_HEADER.match(text) or _PROBLEM_LETTER.match(text)
        if m:
            return m.group(1)
    return None


def split_editorial_round(html: str, contest_id: int) -> list[EditorialSection]:
    soup = BeautifulSoup(html, "lxml")
    root = _content_root(soup)
    order: list[str] = []
    parts: dict[str, dict] = {}
    current: str | None = None
    for el in _blocks(root):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        idx = _header_index(el, text, contest_id)
        if idx is not None:
            current = idx
            if idx not in parts:
                parts[idx] = {"heading": text, "text": [], "code": []}
                order.append(idx)
            continue
        if current is None:
            continue
        if el.name == "pre":
            parts[current]["code"].append(el.get_text("\n").strip())
        else:
            parts[current]["text"].append(text)

    # return is OUTSIDE the for loop (same indent as "for"), so it runs once, after every block is read
    return [
        EditorialSection(
            contest_id=contest_id,
            index=idx,
            heading=parts[idx]["heading"],
            text="\n".join(parts[idx]["text"]).strip(),
            code=[c for c in parts[idx]["code"] if c],
        )
        for idx in order
    ]


def confirm_title(section: EditorialSection, problem_title: str) -> bool:
    title = _norm(problem_title)
    if not title:
        return False
    return title in _norm(section.heading + " " + section.text[:300])