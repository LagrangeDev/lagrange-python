from typing import TypeVar

from .elems import Text, At, AtAll, Image, Emoji, Json, Quote, Raw, Audio

T = TypeVar(
    "T", "Text", "AtAll", "At", "Image", "Emoji", "Json", "Quote", "Raw", "Audio"
)
