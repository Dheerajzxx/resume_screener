from pathlib import Path

from ui.user_guide import GUIDE_MARKDOWN


def test_user_guide_file_matches_embedded_markdown():
    guide_path = Path(__file__).resolve().parents[1] / "USER_GUIDE.md"
    assert guide_path.read_text(encoding="utf-8").strip() == GUIDE_MARKDOWN.strip(), (
        "USER_GUIDE.md changed; update GUIDE_MARKDOWN in ui/user_guide.py "
        "to match it"
    )
