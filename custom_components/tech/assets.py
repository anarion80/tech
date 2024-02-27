"""Assets for translations."""
import json
import logging
import os

from .const import DEFAULT_ICON, ICON_BY_ID, ICON_BY_TYPE, TXT_ID_BY_TYPE

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

_subtitles = None


def loadSubtitles(language="pl"):
    """Load subtitles for the specified language.

    Args:
        language (str): The language code for the subtitles. Defaults to "pl".

    Returns:
        None

    """
    # TODO: Get subtitles directly from: https://emodul.pl/api/v1/i18n/{lang}
    global _subtitles  # noqa: PLW0603
    _LOGGER.debug("loading emodul.%s.json", language)
    filename = os.path.join(
        os.path.dirname(__file__), "translations", f"emodul.{language}.json"
    )
    f = open(filename)
    data = json.loads(f.read())
    _subtitles = data["subtitles"]


def get_text(id) -> str:
    """Get text by id."""
    return _subtitles.get(str(id), f"txtId {id}")


def get_text_by_type(type) -> str:
    """Get text by type."""
    id = TXT_ID_BY_TYPE.get(type, f"type {type}")
    return get_text(id)


def get_icon(id) -> str:
    """Get icon by id."""
    return ICON_BY_ID.get(id, DEFAULT_ICON)


def get_icon_by_type(type) -> str:
    """Get icon by type."""
    return ICON_BY_TYPE.get(type, DEFAULT_ICON)
