SELECTORS = {
    "statement_root": "div.problem-statement",
    "header": "div.header",
    "title": "div.header div.title",
    "time_limit": "div.header div.time-limit",
    "memory_limit": "div.header div.memory-limit",
    "input_spec": "div.input-specification",
    "output_spec": "div.output-specification",
    "sample_tests": "div.sample-tests",
    "sample_input": "div.input pre",
    "sample_output": "div.output pre",
    "note": "div.note",
}

# selectors.py acts as a centralized map of Codeforces'
# HTML structure. Instead of hardcoding CSS classes inside
# your parsing logic, you store them in one dictionary so that
# if Codeforces ever changes its layout, you only update one file.