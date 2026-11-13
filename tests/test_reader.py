from pathlib import Path
from app.reader.parser import parse_problem_html

def test_parse_single_problem():
    html_path=Path("fixtures/problems/1950_A.html")
    html=html_path.read_text(encoding="utf-8")

    problem = parse_problem_html(html,problem_id="1950A")
    print("\nTitle:", problem.title)
    print("Limits:", problem.time_limit, "|", problem.memory_limit)
    print("Samples count:", len(problem.samples))
    print("First sample input:\n", problem.samples[0].input)

    assert problem.title
    assert len(problem.samples) >= 1
    assert problem.input_spec