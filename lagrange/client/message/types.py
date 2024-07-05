from typing import Union, TYPE_CHECKING
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from .elems import (
        Text,
        At,
        AtAll,
        Image,
        Emoji,
        Json,
        Quote,
        Raw,
        Audio,
        Poke,
        MarketFace,
    )

# T = TypeVar(
#     "T",
#     "Text",
#     "AtAll",
#     "At",
#     "Image",
#     "Emoji",
#     "Json",
#     "Quote",
#     "Raw",
#     "Audio",
#     "Poke",
#     "MarketFace",
# )
Element: TypeAlias = Union[
    "Text",
    "AtAll",
    "At",
    "Image",
    "Emoji",
    "Json",
    "Quote",
    "Raw",
    "Audio",
    "Poke",
    "MarketFace",
]
