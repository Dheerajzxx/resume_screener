import pytest
from PySide6.QtCore import QSettings

from ui.presets import PresetStore


def make_store(tmp_path):
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    return PresetStore(settings)


def test_save_and_get_preset(tmp_path):
    store = make_store(tmp_path)

    store.save("Backend", "python:3, sql")

    assert store.names() == ["Backend"]
    assert store.exists("Backend")
    assert store.get("Backend") == "python:3, sql"


def test_names_are_sorted_case_insensitively(tmp_path):
    store = make_store(tmp_path)
    store.save("frontend", "js|javascript")
    store.save("Backend", "python:3, sql")
    store.save("data", "sql, pandas")

    assert store.names() == ["Backend", "data", "frontend"]


def test_save_overwrites_existing_preset(tmp_path):
    store = make_store(tmp_path)
    store.save("Backend", "python")
    store.save("Backend", "python:3, django")

    assert store.names() == ["Backend"]
    assert store.get("Backend") == "python:3, django"


def test_names_are_trimmed(tmp_path):
    store = make_store(tmp_path)

    returned = store.save("  Backend  ", "python")

    assert returned == "Backend"
    assert store.names() == ["Backend"]


def test_delete_removes_only_the_named_preset(tmp_path):
    store = make_store(tmp_path)
    store.save("Backend", "python")
    store.save("Frontend", "js|javascript")

    store.delete("Backend")

    assert store.names() == ["Frontend"]
    assert store.get("Backend") is None


def test_presets_persist_to_a_new_store_instance(tmp_path):
    first = make_store(tmp_path)
    first.save("Backend", "python:3, sql")

    second = make_store(tmp_path)

    assert second.names() == ["Backend"]
    assert second.get("Backend") == "python:3, sql"


def test_missing_preset_returns_none(tmp_path):
    store = make_store(tmp_path)
    assert store.get("Nope") is None
    assert not store.exists("Nope")


@pytest.mark.parametrize("name", ["", "   ", "team/backend", "team\\backend"])
def test_invalid_names_are_rejected(tmp_path, name):
    store = make_store(tmp_path)
    with pytest.raises(ValueError):
        store.save(name, "python")
