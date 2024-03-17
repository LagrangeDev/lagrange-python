from typing import TypeVar

from .elems import *

T = TypeVar(
    "T", "Text", "AtAll", "At", "Image", "Emoji", "Json", "Quote", "Raw", "Audio"
)
