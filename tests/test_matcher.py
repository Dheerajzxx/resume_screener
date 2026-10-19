import pytest

from core.matcher import Keyword, parse_keyword, parse_keywords, qualifies, score


def texts(keywords):
    return [keyword.text for keyword in keywords]


def test_parse_keywords_trims_spacing_and_empty_entries():
    keywords = parse_keywords(" python, sql ,, django ")
    assert texts(keywords) == ["python", "sql", "django"]
    assert all(keyword.weight == 1 for keyword in keywords)


def test_parse_keywords_is_case_insensitively_deduplicated():
    assert texts(parse_keywords("Python, python, PYTHON, sql")) == [
        "Python",
        "sql",
    ]


def test_parse_keywords_keeps_alternatives_together():
    assert texts(parse_keywords("js|javascript, c++")) == ["js|javascript", "c++"]


def test_parse_keywords_drops_pipe_only_entries():
    assert texts(parse_keywords("python, |,  ,sql")) == ["python", "sql"]


def test_parse_keywords_empty_string():
    assert parse_keywords("") == []


def test_parse_keyword_reads_positive_weight():
    assert parse_keyword("python:3") == Keyword("python", 3)
    assert parse_keyword("python: 4") == Keyword("python", 4)
    assert parse_keyword(" js | javascript : 2 ") == Keyword("js|javascript", 2)


def test_parse_keyword_keeps_non_numeric_colon_text():
    assert parse_keyword("http://example") == Keyword("http://example", 1)
    assert parse_keyword("python:abc") == Keyword("python:abc", 1)


def test_parse_keyword_clamps_zero_weight_to_one():
    assert parse_keyword("python:0") == Keyword("python", 1)


def test_parse_keywords_dedupes_by_keyword_and_keeps_first_weight():
    assert parse_keywords("python:2, PYTHON:5") == [Keyword("python", 2)]


def test_java_does_not_match_javascript():
    percent, matched, missing = score("I write JavaScript every day", ["java"])
    assert percent == 0.0
    assert matched == []
    assert missing == ["java"]


def test_java_matches_standalone_word():
    percent, matched, _ = score("Five years of Java and Spring", ["java"])
    assert percent == 100.0
    assert matched == ["java"]


def test_cpp_and_csharp_match_literal_punctuation():
    percent, matched, _ = score("C++ and C# developer", ["c++", "c#"])
    assert percent == 100.0
    assert matched == ["c++", "c#"]


def test_c_does_not_match_inside_cpp():
    percent, _, missing = score("Strong C++ background", ["C"])
    assert percent == 0.0
    assert missing == ["C"]


def test_dotnet_matches_after_a_word_character():
    percent, matched, _ = score("Built services in ASP.NET Core", [".NET"])
    assert percent == 100.0
    assert matched == [".NET"]


def test_dotnet_matches_standalone():
    percent, _, _ = score("Experience with .NET 8", [".NET"])
    assert percent == 100.0


def test_matching_is_case_insensitive():
    percent, matched, _ = score("PYTHON and SQL", ["python", "sql"])
    assert percent == 100.0
    assert matched == ["python", "sql"]


def test_whole_word_prevents_substring_matches():
    percent, _, missing = score("I maintain MySQL databases", ["sql"])
    assert percent == 0.0
    assert missing == ["sql"]


def test_alternatives_any_one_counts():
    percent, matched, _ = score("We use JavaScript on the frontend", ["js|javascript"])
    assert percent == 100.0
    assert matched == ["js|javascript"]


def test_alternatives_match_other_spelling():
    percent, matched, _ = score("Some Python, mostly JS", ["js|javascript", "python"])
    assert percent == 100.0
    assert matched == ["js|javascript", "python"]


def test_score_reports_matched_and_missing():
    percent, matched, missing = score("Python and SQL only", ["python", "aws", "sql", "go"])
    assert percent == 50.0
    assert matched == ["python", "sql"]
    assert missing == ["aws", "go"]


def test_percent_is_rounded_to_one_decimal():
    percent, _, _ = score("python and sql", ["python", "sql", "aws"])
    assert percent == 66.7


def test_zero_keywords_scores_zero():
    assert score("anything at all", []) == (0.0, [], [])


def test_weighted_score_uses_weight_share():
    percent, matched, missing = score(
        "Python and SQL", ["python:3", "sql", "aws:2"]
    )
    assert percent == 66.7  # (3 + 1) / (3 + 1 + 2)
    assert matched == ["python ×3", "sql"]
    assert missing == ["aws ×2"]


def test_weighted_alternatives_count_once():
    percent, matched, missing = score(
        "JavaScript developer", ["js|javascript:3", "python"]
    )
    assert percent == 75.0
    assert matched == ["js|javascript ×3"]
    assert missing == ["python"]


def test_weighted_keyword_objects_are_accepted():
    percent, matched, _ = score("Python", [Keyword("python", 3)])
    assert percent == 100.0
    assert matched == ["python ×3"]


@pytest.mark.parametrize(
    ("percent", "threshold", "expected"),
    [
        (70.0, 70, True),
        (70.1, 70, True),
        (69.9, 70, False),
        (0.0, 0, True),
        (None, 0, False),
    ],
)
def test_qualifies_uses_inclusive_threshold(percent, threshold, expected):
    assert qualifies(percent, threshold) is expected
