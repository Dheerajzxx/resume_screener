from __future__ import annotations

from PySide6.QtCore import QSettings

GROUP = "presets"


class PresetStore:
    """Named keyword sets persisted in the app's existing QSettings."""

    def __init__(self, settings: QSettings) -> None:
        self._settings = settings

    @staticmethod
    def _key(name: str) -> str:
        return f"{GROUP}/{name}"

    @staticmethod
    def _validate(name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Preset name cannot be empty")
        if "/" in cleaned or "\\" in cleaned:
            raise ValueError("Preset names cannot contain slashes")
        return cleaned

    def names(self) -> list[str]:
        self._settings.beginGroup(GROUP)
        try:
            keys = self._settings.childKeys()
        finally:
            self._settings.endGroup()
        return sorted(keys, key=str.casefold)

    def exists(self, name: str) -> bool:
        try:
            key = self._key(self._validate(name))
        except ValueError:
            return False
        return self._settings.contains(key)

    def get(self, name: str) -> str | None:
        try:
            key = self._key(self._validate(name))
        except ValueError:
            return None
        if not self._settings.contains(key):
            return None
        value = self._settings.value(key, "", type=str)
        return value if isinstance(value, str) else str(value)

    def save(self, name: str, keywords: str) -> str:
        cleaned = self._validate(name)
        self._settings.setValue(self._key(cleaned), keywords)
        self._settings.sync()
        return cleaned

    def delete(self, name: str) -> None:
        cleaned = self._validate(name)
        self._settings.remove(self._key(cleaned))
        self._settings.sync()
