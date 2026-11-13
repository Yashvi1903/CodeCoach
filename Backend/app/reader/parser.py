from bs4 import BeautifulSoup,Tag
from app.reader.schema import Problem,SampleTest
from app.reader.selectors import SELECTORS

class ParseError(Exception):
    """Raised when required CF problem sections cannot be extractec."""

def _extract_pre_text(pre_tag: Tag)->str:
    for br in pre_tag.find_all("br"):
        br.replace_with("\n")

    lines=pre_tag.find_all("div",class_="test-example-line")
    if lines:
        return "\n".join(line.get_text() for line in lines).strip()
    return pre_tag.get_text().strip()

def _clean_section_text(section: Tag | None, header_label: str) -> str:
    if not section:
        return ""
    text = section.get_text("\n", strip=True)
    if text.startswith(header_label):
        text = text[len(header_label):].strip()
    return text

def parse_problem_html(html: str, problem_id: str | None = None) -> Problem:
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(SELECTORS["statement_root"])
    if not root:
        raise ParseError("Couldn't read this page: missing problem-statement container.")

    title_el = root.select_one(SELECTORS["title"])
    time_el = root.select_one(SELECTORS["time_limit"])
    mem_el = root.select_one(SELECTORS["memory_limit"])
    input_el = root.select_one(SELECTORS["input_spec"])
    output_el = root.select_one(SELECTORS["output_spec"])
    note_el = root.select_one(SELECTORS["note"])

    title = title_el.get_text(strip=True) if title_el else ""
    time_limit = _clean_section_text(time_el, "time limit per test")
    memory_limit = _clean_section_text(mem_el, "memory limit per test")
    input_spec = _clean_section_text(input_el, "Input")
    output_spec = _clean_section_text(output_el, "Output")
    note = _clean_section_text(note_el, "Note") or None

    # Legend consists of direct <div> children between header and input-specification
    legend_parts = []
    header_el = root.select_one(SELECTORS["header"])
    if header_el:
        for sibling in header_el.find_next_siblings("div"):
            classes = sibling.get("class") or []
            if "input-specification" in classes:
                break
            legend_parts.append(sibling.get_text("\n", strip=True))
    legend = "\n\n".join(legend_parts).strip()

    # Extract samples
    samples: list[SampleTest] = []
    sample_container = root.select_one(SELECTORS["sample_tests"])
    if sample_container:
        inputs = sample_container.select(SELECTORS["sample_input"])
        outputs = sample_container.select(SELECTORS["sample_output"])
        for inp, outp in zip(inputs, outputs):
            samples.append(
                SampleTest(
                    input=_extract_pre_text(inp),
                    output=_extract_pre_text(outp),
                )
            )

    # Constraints usually live in input_spec (and occasionally legend)
    constraints_raw = f"{input_spec}\n{legend}".strip()

    # Check required fields per F1 failure handling rules
    if not title or not input_spec or not samples:
        raise ParseError("Couldn't read this page: required fields (title, constraints, or samples) missing.")

    has_figures = bool(root.find("img") or root.find("svg"))

    return Problem(
        problem_id=problem_id,
        title=title,
        time_limit=time_limit,
        memory_limit=memory_limit,
        legend=legend,
        input_spec=input_spec,
        output_spec=output_spec,
        constraints_raw=constraints_raw,
        samples=samples,
        note=note,
        has_figures=has_figures,
        raw_text=root.get_text("\n", strip=True),
    )