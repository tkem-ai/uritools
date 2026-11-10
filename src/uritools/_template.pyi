from collections.abc import Iterable, Mapping
from typing import TypeAlias

_TemplateScalar: TypeAlias = str | bytes | int | float | None
_TemplateValue: TypeAlias = (
    _TemplateScalar | Mapping[str | bytes, _TemplateScalar] | Iterable[_TemplateScalar]
)

class URITemplate:
    template: str
    def __init__(self, template: str | bytes) -> None: ...
    def expand(
        self,
        variables: Mapping[str, _TemplateValue] | None = ...,
        /,
        **kwargs: _TemplateValue,
    ) -> str: ...
