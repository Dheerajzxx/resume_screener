from core.shortlist import FOLDER_NAME, shortlist


def make_file(path, content="resume"):
    path.write_text(content, encoding="utf-8")
    return path


def test_creates_shortlisted_folder_and_copies(tmp_path):
    source = make_file(tmp_path / "jane.pdf")

    target = shortlist([source], tmp_path)

    assert target == tmp_path / FOLDER_NAME
    assert target.is_dir()
    assert (target / "jane.pdf").read_text(encoding="utf-8") == "resume"
    assert source.exists()  # copy is the default


def test_reuses_existing_shortlisted_folder(tmp_path):
    source = make_file(tmp_path / "jane.pdf")
    target = tmp_path / FOLDER_NAME
    target.mkdir()
    marker = make_file(target / "keep.txt", "keep me")

    shortlist([source], tmp_path)

    assert marker.exists()
    assert (target / "jane.pdf").exists()


def test_collisions_get_numeric_suffixes(tmp_path):
    target = tmp_path / FOLDER_NAME
    target.mkdir()
    make_file(target / "jane.pdf", "first")
    source = make_file(tmp_path / "jane.pdf", "second")

    shortlist([source], tmp_path)
    shortlist([source], tmp_path)

    assert (target / "jane.pdf").read_text(encoding="utf-8") == "first"
    assert (target / "jane (1).pdf").read_text(encoding="utf-8") == "second"
    assert (target / "jane (2).pdf").read_text(encoding="utf-8") == "second"


def test_move_removes_source(tmp_path):
    source = make_file(tmp_path / "ravi.pdf", "content")

    target = shortlist([source], tmp_path, move=True)

    assert not source.exists()
    assert (target / "ravi.pdf").read_text(encoding="utf-8") == "content"


def test_missing_source_is_skipped(tmp_path):
    target = shortlist([tmp_path / "nope.pdf"], tmp_path)
    assert target.is_dir()
    assert list(target.iterdir()) == []


def test_multiple_files_are_all_copied(tmp_path):
    first = make_file(tmp_path / "a.pdf", "a")
    second = make_file(tmp_path / "b.pdf", "b")

    target = shortlist([first, second], tmp_path)

    assert {path.name for path in target.iterdir()} == {"a.pdf", "b.pdf"}
