import csv
from pathlib import Path

from core.export import HEADERS, export_csv
from core.models import ResultRow


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def test_export_writes_ranked_rows_in_order(tmp_path):
    jane = tmp_path / "jane.pdf"
    bob = tmp_path / "bob.pdf"
    scan = tmp_path / "scan.pdf"
    rows = [
        ResultRow(jane, 80.0, ["python ×3", "sql"], ["aws"], "OK"),
        ResultRow(bob, 66.7, ["sql"], ["python ×3", "aws ×2"], "OK"),
        ResultRow(scan, None, [], [], "SCANNED"),
    ]

    target = export_csv(rows, tmp_path / "results.csv")

    data = read_rows(target)
    assert data[0] == list(HEADERS)
    assert data[1] == [
        "1",
        "jane.pdf",
        "80",
        "python ×3; sql",
        "aws",
        "OK",
        str(jane),
    ]
    assert data[2] == [
        "2",
        "bob.pdf",
        "66.7",
        "sql",
        "python ×3; aws ×2",
        "OK",
        str(bob),
    ]
    assert data[3] == [
        "3",
        "scan.pdf",
        "",
        "",
        "",
        "Scanned",
        str(scan),
    ]


def test_export_empty_rows_writes_header_only(tmp_path):
    target = export_csv([], tmp_path / "empty.csv")
    assert read_rows(target) == [list(HEADERS)]


def test_export_preserves_unicode_and_quotes_commas(tmp_path):
    path = tmp_path / "josé, résumé.pdf"
    rows = [ResultRow(path, 100.0, ["café"], [], "OK")]

    target = export_csv(rows, tmp_path / "unicode.csv")

    data = read_rows(target)
    assert data[1][1] == "josé, résumé.pdf"
    assert data[1][3] == "café"
    assert data[1][6].endswith("josé, résumé.pdf")


def test_export_uses_stable_rank_for_each_row(tmp_path):
    rows = [
        ResultRow(Path("a.pdf"), 50.0, [], ["x"], "OK"),
        ResultRow(Path("b.pdf"), 40.0, [], ["y"], "OK"),
    ]
    data = read_rows(export_csv(rows, tmp_path / "ranks.csv"))
    assert [row[0] for row in data[1:]] == ["1", "2"]
