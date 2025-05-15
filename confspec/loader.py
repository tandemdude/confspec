# -*- coding: utf-8 -*-
# Copyright (c) 2025-present tandemdude
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

__all__ = ["load", "loads", "parser_registry"]

import json
import pathlib
import typing as t

from confspec import helpers
from confspec import interpolate
from confspec import parsers

if t.TYPE_CHECKING:
    from collections.abc import Callable

    import msgspec
    import pydantic

    StructT = t.TypeVar("StructT", bound=msgspec.Struct)
    BaseModelT = t.TypeVar("BaseModelT", bound=pydantic.BaseModel)


parser_registry: dict[str, type[parsers.Parser]] = {
    "json": parsers.JsonParser,
    "toml": parsers.TomlParser,
    "yaml": parsers.YamlParser,
    "yml": parsers.YamlParser,
}
"""Dictionary mapping file extension to parser class used when parsing data of that format."""

KnownFormats: t.TypeAlias = t.Literal["json", "toml", "yaml", "yml"]


def _loads(
    raw: str | bytes,
    fmt: KnownFormats | str,
    /,
    *,
    cls: type[pydantic.BaseModel | msgspec.Struct] | None = None,
    strict: bool = False,
    dec_hook: Callable[[type[t.Any], t.Any], t.Any] | None = None,
) -> dict[str, t.Any] | pydantic.BaseModel | msgspec.Struct:
    parser = parser_registry.get(fmt)
    if parser is None:
        raise NotImplementedError(f"no parser registered for format {fmt!r}")

    if isinstance(raw, str):
        raw = raw.encode()

    parsed = parser().read(raw)
    interpolated = interpolate.InterpolationVisitor().visit(parsed)
    if cls is None:
        return interpolated

    dumped = json.dumps(interpolated)
    if helpers.is_pydantic(cls):
        return cls.model_validate_json(dumped, strict=strict)
    elif helpers.is_msgspec(cls):
        import msgspec

        return msgspec.json.decode(dumped, type=cls, strict=strict, dec_hook=dec_hook)

    raise NotImplementedError(f"unknown class '{cls}' provided")


@t.overload
def loads(raw: str | bytes, fmt: KnownFormats | str, /) -> dict[str, t.Any]: ...
@t.overload
def loads(
    raw: str | bytes,
    fmt: KnownFormats | str,
    /,
    *,
    cls: type[StructT],
    strict: bool = False,
    dec_hook: Callable[[type[t.Any], t.Any], t.Any] | None = None,
) -> StructT: ...
@t.overload
def loads(
    raw: str | bytes, fmt: KnownFormats | str, /, *, cls: type[BaseModelT], strict: bool = False
) -> BaseModelT: ...
def loads(
    raw: str | bytes,
    fmt: KnownFormats | str,
    /,
    *,
    cls: type[pydantic.BaseModel | msgspec.Struct] | None = None,
    strict: bool = False,
    dec_hook: Callable[[type[t.Any], t.Any], t.Any] | None = None,
) -> dict[str, t.Any] | pydantic.BaseModel | msgspec.Struct:
    """
    Like :meth:`~load`, but loads the configuration from the given string or bytes object instead. You must
    pass a format when using this method so that the library knows which parser to use. All other arguments
    have the same meaning as in :meth:`~load`.
    """
    return _loads(raw, fmt, cls=cls, strict=strict, dec_hook=dec_hook)


@t.overload
def load(path: str | pathlib.Path, /) -> dict[str, t.Any]: ...
@t.overload
def load(
    path: str | pathlib.Path,
    /,
    *,
    cls: type[StructT],
    strict: bool = False,
    dec_hook: Callable[[type[t.Any], t.Any], t.Any] | None = None,
) -> StructT: ...
@t.overload
def load(path: str | pathlib.Path, /, *, cls: type[BaseModelT], strict: bool = False) -> BaseModelT: ...
def load(
    path: str | pathlib.Path,
    /,
    *,
    cls: type[pydantic.BaseModel | msgspec.Struct] | None = None,
    strict: bool = False,
    dec_hook: Callable[[type[t.Any], t.Any], t.Any] | None = None,
) -> dict[str, t.Any] | pydantic.BaseModel | msgspec.Struct:
    """
    Loads arbitrary configuration from the given path, performing environment variable substitutions, and
    parses it into the given class (or to a dictionary if no class was provided).

    Currently supported formats are: yaml, toml and JSON. Additional formats can be supported by creating your own
    custom implementation of :obj:`~confspec.parsers.abc.Parser` and registering it with :obj:`~parser_registry`.

    Args:
        path: The path to the configuration file.
        cls: The pydantic BaseModel, or msgspec Struct to parse the configuration into. If :obj:`None`, the
            configuration will be parsed into a dictionary. Defaults to :obj:`None`.
        strict: Whether the parsing behaviour of pydantic/msgspec should be in strict mode. Defaults to :obj:`False`.
            If :obj:`True`, then parsers will not perform type coercion (e.g. digit string to int).
        dec_hook: Optional decode hook for msgspec to use when parsing to allow supporting additional types.

    Returns:
        The parsed configuration.

    Raises:
        :obj:`NotImplementedError`: If a file with an unrecognized format is specified.
        :obj:`ValueError`: If the file cannot be parsed to a dictionary (e.g. the top level object is an array).
        :obj:`ImportError`: If a required dependency is not installed.
    """
    path = pathlib.Path(path) if not isinstance(path, pathlib.Path) else path

    with open(path, "rb") as file:
        content = file.read().strip()

    return _loads(content, path.suffix[1:], cls=cls, strict=strict, dec_hook=dec_hook)
