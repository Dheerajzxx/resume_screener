import pymupdf
import pytest

from core.extractor import MIN_TEXT_CHARS, clear_cache, extract_text, extract_text_cached


def make_pdf(path, text):
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(str(path))
    doc.close()
    return path


def test_extracts_text_from_text_pdf(tmp_path):
    text = "Python developer with SQL and AWS experience building services."
    path = make_pdf(tmp_path / "resume.pdf", text)

    extracted, status = extract_text(path)

    assert status == "OK"
    assert "Python developer" in extracted


def test_short_text_is_flagged_as_scanned(tmp_path):
    path = make_pdf(tmp_path / "scan.pdf", "")

    text, status = extract_text(path)

    assert status == "SCANNED"
    assert len(text.strip()) < MIN_TEXT_CHARS


def test_corrupt_file_is_flagged_as_error(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"this is not a pdf")

    text, status = extract_text(path)

    assert (text, status) == ("", "ERROR")


def test_encrypted_file_is_flagged(tmp_path):
    path = tmp_path / "locked.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "A" * 100)
    doc.save(
        str(path),
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner",
        user_pw="user",
    )
    doc.close()

    text, status = extract_text(path)

    assert (text, status) == ("", "ENCRYPTED")


def test_cached_extraction_returns_same_result(tmp_path):
    clear_cache()
    path = make_pdf(
        tmp_path / "resume.pdf",
        "A sufficiently long resume body mentioning Python and SQL and more text.",
    )

    first = extract_text_cached(path)
    second = extract_text_cached(path)

    assert first == second
    assert first[1] == "OK"
