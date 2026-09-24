"""Per-code rules for interpreting parameter/setting names.

Parameters and settings only carry the raw `name` the user wrote. Each `Code` subclass declares a `name_format`
that turns that raw name into a parsed name it knows how to apply when editing its input file.

Subclasses must repeat `frozen=True`. Pydantic inherits it at runtime, but type checkers apply dataclass rules
and reject a non-frozen subclass of a frozen class.
"""
import typing
import pydantic


class NameFormat(pydantic.BaseModel, frozen=True, extra='forbid'):
    """Structured interpretation of a parameter/setting name. Subclasses define the fields and `parse`."""
    raw: str

    @classmethod
    def parse(cls, name: str) -> typing.Self:
        return cls(raw=name)


class RawName(NameFormat, frozen=True):
    """No interpretation. The name is passed through as-is (python, user, flash)."""
    pass


def _split(name: str, fields: tuple[str, ...], required: int) -> dict:
    parts = name.split('.')
    if not required <= len(parts) <= len(fields):
        raise ValueError(f"Name `{name}` must have between {required} and {len(fields)} '.'-separated parts: "
                         f"{'.'.join(fields[:required])}[.{'].['.join(fields[required:])}]")
    return dict(zip(fields, parts))


class _Indexed(NameFormat, frozen=True):
    """Adds an optional 1-based `index` selecting one of several repeated commands."""
    index: typing.Optional[pydantic.PositiveInt] = None

    @property
    def zero_based_index(self) -> typing.Optional[int]:
        """`index` converted for list access. None when the user did not give an index."""
        return None if self.index is None else self.index - 1


class ItemAttributeIndex(_Indexed, frozen=True):
    """`item.attribute[.index]` for codes with named elements/commands (elegant, opal, madx, spiffe)."""
    item: str
    attribute: str

    @classmethod
    def parse(cls, name: str) -> typing.Self:
        return cls(raw=name, **_split(name, ('item', 'attribute', 'index'), required=2))


class AttributeIndex(_Indexed, frozen=True):
    """`attribute[.index]` for codes where the command type is implied (genesis)."""
    attribute: str

    @classmethod
    def parse(cls, name: str) -> typing.Self:
        return cls(raw=name, **_split(name, ('attribute', 'index'), required=1))
